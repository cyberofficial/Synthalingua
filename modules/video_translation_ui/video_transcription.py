"""
Video Transcription Manager Module

Manages the transcription and translation of video audio chunks.
Extends the existing sub_gen.py logic for video-specific processing.

Handles:
- Integration with existing Whisper models (BaseWhisper, FasterWhisper, OpenVINO)
- Chunk-based transcription for buffered processing
- Silence detection and speech region processing
- Translation pipeline integration
- SRT timestamp generation with accurate phrase-level timing
- Resource management for model loading
- Subprocess-based isolation to ensure complete VRAM cleanup
"""

import os
import logging
import threading
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path
import time
import tempfile
import subprocess
import sys
import json

# Import existing Synthalingua modules
from modules import parser_args
from modules.device_manager import setup_device
from modules.languages import get_valid_languages

# Import silence detection
from modules.video_translation_ui.silence_detector import SilenceDetector

logger = logging.getLogger(__name__)

# Auto timeout floor for one-shot worker subprocesses (seconds)
WORKER_TIMEOUT_FLOOR_SECONDS = 900
# Auto timeout multiplier: allowed runtime = audio duration * this factor (seconds per second of audio)
WORKER_TIMEOUT_DURATION_MULTIPLIER = 30


def _compute_worker_timeout(timeout: Optional[int], audio_duration: Optional[float]) -> int:
    """
    Compute the effective worker timeout.

    If an explicit timeout is provided it wins. Otherwise the timeout scales
    with the audio duration so long videos do not hit a fixed cap and fail:
    timeout = max(900s, audio_duration * 30). That covers very slow CPU
    transcription (up to 30x slower than realtime) while still bounding true hangs.
    """
    if timeout is not None:
        return int(timeout)
    if audio_duration and audio_duration > 0:
        return max(WORKER_TIMEOUT_FLOOR_SECONDS, int(audio_duration * WORKER_TIMEOUT_DURATION_MULTIPLIER))
    return WORKER_TIMEOUT_FLOOR_SECONDS


class _PersistentWorker:
    """
    Long-lived transcription worker subprocess that loads the model ONCE and
    then accepts jobs as JSON lines on stdin, returning results as JSON lines
    on stdout (RESULT_EVENT) with optional SEGMENT_EVENT streaming during a job.

    Used by the video editor fast path (redo section, transcribe segment, batch
    redo) so the model is not reloaded from scratch for every editor action.
    """

    _RESULT_PREFIX = "RESULT_EVENT:"
    _SEGMENT_PREFIX = "SEGMENT_EVENT:"

    def __init__(self, model_source: str, model_size: str, device: str,
                 compute_type: str, model_dir: str, debug: bool = False):
        self.model_source = model_source
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model_dir = model_dir
        self.debug = debug

        self._process = None
        self._result_queue = None
        self._job_lock = threading.Lock()
        self._active_job_id = None
        self._active_segment_callback = None
        self._stdout_thread = None
        self._stderr_lines = []

        self._spawn()

    def _build_command(self) -> List[str]:
        is_likely_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        base_args = [
            '--persistent',
            '--model_source', self.model_source,
            '--model_size', self.model_size,
            '--device', self.device,
            '--compute_type', self.compute_type,
            '--model_dir', self.model_dir
        ]
        if self.debug:
            base_args.append('--debug')

        if is_likely_frozen:
            return [sys.executable, '--run-video-worker'] + base_args

        worker_script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'video_transcription_worker.py'
        )
        return [sys.executable, worker_script_path] + base_args

    def _spawn(self):
        import queue as _queue
        command = self._build_command()
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        logger.info(f"Starting persistent video worker subprocess: "
                    f"model={self.model_source}/{self.model_size}, device={self.device}")

        self._process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            creationflags=creation_flags
        )
        self._result_queue = _queue.Queue()

        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stdout_thread.start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stderr(self):
        try:
            for line in self._process.stderr:
                line = line.rstrip('\n')
                if line.strip():
                    self._stderr_lines.append(line)
                    if self.debug:
                        logger.debug(f"[PersistentWorker stderr] {line}")
        except Exception:
            pass

    def _read_stdout(self):
        try:
            for line in self._process.stdout:
                line = line.rstrip('\n')
                if not line:
                    continue

                if line.startswith(self._RESULT_PREFIX):
                    try:
                        result = json.loads(line[len(self._RESULT_PREFIX):])
                        self._result_queue.put(result)
                    except Exception as e:
                        logger.warning(f"Failed to parse worker result line: {e}")

                elif line.startswith(self._SEGMENT_PREFIX):
                    try:
                        event = json.loads(line[len(self._SEGMENT_PREFIX):])
                        # Only dispatch to the callback of the currently running job
                        if (self._active_job_id is not None
                                and event.get('job_id') == self._active_job_id
                                and self._active_segment_callback):
                            self._active_segment_callback(
                                {
                                    'start': event.get('start', 0.0),
                                    'end': event.get('end', 0.0),
                                    'text': '',
                                    'translation': event.get('text', '')
                                },
                                event.get('index', 0) + 1,
                                event.get('total', 0)
                            )
                    except Exception as e:
                        logger.warning(f"Failed to parse/handle segment event: {e}")

                else:
                    if self.debug and line.strip():
                        logger.debug(f"[PersistentWorker] {line}")
        except Exception as e:
            logger.debug(f"Persistent worker stdout reader ended: {e}")

    @property
    def alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def run_job(self, job: Dict, on_segment: Optional[Callable] = None,
                timeout: Optional[int] = None) -> Dict:
        """
        Send one job to the worker and wait for its result.

        Args:
            job: Job dict (audio_path, task, language, silence params, ...). A
                 unique job_id is added automatically.
            on_segment: Optional callback(timestamp_dict, index, total) invoked
                        for each streamed segment while the job runs.
            timeout: Max seconds to wait for the result.

        Returns:
            The worker's result dict.

        Raises:
            RuntimeError: If the worker dies, the job times out, or reports an error.
        """
        import queue as _queue

        if not self.alive:
            raise RuntimeError("Persistent worker is not alive")

        job_id = f"job_{int(time.time() * 1000)}_{id(job)}"
        payload = dict(job)
        payload['job_id'] = job_id

        effective_timeout = _compute_worker_timeout(timeout, payload.get('audio_duration'))

        with self._job_lock:
            self._active_job_id = job_id
            self._active_segment_callback = on_segment
            try:
                self._process.stdin.write(json.dumps(payload) + '\n')
                self._process.stdin.flush()
            except Exception as e:
                raise RuntimeError(f"Failed to send job to persistent worker: {e}")

            result = None
            deadline = time.time() + effective_timeout
            try:
                while result is None:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        raise RuntimeError(
                            f"Persistent worker job timed out after {effective_timeout} seconds")
                    try:
                        candidate = self._result_queue.get(timeout=min(remaining, 5.0))
                    except _queue.Empty:
                        if not self.alive:
                            # Worker died; drain any final result that landed before death
                            try:
                                result = self._result_queue.get_nowait()
                            except _queue.Empty:
                                raise RuntimeError(
                                    "Persistent worker died while processing job"
                                    + (f" | Last stderr: {self._stderr_lines[-1]}"
                                       if self._stderr_lines else ""))
                            continue
                        continue
                    if candidate.get('job_id') == job_id:
                        result = candidate
                    # else: stale result from a previous timed-out job; discard
            finally:
                self._active_job_id = None
                self._active_segment_callback = None

        if result.get('status') == 'error':
            raise RuntimeError(f"Persistent worker reported error: {result.get('message', 'Unknown error')}")

        return result

    def stop(self):
        """Terminate the worker subprocess."""
        if self._process is None:
            return
        try:
            if self.alive:
                try:
                    self._process.stdin.write(json.dumps({'cmd': 'shutdown'}) + '\n')
                    self._process.stdin.flush()
                except Exception:
                    pass
                try:
                    self._process.wait(timeout=3.0)
                except Exception:
                    self._process.kill()
        except Exception:
            pass


# Registry of live persistent workers, keyed by full model configuration.
# One worker (one loaded model) is shared by all editor actions using the same config.
_persistent_workers: Dict[Tuple, _PersistentWorker] = {}
_persistent_workers_lock = threading.Lock()


def get_persistent_worker(model_source: str, model_size: str, device: str,
                          compute_type: str, model_dir: str,
                          debug: bool = False) -> _PersistentWorker:
    """Get (or spawn) the shared persistent worker for the given model configuration."""
    key = (str(model_source).lower(), str(model_size), str(device), str(compute_type),
           str(model_dir), bool(debug))
    with _persistent_workers_lock:
        worker = _persistent_workers.get(key)
        if worker is not None and not worker.alive:
            logger.warning("Persistent worker for this config died; respawning")
            worker.stop()
            worker = None
        if worker is None:
            worker = _PersistentWorker(
                model_source=str(model_source).lower(),
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                model_dir=model_dir,
                debug=debug
            )
            _persistent_workers[key] = worker
        return worker


def shutdown_persistent_workers():
    """Stop all persistent workers (called before bulk processing and on app shutdown)."""
    with _persistent_workers_lock:
        worker_count = len(_persistent_workers)
        for worker in _persistent_workers.values():
            try:
                worker.stop()
            except Exception as e:
                logger.debug(f"Error stopping persistent worker: {e}")
        _persistent_workers.clear()
    if worker_count:
        logger.info(f"Persistent video workers shut down ({worker_count})")


def _run_transcription_in_subprocess(
    audio_path: str,
    model_source: str,
    model_size: str,
    device: str,
    compute_type: str,
    model_dir: str,
    language: Optional[str] = None,
    task: str = "transcribe",
    debug: bool = False,
    timeout: Optional[int] = None,
    enable_silence_detection: bool = False,
    silence_threshold_db: float = -50.0,
    min_silence_duration: float = 0.1,
    chunk_start_time: float = 0.0,
    on_segment_callback: Optional[Callable] = None,
    temperature: Optional[float] = None,
    compression_ratio_threshold: float = 2.4,
    audio_duration: Optional[float] = None
) -> Dict:
    """
    Run transcription in a separate subprocess to ensure complete VRAM cleanup.
    
    Uses subprocess.Popen() pattern (like sub_gen.py) which works correctly in both
    frozen (PyInstaller) and source mode. By running in a separate process,
    all GPU memory is freed after completion.
    
    For translate task with on_segment_callback, parses stdout in real-time for
    SEGMENT_EVENT: markers to enable incremental translation updates.
    
    Args:
        audio_path: Path to audio file
        model_source: Model source (whisper, fasterwhisper, openvino)
        model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
        device: Device to use (cpu, cuda)
        compute_type: Compute type for FasterWhisper/OpenVINO
        model_dir: Directory containing models
        language: Optional language code (None for auto-detect)
        task: Task type (transcribe or translate)
        debug: Enable debug output
        timeout: Timeout in seconds. None (default) = auto-scale with audio duration:
                 max(900s, audio_duration * 30). Pass an int to force a fixed timeout.
        audio_duration: Duration of the audio in seconds (used for the auto timeout)
        enable_silence_detection: Enable silence detection for segment-level processing
        silence_threshold_db: Silence threshold in dB
        min_silence_duration: Minimum silence duration in seconds
        chunk_start_time: Chunk start time for timestamp calculation
        on_segment_callback: Optional callback(segment_dict, index, total) for incremental updates
        
    Returns:
        dict: Result with 'text', 'language', 'processing_time', and optionally 'timestamps' list
        
    Raises:
        RuntimeError: If process fails
    """
    # Create temporary JSON file for output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        output_json_path = f.name

    # Resolve the effective timeout (explicit value wins, otherwise auto-scale with duration)
    effective_timeout = _compute_worker_timeout(timeout, audio_duration)

    try:
        # Detect if we're running in a frozen PyInstaller executable
        is_likely_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        
        # Build command based on mode
        if is_likely_frozen:
            # In frozen mode, re-launch the frozen executable with --run-video-worker flag
            command = [
                sys.executable,
                '--run-video-worker',
                '--audio_path', audio_path,
                '--output_json_path', output_json_path,
                '--model_source', model_source,
                '--model_size', model_size,
                '--device', device,
                '--compute_type', compute_type,
                '--model_dir', model_dir,
                '--task', task
            ]
            if language:
                command.extend(['--language', language])
            if debug:
                command.append('--debug')
            if enable_silence_detection:
                command.append('--enable_silence_detection')
                command.extend(['--silence_threshold_db', str(silence_threshold_db)])
                command.extend(['--min_silence_duration', str(min_silence_duration)])
                command.extend(['--chunk_start_time', str(chunk_start_time)])
            if temperature is not None:
                command.extend(['--temperature', str(temperature)])
            
            # Add compression_ratio_threshold
            command.extend(['--compression_ratio_threshold', str(compression_ratio_threshold)])
        else:
            # In source mode, execute the worker script directly
            worker_script_path = os.path.join(
                os.path.dirname(__file__), 
                'video_transcription_worker.py'
            )
            command = [
                sys.executable,
                worker_script_path,
                '--audio_path', audio_path,
                '--output_json_path', output_json_path,
                '--model_source', model_source,
                '--model_size', model_size,
                '--device', device,
                '--compute_type', compute_type,
                '--model_dir', model_dir,
                '--task', task
            ]
            if language:
                command.extend(['--language', language])
            if debug:
                command.append('--debug')
            if enable_silence_detection:
                command.append('--enable_silence_detection')
                command.extend(['--silence_threshold_db', str(silence_threshold_db)])
                command.extend(['--min_silence_duration', str(min_silence_duration)])
                command.extend(['--chunk_start_time', str(chunk_start_time)])
            if temperature is not None:
                command.extend(['--temperature', str(temperature)])
            
            # Add compression_ratio_threshold
            command.extend(['--compression_ratio_threshold', str(compression_ratio_threshold)])
        
        # Set up UTF-8 encoding environment
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        logger.debug(f"Starting video transcription worker subprocess: model={model_source}/{model_size}, task={task}, silence_detection={enable_silence_detection}")
        if debug:
            logger.debug(f"Command: {' '.join(command)}")
        
        # Start subprocess
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            creationflags=creation_flags
        )
        
        # For translate task with callback, parse stdout in real-time for segment events
        if task == "translate" and on_segment_callback:
            stdout_lines = []
            stderr_lines = []
            
            import threading
            import queue
            
            # Queue for collecting stderr
            stderr_queue = queue.Queue()
            
            def read_stderr():
                for line in process.stderr:
                    stderr_queue.put(line)
            
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            stderr_thread.start()
            
            # Read stdout line by line, parsing segment events
            try:
                for line in process.stdout:
                    stdout_lines.append(line)
                    
                    # Log worker output if debug enabled
                    if debug and line.strip():
                        logger.debug(f"[Worker] {line.rstrip()}")
                    
                    # Check for segment event markers
                    if line.startswith("SEGMENT_EVENT:"):
                        try:
                            segment_json = line[len("SEGMENT_EVENT:"):].strip()
                            segment_data = json.loads(segment_json)
                            
                            # Build timestamp dict compatible with callback
                            timestamp_dict = {
                                'start': segment_data['start'],
                                'end': segment_data['end'],
                                'text': '',  # Original text (not used for translate task)
                                'translation': segment_data['text']  # Translation from worker
                            }
                            
                            # Call callback immediately for real-time UI update
                            on_segment_callback(
                                timestamp_dict,
                                segment_data['index'] + 1,
                                segment_data['total']
                            )
                        except Exception as e:
                            logger.warning(f"Failed to parse segment event: {e}")
            except Exception as e:
                logger.error(f"Error reading stdout: {e}")
            
            # Wait for process to complete
            process.wait(timeout=effective_timeout)
            
            # Collect stderr
            stderr_thread.join(timeout=1)
            stderr_lines_collected = []
            while not stderr_queue.empty():
                try:
                    stderr_lines_collected.append(stderr_queue.get_nowait())
                except:
                    break
            
            # Log stderr if debug enabled
            if debug and stderr_lines_collected:
                for line in stderr_lines_collected:
                    if line.strip():
                        logger.debug(f"[Worker stderr] {line.rstrip()}")
            
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines_collected)
        else:
            # Standard communication for transcribe task or no callback
            try:
                stdout, stderr = process.communicate(timeout=effective_timeout)
                
                # Log worker output if debug enabled
                if debug:
                    if stdout and stdout.strip():
                        for line in stdout.split('\n'):
                            if line.strip():
                                logger.debug(f"[Worker] {line}")
                    if stderr and stderr.strip():
                        for line in stderr.split('\n'):
                            if line.strip():
                                logger.debug(f"[Worker stderr] {line}")
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise RuntimeError(f"Worker process timed out after {effective_timeout} seconds")
        
        # Check exit code and read result from JSON file
        # IMPORTANT: Always try to read JSON file first - worker writes errors there
        result = None
        if os.path.exists(output_json_path):
            try:
                with open(output_json_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
            except Exception as json_error:
                logger.error(f"Failed to read worker output JSON: {json_error}")
        
        # If process failed, build comprehensive error message
        if process.returncode != 0:
            error_msg = f"Worker process failed with exit code {process.returncode}"
            
            # Include worker's error message if available in JSON
            if result and result.get("status") == "error":
                worker_error = result.get('message', 'Unknown error')
                error_msg += f"\nWorker error: {worker_error}"
                
                # Include full traceback if available
                if 'traceback' in result:
                    error_msg += f"\nWorker traceback:\n{result['traceback']}"
            
            # Include stderr if available
            if stderr and stderr.strip():
                error_msg += f"\nStderr: {stderr.strip()}"
            
            # Include last few lines of stdout for context
            if stdout and stdout.strip():
                stdout_lines = stdout.strip().split('\n')
                last_lines = stdout_lines[-10:] if len(stdout_lines) > 10 else stdout_lines
                error_msg += f"\nLast stdout lines:\n" + "\n".join(last_lines)
            
            raise RuntimeError(error_msg)
        
        # If process succeeded but no output file
        if not result:
            raise RuntimeError("Worker did not create output JSON file")
        
        # Check result status (redundant check but safe)
        if result.get("status") == "error":
            raise RuntimeError(f"Worker reported error: {result.get('message', 'Unknown error')}")
        
        # Return successful result
        return_dict = {
            "text": result.get("text", ""),
            "language": result.get("language", "unknown"),
            "processing_time": result.get("processing_time", 0.0)
        }
        
        # If silence detection was enabled, include timestamps
        if enable_silence_detection and 'timestamps' in result:
            return_dict['timestamps'] = result['timestamps']
        
        return return_dict
        
    except Exception as e:
        logger.error(f"Worker subprocess execution failed: {e}", exc_info=True)
        raise
    finally:
        # Clean up temporary JSON file
        try:
            if os.path.exists(output_json_path):
                os.unlink(output_json_path)
        except:
            pass



class VideoTranscriptionManager:
    """
    Manages transcription and translation for video chunks.
    
    Integrates with existing Synthalingua model infrastructure and provides
    chunk-based processing for buffered video transcription.
    """
    
    def __init__(self,
                 model_source: str = "fasterwhisper",
                 model_size: str = "base",
                 device: str = "auto",
                 compute_type: str = "float16",
                 source_language: Optional[str] = None,
                 target_language: str = "en",
                 enable_translation: bool = True,
                 enable_silence_detection: bool = True,
                 silence_threshold_db: float = -35.0,
                 min_silence_duration: float = 0.5,
                 model_dir: str = "./models",
                 temperature: Optional[float] = None,
                 compression_ratio_threshold: float = 2.4,
                 debug_mode: bool = False,
                 worker_timeout: Optional[int] = None):
        """
        Initialize Video Transcription Manager.
        
        Args:
            model_source: Model source ("whisper", "fasterwhisper", "openvino")
            model_size: Model size ("tiny", "base", "small", "medium", "large-v2", "large-v3")
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Compute type for FasterWhisper/OpenVINO
            source_language: Source language code (None for auto-detect)
            target_language: Target language code for translation
            enable_translation: Whether to enable translation
            enable_silence_detection: Whether to detect and skip silence
            silence_threshold_db: dB threshold for silence detection
            min_silence_duration: Minimum silence duration in seconds
            model_dir: Directory containing models
        """
        self.model_source = model_source.lower()
        self.model_size = model_size
        self.device = device if device != "auto" else self._auto_detect_device()
        self.compute_type = compute_type
        # Convert 'auto' to None for language auto-detection
        self.source_language = None if source_language in ('auto', '', None) else source_language
        self.target_language = target_language
        self.enable_translation = enable_translation
        self.enable_silence_detection = enable_silence_detection
        self.model_dir = model_dir
        self.temperature = temperature  # None = use fallback, float = fixed temp
        self.compression_ratio_threshold = compression_ratio_threshold
        self.debug_mode = debug_mode  # Enable debug logging in worker subprocess
        self.worker_timeout = worker_timeout  # None = auto-scale with audio duration
        
        logger.info(f"VideoTranscriptionManager initialized: model={model_source}/{model_size}, "
                   f"device={self.device}, source_lang={self.source_language}, target_lang={target_language}, "
                   f"silence_detection={enable_silence_detection}")
        
        # Silence detector
        if self.enable_silence_detection:
            self.silence_detector = SilenceDetector(
                silence_threshold_db=silence_threshold_db,
                min_silence_duration=min_silence_duration,
                min_speech_duration=0.1
            )
        else:
            self.silence_detector = None
        
        # No model instance - models are loaded in subprocess for complete isolation
        self.model = None
        self.model_lock = threading.Lock()
        self.model_loaded = False
        
        # Statistics
        self.chunks_processed = 0
        self.total_processing_time = 0.0
        
        logger.info(f"VideoTranscriptionManager initialized (models will run in subprocess): "
                   f"source={model_source}, size={model_size}, device={self.device}")
    
    def _auto_detect_device(self) -> str:
        """Auto-detect best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except:
            pass
        return "cpu"
    
    def detect_language(self, audio_path: str) -> Tuple[str, float]:
        """
        Detect language from audio file using subprocess.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            # Use subprocess to detect language
            # Run transcription task to get language info
            result = _run_transcription_in_subprocess(
                audio_path=audio_path,
                model_source=self.model_source,
                model_size=self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                model_dir=self.model_dir,
                language=None,  # Auto-detect
                task="transcribe",
                debug=self.debug_mode
            )
            
            detected_language = result.get('language', 'unknown')
            confidence = 0.9 if detected_language != 'unknown' else 0.0
            
            logger.debug(f"Language detection result: {detected_language} ({confidence:.2%})")
            return (detected_language, confidence)
            
        except Exception as e:
            logger.error(f"Language detection failed: {e}", exc_info=True)
            return ("unknown", 0.0)
    
    def transcribe_chunk(self,
                        audio_path: str,
                        chunk_id: int,
                        language: Optional[str] = None,
                        duration: Optional[float] = None) -> Dict:
        """
        Transcribe a single audio chunk using subprocess isolation.
        
        Args:
            audio_path: Path to audio file
            chunk_id: Chunk identifier
            language: Optional language code (will auto-detect if None)
            duration: Optional audio duration in seconds (used for the auto worker timeout)
            
        Returns:
            dict: Transcription result with:
                - chunk_id: Chunk identifier
                - transcription: Transcribed text
                - language: Detected/used language
                - language_confidence: Detection confidence
                - processing_time: Time taken in seconds
                - success: Whether transcription succeeded
                - error: Error message if failed
        """
        start_time = time.time()
        result = {
            'chunk_id': chunk_id,
            'transcription': '',
            'language': language or self.source_language or 'unknown',
            'language_confidence': 0.0,
            'processing_time': 0.0,
            'success': False,
            'error': None
        }
        
        try:
            # Determine language to use
            use_language = language or self.source_language
            
            if not use_language:
                # Auto-detect language
                detected_lang, confidence = self.detect_language(audio_path)
                if detected_lang != "unknown":
                    result['language'] = detected_lang
                    result['language_confidence'] = confidence
                    use_language = detected_lang
                    logger.debug(f"Detected language for chunk {chunk_id}: "
                               f"{detected_lang} ({confidence:.2%})")
                else:
                    # Detection failed, let model auto-detect
                    result['language'] = None
                    use_language = None
                    logger.warning(f"Language detection failed for chunk {chunk_id}, using model auto-detect")
            else:
                result['language'] = use_language
                logger.debug(f"Using specified language for chunk {chunk_id}: {use_language}")
            
            # Transcribe using subprocess
            logger.info(f" Transcribing audio chunk {chunk_id} ({use_language or 'auto'})...")
            
            transcription_result = _run_transcription_in_subprocess(
                audio_path=audio_path,
                model_source=self.model_source,
                model_size=self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                model_dir=self.model_dir,
                language=self.source_language,
                task="transcribe",
                debug=self.debug_mode,
                timeout=self.worker_timeout,
                audio_duration=duration
            )
            
            result['transcription'] = transcription_result.get('text', '').strip()
            result['language'] = transcription_result.get('language', result['language'])
            result['success'] = True
            
            # Update statistics
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            self.chunks_processed += 1
            self.total_processing_time += processing_time
            
            logger.debug(f"Chunk {chunk_id} transcribed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to transcribe chunk {chunk_id}: {e}", exc_info=True)
        
        return result
    
    def translate_text(self, text: str, source_lang: str, audio_path: Optional[str] = None,
                        duration: Optional[float] = None) -> str:
        """
        Translate transcribed text to target language using subprocess isolation.
        
        For translation to English, uses Whisper's built-in translation capability
        which requires re-processing the audio with task="translate".
        
        Args:
            text: Text to translate (used if audio_path not provided)
            source_lang: Source language code
            audio_path: Optional path to audio file for Whisper translation
            duration: Optional audio duration in seconds (used for the auto worker timeout)
            
        Returns:
            str: Translated text
        """
        if not self.enable_translation:
            return ""
        
        # If source and target are the same, no translation needed
        if source_lang == self.target_language:
            return text
        
        logger.info(f" Translating text from {source_lang} to {self.target_language}...")
        try:
            # For translation to English, use Whisper's built-in translation
            if self.target_language == "en":
                # If audio path provided, use Whisper's translate task
                if audio_path and os.path.exists(audio_path):
                    logger.debug(f"Using Whisper translate task on audio")
                    
                    # Run translation using subprocess
                    translation_result = _run_transcription_in_subprocess(
                        audio_path=audio_path,
                        model_source=self.model_source,
                        model_size=self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                        model_dir=self.model_dir,
                        language=source_lang,
                        task="translate",  # Translate to English
                        debug=self.debug_mode,
                        timeout=self.worker_timeout,
                        audio_duration=duration
                    )
                    
                    translated = translation_result.get('text', '').strip()
                    if translated:
                        logger.debug(f"Translation successful: '{translated[:80]}'")
                        return translated
                    else:
                        logger.warning(f"Translation task failed, returning original text")
                        return text
                else:
                    # No audio available - cannot translate without re-processing
                    logger.warning(f"No audio path provided for translation, returning original text")
                    return text
            else:
                logger.warning(f"Translation to {self.target_language} not yet implemented")
                return text
                
        except Exception as e:
            logger.error(f"Translation failed: {e}", exc_info=True)
            return text  # Return original text on error
    
    def process_chunk(self,
                     audio_path: str,
                     chunk_id: int,
                     start_time: float,
                     end_time: float,
                     on_segment_complete: Optional[Callable] = None) -> Dict:
        """
        Process a complete chunk: transcribe and optionally translate.
        
        If silence detection is enabled, only processes speech regions within the chunk,
        providing accurate phrase-level timestamps instead of single chunk-level captions.
        
        Args:
            audio_path: Path to chunk audio file
            chunk_id: Chunk identifier
            start_time: Chunk start time in video
            end_time: Chunk end time in video
            on_segment_complete: Optional callback(timestamp_dict) called after each segment
            
        Returns:
            dict: Complete processing result with:
                - chunk_id: Chunk identifier
                - start_time: Chunk start in video
                - end_time: Chunk end in video
                - transcription: Full transcription text
                - translation: Full translation text (if enabled)
                - language: Detected/used language
                - success: Whether processing succeeded
                - error: Error message if failed
                - timestamps: List of caption segments with accurate timing:
                    [{'start': 10.5, 'end': 13.2, 'text': 'Hello world', 'translation': 'Hola mundo'}, ...]
        """
        result = {
            'chunk_id': chunk_id,
            'start_time': start_time,
            'end_time': end_time,
            'transcription': '',
            'translation': '',
            'language': 'unknown',
            'success': False,
            'error': None,
            'timestamps': []
        }
        
        try:
            # Check if silence detection is enabled
            if self.enable_silence_detection and self.silence_detector:
                # Process with silence detection for accurate phrase-level timing
                logger.info(f" Detecting speech regions in chunk {chunk_id}...")
                result = self._process_chunk_with_silence_detection(
                    audio_path, chunk_id, start_time, end_time, on_segment_complete
                )
            else:
                # Process entire chunk as one caption (original behavior)
                logger.info(f" Transcribing entire chunk {chunk_id} (no silence detection)...")
                result = self._process_chunk_without_silence_detection(
                    audio_path, chunk_id, start_time, end_time
                )
            
            if result['success']:
                logger.info(f" Chunk {chunk_id} processed successfully "
                          f"({len(result['timestamps'])} caption segments)")
            else:
                logger.error(f" Chunk {chunk_id} processing failed: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to process chunk {chunk_id}: {e}", exc_info=True)
        
        return result
    
    def _process_chunk_without_silence_detection(self,
                                                 audio_path: str,
                                                 chunk_id: int,
                                                 start_time: float,
                                                 end_time: float) -> Dict:
        """
        Process chunk without silence detection (original behavior).
        Creates a single caption for the entire chunk.
        """
        result = {
            'chunk_id': chunk_id,
            'start_time': start_time,
            'end_time': end_time,
            'transcription': '',
            'translation': '',
            'language': 'unknown',
            'success': False,
            'error': None,
            'timestamps': []
        }
        
        # Transcribe entire chunk
        transcription_result = self.transcribe_chunk(audio_path, chunk_id, duration=(end_time - start_time))
        
        if not transcription_result['success']:
            result['error'] = transcription_result['error']
            return result
        
        result['transcription'] = transcription_result['transcription']
        result['language'] = transcription_result['language']
        
        # Translate if enabled - pass audio path for Whisper translation
        if self.enable_translation and result['transcription']:
            translation = self.translate_text(
                result['transcription'],
                result['language'],
                audio_path=audio_path,  # Pass audio for Whisper translate task
                duration=(end_time - start_time)
            )
            result['translation'] = translation
        
        # Generate basic timestamp (whole chunk as one caption)
        if result['transcription']:
            result['timestamps'] = [{
                'start': start_time,
                'end': end_time,
                'text': result['transcription'],
                'translation': result['translation']
            }]
        
        result['success'] = True
        return result
    
    def _process_chunk_with_silence_detection(self,
                                              audio_path: str,
                                              chunk_id: int,
                                              start_time: float,
                                              end_time: float,
                                              on_segment_complete: Optional[Callable] = None) -> Dict:
        """
        Process chunk with silence detection for accurate phrase-level timing.
        
        Calls worker subprocess ONCE with silence detection enabled.
        Worker handles all segment extraction and processing internally.
        
        Args:
            on_segment_complete: Optional callback(timestamp_dict) called after each segment is processed
        """
        result = {
            'chunk_id': chunk_id,
            'start_time': start_time,
            'end_time': end_time,
            'transcription': '',
            'translation': '',
            'language': 'unknown',
            'success': False,
            'error': None,
            'timestamps': []
        }
        
        try:
            logger.info(f" Processing chunk {chunk_id} with silence detection and translation...")
            
            # Single pass: detect speech regions and translate each one immediately
            # The worker subprocess will:
            # 1. Detect speech regions using silence detection
            # 2. For each region:
            #    - Extract audio
            #    - Translate to English (task="translate")
            #    - Emit SEGMENT_EVENT to stdout
            # 3. Return all translated segments at the end
            #
            # The parent process (here) will:
            # - Parse SEGMENT_EVENT markers from stdout in real-time
            # - Call on_segment_complete callback immediately for each segment
            # - This creates incremental UI updates as each region is translated
            
            translation_result = _run_transcription_in_subprocess(
                audio_path=audio_path,
                model_source=self.model_source,
                model_size=self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                model_dir=self.model_dir,
                language=self.source_language,
                task="translate",  # Translate directly to English
                debug=self.debug_mode,
                timeout=self.worker_timeout,
                enable_silence_detection=True,
                silence_threshold_db=self.silence_detector.silence_threshold_db if self.silence_detector else -50.0,
                min_silence_duration=self.silence_detector.min_silence_duration if self.silence_detector else 0.1,
                chunk_start_time=start_time,
                on_segment_callback=on_segment_complete,  # Real-time callback for each segment
                temperature=self.temperature,
                compression_ratio_threshold=self.compression_ratio_threshold,
                audio_duration=(end_time - start_time) if end_time and start_time else None
            )
            
            if not translation_result or translation_result.get('status') == 'error':
                result['error'] = translation_result.get('message', 'Translation failed')
                return result
            
            # Get timestamps from worker result
            timestamps = translation_result.get('timestamps', [])
            if not timestamps:
                # No speech detected
                result['success'] = True
                result['language'] = self.source_language or 'unknown'
                return result
            
            logger.debug(f"Received {len(timestamps)} translated segments from worker")
            
            # Normalize timestamp format: worker returns translation in 'text' field,
            # but we need it in 'translation' field for UI compatibility
            for ts in timestamps:
                if not ts.get('translation'):
                    ts['translation'] = ts.get('text', '')
                    ts['text'] = ''  # Clear original text since we only show translation
            
            # Build full translation text
            all_translations = [ts.get('translation', '') for ts in timestamps]
            result['translation'] = ' '.join(all_translations)
            result['language'] = translation_result.get('language', self.source_language or 'unknown')
            result['timestamps'] = timestamps
            result['success'] = True
            
            logger.info(f"Translated {len(timestamps)} speech segments in chunk {chunk_id}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to process chunk {chunk_id} with translation: {e}", exc_info=True)
        
        return result
    
    def transcribe_chunk_persistent(self,
                                    audio_path: str,
                                    chunk_id: int,
                                    language: Optional[str] = None,
                                    duration: Optional[float] = None) -> Dict:
        """
        Transcribe a single audio chunk using the persistent preloaded worker.

        Editor fast path: the model is already loaded in the shared worker, so
        no per-call model load happens. The worker also auto-detects and returns
        the language, skipping the separate detection pass that the one-shot path
        performs. Falls back to the one-shot subprocess path on any failure.
        """
        try:
            worker = get_persistent_worker(
                self.model_source, self.model_size, self.device,
                self.compute_type, self.model_dir, self.debug_mode
            )
            # Normalize 'auto'/'' to None: the worker expects None for auto-detection
            use_language = language or self.source_language
            if use_language in ('auto', ''):
                use_language = None
            job = {
                'audio_path': audio_path,
                'task': 'transcribe',
                'language': use_language,
                'enable_silence_detection': False,
                'temperature': self.temperature,
                'compression_ratio_threshold': self.compression_ratio_threshold,
                'audio_duration': duration
            }
            raw = worker.run_job(job, timeout=self.worker_timeout)

            return {
                'chunk_id': chunk_id,
                'transcription': (raw.get('text') or '').strip(),
                'language': raw.get('language', 'unknown'),
                'language_confidence': 0.0,
                'processing_time': raw.get('processing_time', 0.0),
                'success': True,
                'error': None,
                'persistent_worker': True
            }
        except Exception as e:
            logger.warning(f"Persistent transcribe failed ({e}); falling back to one-shot subprocess")
            return self.transcribe_chunk(audio_path, chunk_id, language=language, duration=duration)

    def process_segment_persistent(self,
                                  audio_path: str,
                                  chunk_id: int,
                                  start_time: float,
                                  end_time: float,
                                  on_segment_complete: Optional[Callable] = None) -> Dict:
        """
        Editor fast path with the same contract as process_chunk, but running on
        the persistent preloaded model worker so no model reload occurs per call.

        Used by redo section, transcribe segment, and batch redo. Falls back to
        process_chunk (one-shot subprocess) on any failure.
        """
        result = {
            'chunk_id': chunk_id,
            'start_time': start_time,
            'end_time': end_time,
            'transcription': '',
            'translation': '',
            'language': 'unknown',
            'success': False,
            'error': None,
            'timestamps': []
        }

        try:
            worker = get_persistent_worker(
                self.model_source, self.model_size, self.device,
                self.compute_type, self.model_dir, self.debug_mode
            )
            duration = max(0.0, (end_time or 0.0) - (start_time or 0.0))

            if self.enable_silence_detection and self.silence_detector:
                # Single warm pass: region-by-region translate, mirroring
                # _process_chunk_with_silence_detection
                job = {
                    'audio_path': audio_path,
                    'task': 'translate',
                    'language': self.source_language,
                    'enable_silence_detection': True,
                    'silence_threshold_db': self.silence_detector.silence_threshold_db,
                    'min_silence_duration': self.silence_detector.min_silence_duration,
                    'chunk_start_time': start_time,
                    'temperature': self.temperature,
                    'compression_ratio_threshold': self.compression_ratio_threshold,
                    'audio_duration': duration
                }
                raw = worker.run_job(job, on_segment=on_segment_complete, timeout=self.worker_timeout)

                timestamps = raw.get('timestamps', []) or []

                # Normalize: worker returns translation in 'text' field
                for ts in timestamps:
                    if not ts.get('translation'):
                        ts['translation'] = ts.get('text', '')
                        ts['text'] = ''

                result['translation'] = ' '.join([ts.get('translation', '') for ts in timestamps])
                result['language'] = raw.get('language', self.source_language or 'unknown')
                result['timestamps'] = timestamps
                result['success'] = True
            else:
                # Two warm passes: transcribe then translate, mirroring
                # _process_chunk_without_silence_detection
                t_res = self.transcribe_chunk_persistent(audio_path, chunk_id, duration=duration)
                if not t_res['success']:
                    result['error'] = t_res['error']
                    return result

                result['transcription'] = t_res['transcription']
                result['language'] = t_res['language']

                if self.enable_translation and result['transcription']:
                    job = {
                        'audio_path': audio_path,
                        'task': 'translate',
                        'language': result['language'],
                        'enable_silence_detection': False,
                        'temperature': self.temperature,
                        'compression_ratio_threshold': self.compression_ratio_threshold,
                        'audio_duration': duration
                    }
                    raw = worker.run_job(job, timeout=self.worker_timeout)
                    result['translation'] = (raw.get('text') or '').strip()

                if result['transcription']:
                    result['timestamps'] = [{
                        'start': start_time,
                        'end': end_time,
                        'text': result['transcription'],
                        'translation': result['translation']
                    }]

                result['success'] = True

        except Exception as e:
            logger.warning(f"Persistent segment processing failed ({e}); "
                           f"falling back to one-shot subprocess")
            return self.process_chunk(audio_path, chunk_id, start_time, end_time,
                                       on_segment_complete=on_segment_complete)

        return result

    def get_statistics(self) -> Dict:
        """
        Get processing statistics.
        
        Returns:
            dict: Statistics including chunks processed, average time, etc.
        """
        avg_time = (self.total_processing_time / self.chunks_processed 
                   if self.chunks_processed > 0 else 0)
        
        return {
            'chunks_processed': self.chunks_processed,
            'total_processing_time': round(self.total_processing_time, 2),
            'average_processing_time': round(avg_time, 2),
            'model_source': self.model_source,
            'model_size': self.model_size,
            'device': self.device,
        }
    
    def change_model(self, 
                    model_source: Optional[str] = None,
                    model_size: Optional[str] = None):
        """
        Change the model configuration.
        
        Since models run in subprocess, this just updates configuration.
        No actual model loading happens here.
        
        Args:
            model_source: New model source (optional)
            model_size: New model size (optional)
        """
        if model_source:
            self.model_source = model_source.lower()
        if model_size:
            self.model_size = model_size
        
        logger.info(f"Model configuration updated to: {self.model_source} / {self.model_size}")
    
    def unload_model(self):
        """
        Unload model (no-op since models run in subprocess).
        
        Models are automatically cleaned up after each subprocess completes,
        ensuring complete VRAM/RAM release.
        """
        # No model to unload - subprocess handles cleanup automatically
        logger.debug("Model cleanup not needed (subprocess isolation ensures VRAM release)")
    
    def __del__(self):
        """Destructor (no-op since models run in subprocess)."""
        # No cleanup needed - subprocess handles everything
        pass
