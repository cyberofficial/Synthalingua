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
    timeout: int = 300,
    enable_silence_detection: bool = False,
    silence_threshold_db: float = -50.0,
    min_silence_duration: float = 0.1,
    chunk_start_time: float = 0.0,
    on_segment_callback: Optional[Callable] = None,
    temperature: Optional[float] = None
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
        timeout: Timeout in seconds (default: 300 = 5 minutes)
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
            process.wait(timeout=timeout)
            
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
                stdout, stderr = process.communicate(timeout=timeout)
                
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
                raise RuntimeError(f"Worker process timed out after {timeout} seconds")
        
        # Check exit code
        if process.returncode != 0:
            error_msg = f"Worker process failed with exit code {process.returncode}"
            if stderr:
                error_msg += f"\nStderr: {stderr}"
            raise RuntimeError(error_msg)
        
        # Read result from JSON file
        if not os.path.exists(output_json_path):
            raise RuntimeError("Worker did not create output JSON file")
        
        with open(output_json_path, 'r', encoding='utf-8') as f:
            result = json.load(f)
        
        # Check result status
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
                 debug_mode: bool = False):
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
        self.debug_mode = debug_mode  # Enable debug logging in worker subprocess
        
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
                        language: Optional[str] = None) -> Dict:
        """
        Transcribe a single audio chunk using subprocess isolation.
        
        Args:
            audio_path: Path to audio file
            chunk_id: Chunk identifier
            language: Optional language code (will auto-detect if None)
            
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
                debug=self.debug_mode
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
    
    def translate_text(self, text: str, source_lang: str, audio_path: Optional[str] = None) -> str:
        """
        Translate transcribed text to target language using subprocess isolation.
        
        For translation to English, uses Whisper's built-in translation capability
        which requires re-processing the audio with task="translate".
        
        Args:
            text: Text to translate (used if audio_path not provided)
            source_lang: Source language code
            audio_path: Optional path to audio file for Whisper translation
            
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
                        debug=self.debug_mode
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
        transcription_result = self.transcribe_chunk(audio_path, chunk_id)
        
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
                audio_path=audio_path  # Pass audio for Whisper translate task
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
                enable_silence_detection=True,
                silence_threshold_db=self.silence_detector.silence_threshold_db if self.silence_detector else -50.0,
                min_silence_duration=self.silence_detector.min_silence_duration if self.silence_detector else 0.1,
                chunk_start_time=start_time,
                on_segment_callback=on_segment_complete,  # Real-time callback for each segment
                temperature=self.temperature
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
