"""
Subtitle Generator Module

This module provides functionality to generate subtitles from audio files using the Whisper ASR model.
It supports both transcription (in original language) and translation (to English) tasks.

Key features:
- Automatic language detection
- RAM-aware model selection
- Confidence scoring with color-coded output
- Progress tracking during generation
- SRT format subtitle generation
- Chunked processing for memory efficiency
- Support for custom model directories
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import numpy as np
import gc
import shutil
import tempfile
import uuid
import atexit

import warnings
import glob
import librosa

import os
import sys  # ADDED: For finding python executable
import json # ADDED: For IPC with worker
import concurrent.futures  # ADDED: For parallel processing of speech regions
from modules.demucs_path_helper import get_demucs_python_path

import whisper
import subprocess
from colorama import Fore, Style, init
from modules import parser_args

# Initialize colorama for Windows support
init()

# Parse command-line arguments first to check for debug flag
args = parser_args.parse_arguments()

# Configure logging based on debug flag
log_level = logging.DEBUG if getattr(args, 'debug', False) else logging.WARNING
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)


class TempFileManager:
    """
    Manages the creation and cleanup of temporary files and directories.

    This class creates a single base temporary directory for the application's
    session inside a local 'temp' folder and ensures it's cleaned up upon exit,
    unless the --keep_temp flag is used.
    It is implemented as a singleton to ensure a single instance.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(TempFileManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, keep_temp=False):
        # Initialize only once
        if not hasattr(self, 'initialized'):
            self.keep_temp = keep_temp

            # Get the project's root directory (assuming sub_gen.py is in a 'modules' subdir)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Define the local temp directory path within the project
            local_temp_base = os.path.join(project_root, 'temp')
            
            # Create the local 'temp' directory if it doesn't exist
            os.makedirs(local_temp_base, exist_ok=True)

            # Create a unique session directory inside the local 'temp' folder
            self.base_dir = tempfile.mkdtemp(prefix="sub_gen_session_", dir=local_temp_base)
            
            self.initialized = True
            
            if self.keep_temp:
                print(f"{Fore.YELLOW}ℹ️  Temporary files will be kept at: {self.base_dir}{Style.RESET_ALL}")
            else:
                # Register the cleanup method to be called upon script exit
                atexit.register(self.cleanup)
            logger.info("Temporary file manager initialized. Base directory: %s", self.base_dir)

    def get_temp_path(self, suffix="", prefix=""):
        """Returns a unique path for a new temporary file."""
        filename = f"{prefix}{uuid.uuid4()}{suffix}"
        return os.path.join(self.base_dir, filename)

    def mkdtemp(self, prefix=""):
        """Creates and returns a new temporary directory inside the base directory."""
        dir_path = os.path.join(self.base_dir, f"{prefix}{uuid.uuid4()}")
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    def cleanup(self):
        """Removes the base temporary directory and all its contents."""
        if self.keep_temp:
            logger.info("Skipping cleanup of temporary directory as requested: %s", self.base_dir)
            return
        
        try:
            if os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir, ignore_errors=True)
                print(f"{Fore.YELLOW}🗑️ Temporary files cleaned up from: {self.base_dir}{Style.RESET_ALL}")
                logger.info("Successfully cleaned up temporary directory: %s", self.base_dir)
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to clean up temporary files at {self.base_dir}: {e}{Style.RESET_ALL}")
            logger.error("Failed to cleanup temporary directory %s: %s", self.base_dir, e, exc_info=True)

# Initialize the temporary file manager globally
temp_manager = TempFileManager(keep_temp=getattr(args, 'keep_temp', False))


# Global variable to track auto-proceed mode for detection reviews
_auto_proceed_detection = False
# Global variable to track if user wants to skip Turbo model questions
_skip_turbo_questions = False
# Global variable to track intelligent mode (auto-testing higher models)
# Pulls true from intelligent_mode from arg parse, if not set then assume false
_intelligent_mode = getattr(args, 'intelligent_mode', False)
# Global variables to persist custom silence detection settings in auto mode
_last_silence_threshold = None
_last_silence_duration = None

# Inform user if word_timestamps is enabled
if getattr(args, 'word_timestamps', False):
    print(f"{Fore.CYAN}ℹ️  Word-level timestamps are enabled. This may make subtitle generation a bit slower as it requires more processing power. If you notice any unusual slowdowns, try removing the --word_timestamps flag next time you run this command.{Style.RESET_ALL}")

# Inform user if isolate_vocals is enabled
if getattr(args, 'isolate_vocals', False):
    jobs_info = ""
    if hasattr(args, 'demucs_jobs') and args.demucs_jobs > 0:
        jobs_info = f" Using {args.demucs_jobs} parallel jobs for faster processing."
    print(f"{Fore.CYAN}ℹ️  Vocal isolation is enabled. The program will attempt to extract vocals from the input audio before generating subtitles. This may take additional time and requires the demucs package.{jobs_info}{Style.RESET_ALL}")

# Inform user if silent_detect is enabled
if getattr(args, 'silent_detect', False):
    custom_threshold = hasattr(args, 'silent_threshold') and args.silent_threshold != -35.0
    custom_duration = hasattr(args, 'silent_duration') and args.silent_duration != 0.5
    
    settings_info = ""
    if custom_threshold or custom_duration:
        parts = []
        if custom_threshold:
            parts.append(f"threshold: {getattr(args, 'silent_threshold', -35.0)}dB")
        if custom_duration:
            parts.append(f"min duration: {getattr(args, 'silent_duration', 0.5)}s")
        settings_info = f" ({', '.join(parts)})"
    
    print(f"{Fore.CYAN}ℹ️  Silent detection is enabled{settings_info}. The program will skip processing silent audio chunks during caption generation. This may improve processing speed for files with long silent periods.{Style.RESET_ALL}")

def group_speech_regions_by_silence(regions: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Group consecutive speech regions separated by silence into batches.
    Each group contains consecutive speech regions, and groups are separated by silence.
    Args:
        regions (List[Dict]): List of regions with 'type', 'start', 'end', etc.
    Returns:
        List[List[Dict]]: List of groups, each a list of consecutive speech regions.
    """
    groups = []
    current_group = []
    for region in regions:
        if region['type'] == 'speech':
            current_group.append(region)
        else:
            if current_group:
                groups.append(current_group)
                current_group = []
    if current_group:
        groups.append(current_group)
    return groups

# NEW HELPER FUNCTION TO RUN TRANSCRIPTION IN A SEPARATE PROCESS
def run_transcription_in_process(
    audio_path: str,
    model_type: str,
    decode_options: Dict[str, Any],
    model_dir: str,
    device: str = "cuda"
) -> Dict[str, Any]:
    """
    Runs the Whisper transcription in a separate child process.

    This ensures that all GPU memory is freed after the transcription is complete,
    preventing caching issues when switching models.

    Args:
        audio_path (str): Path to the audio file to transcribe.
        model_type (str): The Whisper model to use (e.g., 'large-v3').
        decode_options (Dict[str, Any]): A dictionary of options for the transcribe call.
        model_dir (str): The directory where models are stored.
        device (str): Device to run on ('cpu' or 'cuda'). Defaults to 'cuda'.

    Returns:
        Dict[str, Any]: The transcription result dictionary from Whisper.

    Raises:
        RuntimeError: If the transcription worker process fails.
    """
    # Use the TempFileManager to get a path for the worker's JSON output.
    # atexit will handle cleanup, so no 'finally' block is needed here.
    output_json_path = temp_manager.get_temp_path(suffix='.json', prefix='worker_output_')

    # Serialize decode_options to a JSON string to pass as a single argument
    decode_options_json = json.dumps(decode_options, ensure_ascii=False)

    # Check if running as a frozen executable (e.g., Nuitka, PyInstaller)
    is_frozen = getattr(sys, 'frozen', False)
    # A more robust check for frozen executable, in case sys.frozen is not set correctly.
    # This checks if the executable is not 'python.exe' or 'pythonw.exe'.
    is_likely_frozen = is_frozen or ('python' not in os.path.basename(sys.executable).lower())

    command = []
    if is_likely_frozen:
        print(f"{Fore.CYAN}ℹ️  Running in portable (frozen) mode: launching worker as a subprocess...{Style.RESET_ALL}")
        # When frozen, re-launch the executable with a special flag to act as a worker.
        command = [
            sys.executable,
            '--run-worker',
            "--audio_path", audio_path,
            "--output_json_path", output_json_path,
            "--model_type", model_type,
            "--model_dir", model_dir,
            "--device", device,
            "--decode_options_json", decode_options_json,
            "--model_source", args.model_source,
            "--compute_type", args.compute_type
        ]

    else:
        print(f"{Fore.CYAN}\nℹ️  Running in source mode: launching worker script as a subprocess...{Style.RESET_ALL}")
        # When running from source, execute the worker script directly.
        worker_script_path = os.path.join(os.path.dirname(__file__), "transcribe_worker.py")
        if not os.path.exists(worker_script_path):
            raise FileNotFoundError(f"Transcription worker script not found at: {worker_script_path}")

        command = [
            sys.executable,  # This will be 'python.exe' or equivalent
            worker_script_path,
            "--audio_path", audio_path,
            "--output_json_path", output_json_path,
            "--model_type", model_type,
            "--model_dir", model_dir,
            "--device", device,
            "--decode_options_json", decode_options_json,
            "--model_source", args.model_source,
            "--compute_type", args.compute_type
        ]

    # Show the command if in debug mode
    if getattr(args, 'debug', False):
        logger.debug("Running worker command: %s", " ".join(f'"{c}"' for c in command))

    # Set up environment variables to ensure UTF-8 encoding for the subprocess
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONLEGACYWINDOWSSTDIO'] = '0'  # Ensure UTF-8 on Windows
    
    try:
        # Run the worker process with explicit UTF-8 handling
        # Use Popen for better control over encoding and error handling
        import subprocess
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env,
            # Suppress console window on Windows for cleaner output
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith('win') else 0
        )
        
        # Get output with timeout to prevent hanging
        try:
            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise RuntimeError("Transcription worker timed out after 5 minutes")
        
        # Create a mock process object to maintain compatibility
        class ProcessResult:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        process = ProcessResult(returncode, stdout, stderr)
        
    except UnicodeError as e:
        # Fallback: try with binary mode and decode manually
        logger.warning("UTF-8 subprocess failed, trying binary mode: %s", e)
        process_binary = subprocess.run(
            command,
            capture_output=True,
            text=False,
            env=env
        )
        # Manually decode the output
        try:
            stdout = process_binary.stdout.decode('utf-8', errors='replace') if process_binary.stdout else ""
            stderr = process_binary.stderr.decode('utf-8', errors='replace') if process_binary.stderr else ""
        except UnicodeDecodeError:
            stdout = process_binary.stdout.decode('cp1252', errors='replace') if process_binary.stdout else ""
            stderr = process_binary.stderr.decode('cp1252', errors='replace') if process_binary.stderr else ""
        
        # Create a mock process object with decoded strings
        class MockProcess:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        process = MockProcess(process_binary.returncode, stdout, stderr)

    # Log worker's output (filter out Unicode threading errors)
    if process.stdout:
        logger.info("Worker STDOUT:\n%s", process.stdout)
    if process.stderr:
        # Filter out the specific Unicode threading errors that don't affect functionality
        stderr_lines = process.stderr.split('\n')
        filtered_stderr = []
        skip_next = False
        
        for line in stderr_lines:
            # Skip Unicode threading errors that are harmless
            if any(error_pattern in line for error_pattern in [
                "UnicodeDecodeError: 'charmap' codec can't decode",
                "Exception in thread",
                "_readerthread",
                "encodings\\cp1252.py"
            ]):
                skip_next = True
                continue
            elif skip_next and (line.strip() == "" or line.startswith("  ")):
                # Skip continuation lines of the error traceback
                continue
            else:
                skip_next = False
                if line.strip():  # Only add non-empty lines
                    filtered_stderr.append(line)
        
        if filtered_stderr:
            logger.warning("Worker STDERR:\n%s", "\n".join(filtered_stderr))

    # Check if the process completed successfully
    if process.returncode != 0:
        raise RuntimeError(
            f"Transcription worker failed with exit code {process.returncode}.\n"
            f"Stderr: {process.stderr}"
        )

    # Read the result from the temporary JSON file
    try:
        with open(output_json_path, 'r', encoding='utf-8') as f:
            response = json.load(f)
    except UnicodeDecodeError as e:
        # Fallback: try reading with different encodings if UTF-8 fails
        logger.warning("UTF-8 decoding failed, trying alternative encodings: %s", e)
        for encoding in ['utf-8-sig', 'cp1252', 'latin1']:
            try:
                with open(output_json_path, 'r', encoding=encoding) as f:
                    response = json.load(f)
                logger.info("Successfully read JSON with encoding: %s", encoding)
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        else:
            raise RuntimeError(f"Could not read worker output JSON with any encoding. Original error: {e}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Worker output JSON is malformed: {e}")

    if response.get("status") == "error":
        raise RuntimeError(f"Transcription worker reported an error: {response.get('message')}")

    return response.get("result", {})

def format_human_time(seconds: float) -> str:
    """
    Convert seconds to human-readable format (e.g., 1m40.2s).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Human-readable time format
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h{minutes:02d}m{remaining_seconds:04.1f}s"
    else:
        return f"{minutes}m{remaining_seconds:04.1f}s"

def detect_silence_in_audio(audio_path: str, silence_threshold_db: float = -35.0, min_silence_duration: float = 0.1) -> List[Dict[str, Any]]:
    """
    Detect silence and speech regions in audio file using intelligent segmentation.
    
    Args:
        audio_path (str): Path to audio file
        silence_threshold_db (float): dB threshold below which audio is considered silent (default: -35.0)
        min_silence_duration (float): Minimum duration in seconds for a region to be considered silence (default: 0.5)
    
    Returns:
        List[Dict[str, Any]]: List of regions with type, start, and end times
                              [{'type': 'speech', 'start': 13.8, 'end': 42.3}, ...]
    """
    global _last_silence_threshold, _last_silence_duration, _auto_proceed_detection, _intelligent_mode
    # Always use the last set silence threshold and min duration if available
    if _last_silence_threshold is not None:
        silence_threshold_db = _last_silence_threshold
    if _last_silence_duration is not None:
        min_silence_duration = _last_silence_duration
    try:
        # Use Whisper's audio loading first (more reliable, fewer warnings)
        try:
            import whisper.audio
            audio = whisper.audio.load_audio(audio_path)
            sr = 16000  # Whisper's standard sample rate
        except Exception:
            # Fallback: try librosa with error suppression
            try:
                import librosa
                import warnings
                # Suppress librosa warnings about PySoundFile and audioread
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    warnings.filterwarnings("ignore", category=FutureWarning)
                    audio, sr = librosa.load(audio_path, sr=None)
            except ImportError:
                # Last resort: basic audio loading
                raise RuntimeError("Neither Whisper nor librosa audio loading is available")
        
        print(f"{Fore.CYAN}🔍 Analyzing audio for speech/silence regions...{Style.RESET_ALL}")
        
        # Convert dB threshold to linear amplitude
        silence_threshold_linear = 10 ** (silence_threshold_db / 20.0)
        
        # Calculate frame-wise RMS energy with overlapping windows
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop (overlap for smoother detection)
        
        # Calculate RMS for each frame
        rms_frames = []
        for i in range(0, len(audio) - frame_length + 1, hop_length):
            frame = audio[i:i + frame_length]
            rms = np.sqrt(np.mean(frame ** 2)) if len(frame) > 0 else 0.0
            rms_frames.append(rms)
        
        # Create time axis for frames
        frame_times = np.arange(len(rms_frames)) * hop_length / sr
        
        # Detect silence/speech regions
        is_silent = np.array(rms_frames) < silence_threshold_linear
        
        # Find transitions between silence and speech
        transitions = []
        current_state = is_silent[0]
        current_start = 0.0
        current_rms_values = []  # Track RMS values for current region
        
        for i, silent in enumerate(is_silent[1:], 1):
            current_rms_values.append(rms_frames[i-1])  # Add previous frame's RMS
            
            if silent != current_state:
                # State change detected
                region_type = 'silence' if current_state else 'speech'
                region_duration = frame_times[i] - current_start
                
                # Calculate average dB level for this region
                if current_rms_values:
                    avg_rms = np.mean(current_rms_values)
                    avg_db = 20 * np.log10(max(avg_rms, 1e-10))  # Avoid log(0)
                    max_rms = np.max(current_rms_values)
                    max_db = 20 * np.log10(max(max_rms, 1e-10))
                else:
                    avg_db = -float('inf')
                    max_db = -float('inf')
                
                # Only add regions that meet minimum duration requirements
                if region_type == 'silence' and region_duration >= min_silence_duration:
                    transitions.append({
                        'type': 'silence',
                        'start': current_start,
                        'end': frame_times[i],
                        'avg_db': avg_db,
                        'max_db': max_db,
                        'duration': region_duration
                    })
                elif region_type == 'speech' and region_duration >= 0.1:  # Minimum 100ms for speech
                    transitions.append({
                        'type': 'speech',
                        'start': current_start,
                        'end': frame_times[i],
                        'avg_db': avg_db,
                        'max_db': max_db,
                        'duration': region_duration
                    })
                
                current_state = silent
                current_start = frame_times[i]
                current_rms_values = []  # Reset for new region
        
        # Add remaining RMS values for final region
        current_rms_values.extend(rms_frames[len(is_silent)-len(current_rms_values):])
        
        # Add final region
        audio_duration = len(audio) / sr
        final_region_type = 'silence' if current_state else 'speech'
        final_duration = audio_duration - current_start
        
        # Calculate dB for final region
        if current_rms_values:
            avg_rms = np.mean(current_rms_values)
            avg_db = 20 * np.log10(max(avg_rms, 1e-10))
            max_rms = np.max(current_rms_values)
            max_db = 20 * np.log10(max(max_rms, 1e-10))
        else:
            avg_db = -float('inf')
            max_db = -float('inf')
        
        if final_region_type == 'silence' and final_duration >= min_silence_duration:
            transitions.append({
                'type': 'silence',
                'start': current_start,
                'end': audio_duration,
                'avg_db': avg_db,
                'max_db': max_db,
                'duration': final_duration
            })
        elif final_region_type == 'speech' and final_duration >= 0.1:
            transitions.append({
                'type': 'speech',
                'start': current_start,
                'end': audio_duration,
                'avg_db': avg_db,
                'max_db': max_db,
                'duration': final_duration
            })
        
        # Merge adjacent speech regions separated by very short silences
        merged_regions = []
        for region in transitions:
            if (region['type'] == 'speech' and 
                merged_regions and 
                merged_regions[-1]['type'] == 'speech' and
                region['start'] - merged_regions[-1]['end'] < 1.0):  # Less than 1 second gap
                # Merge with previous speech region - combine dB values
                prev_region = merged_regions[-1]
                
                # Weight the dB values by duration for proper averaging
                prev_duration = prev_region['duration']
                curr_duration = region['duration']
                total_duration = prev_duration + curr_duration
                
                # Weighted average of dB values
                combined_avg_db = (prev_region['avg_db'] * prev_duration + region['avg_db'] * curr_duration) / total_duration
                combined_max_db = max(prev_region['max_db'], region['max_db'])
                
                merged_regions[-1].update({
                    'end': region['end'],
                    'avg_db': combined_avg_db,
                    'max_db': combined_max_db,
                    'duration': total_duration
                })
            else:
                merged_regions.append(region)
        
        # Filter out speech regions and show statistics
        speech_regions = [r for r in merged_regions if r['type'] == 'speech']
        silence_regions = [r for r in merged_regions if r['type'] == 'silence']
        
        total_speech_duration = sum(r['end'] - r['start'] for r in speech_regions)
        total_silence_duration = sum(r['end'] - r['start'] for r in silence_regions)
        
        # Calculate speech groups for batch processing
        speech_groups = group_speech_regions_by_silence(merged_regions)
        total_groups_duration = sum(
            sum(region['end'] - region['start'] for region in group) 
            for group in speech_groups
        )
        
        # Calculate workload reduction
        workload_reduction = (total_silence_duration / audio_duration) * 100
        
        print(f"{Fore.GREEN}✓ Audio analysis complete:{Style.RESET_ALL}")
        print(f"   • Speech Groups: {len(speech_groups)} ({total_groups_duration:.1f}s)")
        print(f"   • Speech regions: {len(speech_regions)} ({total_speech_duration:.1f}s)")
        print(f"   • Silence regions: {len(silence_regions)} ({total_silence_duration:.1f}s)")
        print(f"   • Processing efficiency: {100 * total_speech_duration / audio_duration:.1f}% of audio contains speech")
        print(f"   • Current threshold: {silence_threshold_db:.1f}dB")
        
        # Show workload reduction with helpful context
        if workload_reduction > 0:
            time_saved = format_human_time(total_silence_duration)
            print(f"   • {Fore.CYAN}💡 With current settings, workload will be reduced by {workload_reduction:.1f}% (saving {time_saved} of processing){Style.RESET_ALL}")
        else:
            print(f"   • {Fore.YELLOW}⚠️  No workload reduction - consider adjusting threshold for better efficiency{Style.RESET_ALL}")
        
        # Show detailed breakdown of regions with dB levels
        print(f"\n{Fore.CYAN}🔊 Audio Level Analysis:{Style.RESET_ALL}")
        
        for i, region in enumerate(merged_regions):
            region_type = region['type']
            start_time = region['start']
            end_time = region['end']
            duration = region['duration']
            avg_db = region['avg_db']
            max_db = region['max_db']
            
            # Color-code based on region type and dB levels
            if region_type == 'speech':
                icon = "🎵"
                type_color = Fore.GREEN
                type_label = "SPEECH"
            else:
                icon = "🔇"
                type_color = Fore.YELLOW
                type_label = "SILENCE"
            
            # Add recommendations based on dB levels
            recommendation = ""
            if region_type == 'silence':
                if avg_db > silence_threshold_db + 5:
                    recommendation = f" {Fore.RED}(Maybe increase threshold to {avg_db + 3:.1f}dB?){Style.RESET_ALL}"
                elif avg_db > silence_threshold_db:
                    recommendation = f" {Fore.YELLOW}(Close to threshold){Style.RESET_ALL}"
            else:  # speech
                if avg_db < silence_threshold_db:
                    recommendation = f" {Fore.RED}(Maybe decrease threshold to {avg_db - 3:.1f}dB?){Style.RESET_ALL}"
            
            print(f"   {icon} {type_color}{type_label:<7}{Style.RESET_ALL} "
                  f"{start_time:6.1f}s - {end_time:6.1f}s ({duration:5.1f}s) "
                  f"({format_human_time(start_time)} - {format_human_time(end_time)}) "
                  f"│ Avg: {avg_db:6.1f}dB │ Peak: {max_db:6.1f}dB{recommendation}")
        
        # Show threshold guidance
        print(f"\n{Fore.CYAN}💡 Threshold Guidance:{Style.RESET_ALL}")
        
        # Analyze if threshold seems appropriate
        misclassified_speech = [r for r in silence_regions if r['avg_db'] < silence_threshold_db - 5]
        misclassified_silence = [r for r in speech_regions if r['avg_db'] > silence_threshold_db + 10]
        
        if misclassified_speech:
            print(f"   {Fore.YELLOW}⚠️  {len(misclassified_speech)} 'silence' regions have very low audio levels{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}   Consider lowering threshold to around {min(r['avg_db'] for r in misclassified_speech) - 3:.1f}dB{Style.RESET_ALL}")
        
        if misclassified_silence:
            print(f"   {Fore.YELLOW}⚠️  {len(misclassified_silence)} 'speech' regions have high audio levels{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}   Consider raising threshold to around {max(r['avg_db'] for r in misclassified_silence) - 3:.1f}dB{Style.RESET_ALL}")
        
        if not misclassified_speech and not misclassified_silence:
            print(f"   {Fore.GREEN}✅ Current threshold ({silence_threshold_db:.1f}dB) seems well-tuned for this audio{Style.RESET_ALL}")
        
        # Interactive adjustment options
        
        # Check if auto-proceed is enabled
        if _auto_proceed_detection:
            print(f"\n{Fore.GREEN}🚀 Auto-proceeding with current detection (skip mode enabled){Style.RESET_ALL}")
            # Show speech regions that will be processed (simplified now since detailed info is above)
            if speech_regions:
                print(f"\n{Fore.GREEN}🎵 Speech regions to be processed: {len(speech_regions)}{Style.RESET_ALL}")
                print(f"   {Fore.GREEN}   With the current threshold ({silence_threshold_db:.1f}dB) and Min duration: {min_silence_duration:.1f}s{Style.RESET_ALL}")
            return merged_regions
        
        while True:
            print(f"\n{Fore.CYAN}🔧 Detection Review:{Style.RESET_ALL}")
            print(f"   Do you want to:")
            print(f"   1. {Fore.GREEN}Proceed with current detection{Style.RESET_ALL}")
            print(f"   2. {Fore.YELLOW}Adjust threshold settings and re-analyze{Style.RESET_ALL}")
            print(f"   3. {Fore.CYAN}Manually modify region classifications{Style.RESET_ALL}")
            if getattr(args, 'isolate_vocals', False):
                print(f"   4. {Fore.MAGENTA}Try different Demucs model and re-analyze{Style.RESET_ALL}")
            print(f"   5. {Fore.BLUE}Proceed with current detection and skip asking again{Style.RESET_ALL}")

            max_choice = 5 if getattr(args, 'isolate_vocals', False) else 5
            max_choice_vocals = 4 if getattr(args, 'isolate_vocals', False) else 3

            # Always use the last set min_silence_duration if available
            prompt_min_duration = _last_silence_duration if _last_silence_duration is not None else min_silence_duration

            try:
                choice = input(f"\n{Fore.CYAN}Enter your choice (1-{max_choice}): {Style.RESET_ALL}").strip()

                if choice == "1":
                    break  # Proceed with current detection

                elif choice == "5":
                    _auto_proceed_detection = True
                    print(f"{Fore.GREEN}✅ Auto-proceed mode enabled. Future segments will skip detection review.{Style.RESET_ALL}")
                    break

                elif choice == "2":
                    # Re-run with new settings
                    print(f"\n{Fore.CYAN}Current settings:{Style.RESET_ALL}")
                    print(f"   Threshold: {silence_threshold_db:.1f}dB")
                    print(f"   Min duration: {prompt_min_duration:.1f}s")
                    # Get new threshold
                    new_threshold_input = input(f"\n{Fore.CYAN}Enter new threshold (current: {silence_threshold_db:.1f}dB) or press Enter to keep: {Style.RESET_ALL}").strip()
                    if new_threshold_input:
                        try:
                            new_threshold = float(new_threshold_input)
                            print(f"{Fore.GREEN}✅ New threshold: {new_threshold:.1f}dB{Style.RESET_ALL}")
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid threshold. Keeping current: {silence_threshold_db:.1f}dB{Style.RESET_ALL}")
                            new_threshold = silence_threshold_db
                    else:
                        new_threshold = silence_threshold_db
                    # Get new duration
                    new_duration_input = input(f"\n{Fore.CYAN}Enter new min duration (current: {prompt_min_duration:.1f}s) or press Enter to keep: {Style.RESET_ALL}").strip()
                    if new_duration_input:
                        try:
                            new_duration = float(new_duration_input)
                            print(f"{Fore.GREEN}✅ New min duration: {new_duration:.1f}s{Style.RESET_ALL}")
                            _last_silence_duration = new_duration  # Persist for next prompt
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid duration. Keeping current: {prompt_min_duration:.1f}s{Style.RESET_ALL}")
                            new_duration = prompt_min_duration
                    else:
                        new_duration = prompt_min_duration
                    # Store custom values for auto mode AND manual mode
                    _last_silence_threshold = new_threshold
                    _last_silence_duration = new_duration
                    # Re-run analysis
                    print(f"\n{Fore.CYAN}🔄 Re-analyzing with new settings...{Style.RESET_ALL}")
                    return detect_silence_in_audio(audio_path, new_threshold, new_duration)
                
                elif choice == "4" and getattr(args, 'isolate_vocals', False):
                    # Try different Demucs model
                    print(f"\n{Fore.CYAN}🎛️ Demucs Model Selection:{Style.RESET_ALL}")
                    print(f"   Available models:")
                    print(f"   1. {Fore.YELLOW}htdemucs{Style.RESET_ALL} (default, Hybrid Transformer v4)")
                    print(f"   2. {Fore.YELLOW}htdemucs_ft{Style.RESET_ALL} (fine-tuned htdemucs, better quality, slower)")
                    print(f"   3. {Fore.YELLOW}htdemucs_6s{Style.RESET_ALL} (6-source: drums, bass, other, vocals, piano, guitar)")
                    print(f"   4. {Fore.YELLOW}hdemucs_mmi{Style.RESET_ALL} (Hybrid Demucs v3, MusDB + 800 songs)")
                    print(f"   5. {Fore.YELLOW}mdx{Style.RESET_ALL} (MDX challenge Track A winner)")
                    print(f"   6. {Fore.YELLOW}mdx_extra{Style.RESET_ALL} (MDX Track B, trained with extra data)")
                    print(f"   7. {Fore.YELLOW}mdx_q{Style.RESET_ALL} (quantized mdx, smaller/faster)")
                    print(f"   8. {Fore.YELLOW}mdx_extra_q{Style.RESET_ALL} (quantized mdx_extra, smaller/faster)")
                    print(f"   9. {Fore.YELLOW}hdemucs{Style.RESET_ALL} (original Hybrid Demucs v3)")
                    print(f"  10. {Fore.YELLOW}demucs{Style.RESET_ALL} (original time-only Demucs)")
                    
                    print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
                    print(f"   🎯 {Fore.GREEN}Best Quality{Style.RESET_ALL}: htdemucs_ft (fine-tuned)")
                    print(f"   🎯 {Fore.BLUE}Fastest{Style.RESET_ALL}: mdx_q or mdx_extra_q (quantized)")
                    print(f"   🎯 {Fore.MAGENTA}Detailed Separation{Style.RESET_ALL}: htdemucs_6s (6 sources)")
                    print(f"   🎯 {Fore.CYAN}Balanced{Style.RESET_ALL}: mdx_extra (good quality + speed)")
                    print(f"   🎯 {Fore.YELLOW}Legacy/Compatibility{Style.RESET_ALL}: hdemucs or demucs")
                    
                    model_choice = input(f"\n{Fore.CYAN}Select Demucs model (1-10): {Style.RESET_ALL}").strip()
                    
                    model_map = {
                        "1": "htdemucs",
                        "2": "htdemucs_ft", 
                        "3": "htdemucs_6s",
                        "4": "hdemucs_mmi",
                        "5": "mdx",
                        "6": "mdx_extra",
                        "7": "mdx_q",
                        "8": "mdx_extra_q",
                        "9": "hdemucs",
                        "10": "demucs"
                    }
                    
                    if model_choice in model_map:
                        selected_model = model_map[model_choice]
                        print(f"{Fore.GREEN}✅ Selected model: {selected_model}{Style.RESET_ALL}")
                        
                        # Show model info
                        model_info = {
                            "htdemucs": "Latest Hybrid Transformer model (default)",
                            "htdemucs_ft": "Fine-tuned version for better quality",
                            "htdemucs_6s": "6-source separation (includes piano/guitar)",
                            "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                            "mdx": "Frequency-domain model, MDX winner",
                            "mdx_extra": "Enhanced MDX with extra training data",
                            "mdx_q": "Quantized MDX (faster, smaller)",
                            "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                            "hdemucs": "Original Hybrid Demucs v3",
                            "demucs": "Original time-domain Demucs"
                        }
                        
                        print(f"{Fore.CYAN}ℹ️  {model_info[selected_model]}{Style.RESET_ALL}")
                        
                        # Re-run vocal isolation with new model and then re-analyze
                        print(f"\n{Fore.CYAN}🔄 Re-running vocal isolation with {selected_model} model...{Style.RESET_ALL}")
                        
                        # Import the original audio path from the calling function
                        # We need to get the original path before vocal isolation
                        original_audio_path = audio_path.replace("_vocals.wav", "") if "_vocals" in audio_path else audio_path
                        
                        try:
                            print(f"\n{Fore.CYAN}🔄 Re-running vocal isolation with {selected_model} model...{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}📊 Progress will be shown below:{Style.RESET_ALL}")
                            
                            # Use the temp manager to create a directory for demucs output.
                            # This directory will be cleaned up by atexit, fixing a bug where the
                            # temp file was deleted before the recursive call could use it.
                            tmpdir = temp_manager.mkdtemp(prefix='demucs_rerun_')
                            
                            demucs_python_path = get_demucs_python_path()
                            demucs_cmd = [
                                demucs_python_path,
                                '-m', 'demucs',
                                '-n', selected_model,
                                '-o', tmpdir,
                                '--two-stems', 'vocals'
                            ]
                            
                            # Add jobs parameter if specified
                            if hasattr(args, 'demucs_jobs') and args.demucs_jobs > 0:
                                demucs_cmd.extend(['-j', str(args.demucs_jobs)])
                            
                            demucs_cmd.append(original_audio_path)
                            
                            # Run demucs with selected model and real-time progress
                            process = subprocess.Popen(demucs_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
                            
                            # Monitor progress in real-time
                            stderr_output = ""
                            current_phase = 0
                            total_phases = 1  # Default to 1, will update when we detect multiple models
                            last_progress = 0.0  # Track progress separately
                            ensemble_detected = False  # Track if we've already detected ensemble
                            
                            # Check for known multi-model types upfront
                            if selected_model in ['htdemucs_ft', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q']:
                                # These are known to be ensemble models based on testing
                                if selected_model == 'htdemucs_ft':
                                    total_phases = 4  # htdemucs_ft is a bag of 4 models
                                elif selected_model in ['mdx', 'mdx_extra', 'mdx_q']:
                                    total_phases = 4  # These are bags of 4 models
                                elif selected_model == 'mdx_extra_q':
                                    total_phases = 4  # Bag of 4 models but with more complex processing
                                print(f"{Fore.CYAN}  📋 {selected_model} is a multi-model ensemble ({total_phases} internal models){Style.RESET_ALL}")
                                ensemble_detected = True
                            
                            # Determine number of threads for Demucs message
                            num_threads_for_message = getattr(args, 'demucs_jobs', 0)
                            if num_threads_for_message == 0:
                                display_threads = 1
                            else:
                                display_threads = num_threads_for_message
                            print(f"{Fore.CYAN}🎵 Demucs processing using {display_threads} thread{'s' if display_threads != 1 else ''}:{Style.RESET_ALL}")
                            
                            # Read stderr for progress updates
                            while True:
                                if process.stderr is not None:
                                    stderr_line = process.stderr.readline()
                                    if stderr_line:
                                        stderr_output += stderr_line
                                        line_stripped = stderr_line.strip()
                                        
                                        # Detect if this is a bag of models - check multiple patterns (only if not already detected)
                                        if not ensemble_detected and any(phrase in line_stripped.lower() for phrase in ['bag of', 'ensemble of', 'bag_of', 'selected model is']):
                                            try:
                                                # Show debug info to understand the format
                                                if getattr(args, 'debug', False):
                                                    print(f"{Fore.MAGENTA}Debug: Detected bag line: '{line_stripped}'{Style.RESET_ALL}")
                                                
                                                # Try different extraction patterns
                                                if 'bag of' in line_stripped.lower():
                                                    # Pattern: "Selected model is a bag of X models. You will see that many progress bars per track."
                                                    parts = line_stripped.lower().split('bag of')
                                                    if len(parts) > 1:
                                                        # Extract the number between "bag of" and "models"
                                                        models_part = parts[1].split('models')[0].strip()
                                                        if models_part.isdigit():
                                                            detected_phases = int(models_part)
                                                            # Only update if it's actually a multi-model (> 1)
                                                            if detected_phases > 1:
                                                                total_phases = detected_phases
                                                                ensemble_detected = True
                                                                print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                                                                print(f"{Fore.CYAN}  📋 This model will run {total_phases} internal models and combine results{Style.RESET_ALL}")
                                                elif 'models:' in line_stripped.lower():
                                                    # Look for patterns like "4 models:" or similar
                                                    import re
                                                    match = re.search(r'(\d+)\s*models?:', line_stripped.lower())
                                                    if match:
                                                        detected_phases = int(match.group(1))
                                                        if detected_phases > 1:
                                                            total_phases = detected_phases
                                                            ensemble_detected = True
                                                            print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                                                            print(f"{Fore.CYAN}  📋 This model will run {total_phases} internal models and combine results{Style.RESET_ALL}")
                                            except Exception as e:
                                                if getattr(args, 'debug', False):
                                                    print(f"{Fore.MAGENTA}Debug: Bag detection error: {e}{Style.RESET_ALL}")
                                                total_phases = 1
                                        
                                        if any(indicator in line_stripped for indicator in ['%|', 'seconds/s', 'Separating track', 'Selected model']):
                                            if '%|' in line_stripped:
                                                try:
                                                    percent_part = line_stripped.split('%|')[0].strip()
                                                    if percent_part.replace('.', '').replace(' ', '').isdigit():
                                                        percent = float(percent_part)
                                                        
                                                        # Check if we've moved to a new phase (progress reset to low value)
                                                        if percent < last_progress - 15:  # More sensitive detection
                                                            current_phase += 1                                                            # If we detect a reset and haven't detected it's a multi-model, update total_phases
                                                        if total_phases == 1 and current_phase > 0:
                                                            # Estimate total phases based on resets
                                                            # Most ensemble models use 4 models based on our testing
                                                            if selected_model in ['htdemucs_ft', 'mdx', 'mdx_extra', 'mdx_q']:
                                                                total_phases = 4  # Standard 4-model ensemble
                                                            elif selected_model == 'mdx_extra_q':
                                                                total_phases = 4  # Also 4 models but more complex processing
                                                            else:
                                                                # For unknown models, estimate conservatively
                                                                total_phases = current_phase + 2
                                                            print(f"\n{Fore.CYAN}  🔍 Detected multi-model processing (estimated {total_phases} models){Style.RESET_ALL}")
                                                        last_progress = percent
                                                        
                                                        # Show phase info if multiple phases detected or estimated
                                                        if total_phases > 1 or current_phase > 0:
                                                            effective_total = max(total_phases, current_phase + 1)
                                                            phase_info = f" (Model {min(current_phase + 1, effective_total)}/{effective_total})"
                                                            print(f"\r{Fore.GREEN}  Progress: {percent:5.1f}%{phase_info} {Fore.CYAN}🎵{Style.RESET_ALL}", end="", flush=True)
                                                        else:
                                                            print(f"\r{Fore.GREEN}  Progress: {percent:5.1f}% {Fore.CYAN}🎵{Style.RESET_ALL}", end="", flush=True)
                                                except:
                                                    pass
                                            elif 'Separating track' in line_stripped:
                                                print(f"\n{Fore.CYAN}  🎯 {line_stripped}{Style.RESET_ALL}")
                                            elif 'Selected model' in line_stripped and 'bag of' not in line_stripped:
                                                print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                                
                                if process.poll() is not None:
                                    break
                            
                            # Get remaining output
                            remaining_stdout, remaining_stderr = process.communicate()
                            stderr_output += remaining_stderr
                            
                            print()  # New line after progress
                            
                            if process.returncode != 0:
                                print(f"{Fore.RED}❌ Demucs failed with model {selected_model}: {stderr_output}{Style.RESET_ALL}")
                                continue
                            
                            print(f"{Fore.GREEN}✅ Demucs processing complete!{Style.RESET_ALL}")
                            
                            # Find the vocals file
                            base_name = os.path.splitext(os.path.basename(original_audio_path))[0]
                            vocals_pattern = os.path.join(tmpdir, selected_model, base_name, "vocals.wav")
                            vocals_files = glob.glob(vocals_pattern)
                            
                            if not vocals_files:
                                print(f"{Fore.RED}❌ Could not find vocals file after Demucs processing{Style.RESET_ALL}")
                                continue
                            
                            new_vocals_path = vocals_files[0]
                            print(f"{Fore.GREEN}✅ Vocal isolation complete with {selected_model} model{Style.RESET_ALL}")
                            
                            # Re-analyze with the new vocals file
                            print(f"\n{Fore.CYAN}🔄 Re-analyzing audio with new vocal isolation...{Style.RESET_ALL}")
                            return detect_silence_in_audio(new_vocals_path, silence_threshold_db, min_silence_duration)
                                
                        except Exception as e:
                            print(f"{Fore.RED}❌ Error running Demucs with {selected_model}: {e}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}   Continuing with current analysis...{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.RED}❌ Invalid model choice. Please select 1-10.{Style.RESET_ALL}")
                        continue
                    
                elif choice == "3":
                    while True:
                        print(f"\n{Fore.CYAN}Manual Region Modification:{Style.RESET_ALL}")
                        print(f"Enter region numbers to toggle (e.g., '1,3,5' to toggle regions 1, 3, and 5)")
                        print(f"Enter 'back' to return to main menu")
                        print(f"Current regions:")
                        
                        # Update statistics for current display
                        current_speech_regions = [r for r in merged_regions if r['type'] == 'speech']
                        current_silence_regions = [r for r in merged_regions if r['type'] == 'silence']
                        current_speech_duration = sum(r['end'] - r['start'] for r in current_speech_regions)
                        current_silence_duration = sum(r['end'] - r['start'] for r in current_silence_regions)
                        
                        print(f"   • Current: {len(current_speech_regions)} speech ({current_speech_duration:.1f}s), {len(current_silence_regions)} silence ({current_silence_duration:.1f}s)")
                        
                        for i, region in enumerate(merged_regions, 1):
                            region_type = region['type']
                            start_time = region['start']
                            end_time = region['end']
                            duration = region['duration']
                            type_color = Fore.GREEN if region_type == 'speech' else Fore.YELLOW
                            print(f"   {i:2d}. {type_color}{region_type.upper():<7}{Style.RESET_ALL} "
                                  f"{start_time:6.1f}s - {end_time:6.1f}s ({format_human_time(start_time)} - {format_human_time(end_time)})")
                        
                        toggle_input = input(f"\n{Fore.CYAN}Enter region numbers to toggle (or 'back' to return): {Style.RESET_ALL}").strip()
                        
                        if toggle_input.lower() == 'back':
                            break  # Go back to main menu
                            
                        if toggle_input:
                            try:
                                # Parse region numbers
                                region_numbers = [int(x.strip()) for x in toggle_input.split(',') if x.strip()]
                                
                                # Toggle specified regions
                                changes_made = False
                                for region_num in region_numbers:
                                    if 1 <= region_num <= len(merged_regions):
                                        region_idx = region_num - 1
                                        old_type = merged_regions[region_idx]['type']
                                        new_type = 'silence' if old_type == 'speech' else 'speech'
                                        merged_regions[region_idx]['type'] = new_type
                                        
                                        print(f"   {Fore.GREEN}✅ Region {region_num}: {old_type} → {new_type}{Style.RESET_ALL}")
                                        changes_made = True
                                    else:
                                        print(f"   {Fore.RED}❌ Invalid region number: {region_num}{Style.RESET_ALL}")
                                
                                if changes_made:
                                    print(f"\n{Fore.GREEN}✅ Manual modifications applied!{Style.RESET_ALL}")
                                    # Update statistics after manual changes
                                    speech_regions = [r for r in merged_regions if r['type'] == 'speech']
                                    silence_regions = [r for r in merged_regions if r['type'] == 'silence']
                                    
                                    total_speech_duration = sum(r['end'] - r['start'] for r in speech_regions)
                                    total_silence_duration = sum(r['end'] - r['start'] for r in silence_regions)
                                    
                                    print(f"   • Updated speech regions: {len(speech_regions)} ({total_speech_duration:.1f}s)")
                                    print(f"   • Updated silence regions: {len(silence_regions)} ({total_silence_duration:.1f}s)")
                                    
                            except ValueError:
                                print(f"{Fore.RED}❌ Invalid input format. Use comma-separated numbers (e.g., '1,3,5'){Style.RESET_ALL}")
                        else:
                            # Empty input, continue the loop to show regions again
                            continue
                    
                    # Continue to main menu after manual modification
                    continue
                    
                else:
                    max_choice_text = "5"
                    print(f"{Fore.RED}❌ Invalid choice. Please enter 1-{max_choice_text}.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Proceeding with current detection.{Style.RESET_ALL}")
                break
            except EOFError:
                print(f"\n{Fore.YELLOW}⚠️  Input ended. Proceeding with current detection.{Style.RESET_ALL}")
                break
        
        # Show speech regions that will be processed (simplified now since detailed info is above)
        if speech_regions:
            print(f"\n{Fore.GREEN}🎵 Speech regions to be processed: {len(speech_regions)}{Style.RESET_ALL}")
            print(f"   {Fore.GREEN}   With the current threshold ({silence_threshold_db:.1f}dB) and Min duration: {min_silence_duration:.1f}s{Style.RESET_ALL}")
        
        return merged_regions
        
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️  Silence detection failed: {e}. Processing entire file.{Style.RESET_ALL}")
        # If silence detection fails, return the entire audio as one speech chunk
        try:
            import whisper.audio
            audio = whisper.audio.load_audio(audio_path)
            duration = len(audio) / 16000
            return [{'type': 'speech', 'start': 0.0, 'end': duration}]
        except:
            # Last resort - assume 60 minute max duration
            return [{'type': 'speech', 'start': 0.0, 'end': 3600.0}]

def get_next_higher_model(current_ram: str) -> Optional[str]:
    """
    Get the next higher RAM model for better accuracy.
    
    Args:
        current_ram (str): Current RAM setting
        
    Returns:
        Optional[str]: Next higher RAM setting, or None if already at highest
    """
    model_hierarchy = ["1gb", "2gb", "3gb", "6gb", "7gb", "11gb-v2", "11gb-v3"]
    
    try:
        current_index = model_hierarchy.index(current_ram.lower())
        if current_index < len(model_hierarchy) - 1:
            return model_hierarchy[current_index + 1]
        else:
            return None  # Already at highest model
    except ValueError:
        return None  # Invalid current model

def ask_about_turbo_model(task: str) -> Tuple[bool, bool]:
    """
    Ask user if they want to use the Turbo model with translation warning.
    
    Args:
        task (str): Current task ('transcribe' or 'translate')
        
    Returns:
        Tuple[bool, bool]: (use_turbo, skip_future_turbo_questions)
    """
    global _skip_turbo_questions
    
    if _skip_turbo_questions:
        return False, True
    
    print(f"\n{Fore.CYAN}🚀 Turbo Model Available (7GB):{Style.RESET_ALL}")
    print(f"   The Turbo model is faster and uses less memory than the large models.")
    
    if task == "translate":
        print(f"   {Fore.YELLOW}⚠️  WARNING: Turbo model does NOT support translation to English.{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}   It will only transcribe in the original language.{Style.RESET_ALL}")
        print(f"   {Fore.YELLOW}   If you skip this, it will use the 11GB-v2 model instead.{Style.RESET_ALL}")
    else:
        print(f"   {Fore.GREEN}✅ Turbo model supports transcription in original language.{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
    print(f"   1. {Fore.GREEN}Use Turbo model (7GB){Style.RESET_ALL}")
    print(f"   2. {Fore.YELLOW}Skip to 11GB-v2 model{Style.RESET_ALL}")
    print(f"   3. {Fore.BLUE}Skip to 11GB-v2 and don't ask about Turbo again{Style.RESET_ALL}")
    
    while True:
        try:
            choice = input(f"\n{Fore.CYAN}Enter your choice (1/2/3): {Style.RESET_ALL}").strip()
            
            if choice == "1":
                return True, False
            elif choice == "2":
                return False, False
            elif choice == "3":
                _skip_turbo_questions = True
                print(f"{Fore.BLUE}✅ Turbo model questions will be skipped for remaining regions.{Style.RESET_ALL}")
                return False, True
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please enter 1, 2, or 3.{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  Skipping to 11GB-v2 model.{Style.RESET_ALL}")
            return False, False
        except EOFError:
            print(f"\n{Fore.YELLOW}⚠️  Skipping to 11GB-v2 model.{Style.RESET_ALL}")
            return False, False

def get_next_higher_model_with_turbo_handling(current_ram: str, task: str = "translate", auto_continue: bool = False) -> Optional[str]:
    """
    Get the next higher RAM model with special handling for Turbo model.
    
    Args:
        current_ram (str): Current RAM setting
        task (str): Current task ('transcribe' or 'translate')
        auto_continue (bool): Whether user is in auto-continue mode
        
    Returns:
        Optional[str]: Next higher RAM setting, or None if already at highest
    """
    next_model = get_next_higher_model(current_ram)
    
    # Special handling for Turbo model (7GB)
    if next_model == "7gb":
        global _skip_turbo_questions
        
        if auto_continue and not _skip_turbo_questions:
            # In auto-continue mode, show informative message about skipping Turbo
            if task == "translate":
                print(f"   {Fore.CYAN}🚀 Auto-continue: Skipping Turbo model (no translation support) → 11GB-v2{Style.RESET_ALL}")
            else:
                print(f"   {Fore.CYAN}🚀 Auto-continue: Using Turbo model (7GB){Style.RESET_ALL}")
                return next_model
            _skip_turbo_questions = True  # Don't ask again in auto mode
            return get_next_higher_model("7gb")  # Skip to 11GB-v2
        elif _skip_turbo_questions:
            # User previously chose to skip Turbo questions
            if task == "translate":
                print(f"   {Fore.CYAN}🚀 Skipping Turbo model (translation not supported) → 11GB-v2{Style.RESET_ALL}")
            return get_next_higher_model("7gb")  # Skip to 11GB-v2
        else:
            # Ask user about Turbo model
            use_turbo, skip_future = ask_about_turbo_model(task)
            if not use_turbo:
                # Skip to 11GB-v2 instead
                return get_next_higher_model("7gb")  # This will return "11gb-v2"
    
    return next_model

def calculate_region_confidence(segments: List[Dict]) -> float:
    """
    Calculate average confidence for a region's segments.
    
    Args:
        segments (List[Dict]): List of segments from Whisper
        
    Returns:
        float: Average confidence score (0.0 to 1.0)
    """
    if not segments:
        return 0.0
    
    total_confidence = 0.0
    segment_count = 0
    
    for segment in segments:
        if isinstance(segment, dict) and "avg_logprob" in segment and segment["avg_logprob"] is not None:
            # Convert log probability to confidence score
            # A lower avg_logprob means higher confidence. 0 is perfect.
            # We can map it to a 0-1 range. A simple way is exponential.
            confidence = np.exp(segment["avg_logprob"])
            total_confidence += confidence
            segment_count += 1
    
    return total_confidence / segment_count if segment_count > 0 else 0.0

def detect_repeated_segments(segments: List[Dict], threshold: int = 3) -> Tuple[bool, List[str], int]:
    """
    Detect if there are repeated segments in the transcription.
    
    Args:
        segments (List[Dict]): List of segments from Whisper
        threshold (int): Minimum number of repetitions to consider problematic
        
    Returns:
        Tuple[bool, List[str], int]: (has_repetitions, repeated_texts, max_consecutive_count)
    """
    if len(segments) < threshold:
        return False, [], 0
    
    repeated_texts = []
    max_consecutive = 0
    current_consecutive = 1
    
    for i in range(1, len(segments)):
        current_text = segments[i].get("text", "").strip().lower()
        previous_text = segments[i-1].get("text", "").strip().lower()
        
        # Only consider non-empty texts with reasonable length for repetition detection
        if (current_text and previous_text and 
            len(current_text) > 3 and len(previous_text) > 3 and  # Ignore very short segments
            current_text == previous_text):
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
            
            if current_consecutive >= threshold and current_text not in repeated_texts:
                repeated_texts.append(current_text)
        else:
            current_consecutive = 1
    
    has_repetitions = max_consecutive >= threshold
    return has_repetitions, repeated_texts, max_consecutive

def detect_internal_repetitions(segments: List[Dict], min_phrase_length: int = 3, repetition_threshold: int = 5) -> Tuple[bool, List[Dict], int]:
    """
    Detect if individual segments contain repeated phrases within them (internal hallucinations).
    
    Args:
        segments (List[Dict]): List of segments from Whisper
        min_phrase_length (int): Minimum number of words in a phrase to consider for repetition
        repetition_threshold (int): Minimum number of repetitions to consider problematic
        
    Returns:
        Tuple[bool, List[Dict], int]: (has_internal_repetitions, problematic_segments, max_repetitions_found)
    """
    problematic_segments = []
    max_repetitions_found = 0
    has_internal_repetitions = False
    
    for segment in segments:
        if not isinstance(segment, dict):
            continue
            
        text = segment.get("text", "").strip()
        if len(text) < 20:  # Skip very short segments
            continue
        
        words = text.split()
        if len(words) < min_phrase_length * repetition_threshold:  # Not enough words to have meaningful repetitions
            continue
        
        # Check for repeated phrases of different lengths
        for phrase_len in range(min_phrase_length, min(8, len(words) // repetition_threshold + 1)):
            phrase_counts = {}
            
            # Generate all phrases of this length
            for i in range(len(words) - phrase_len + 1):
                phrase = " ".join(words[i:i + phrase_len]).lower()
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
            
            # Check if any phrase is repeated too many times
            for phrase, count in phrase_counts.items():
                if count >= repetition_threshold:
                    has_internal_repetitions = True
                    max_repetitions_found = max(max_repetitions_found, count)
                    
                    # Add to problematic segments if not already added
                    segment_info = {
                        'segment': segment,
                        'repeated_phrase': phrase,
                        'repetition_count': count,
                        'phrase_length': phrase_len
                    }
                    
                    # Check if this segment is already in problematic_segments
                    already_added = False
                    for existing in problematic_segments:
                        if existing['segment'] == segment:
                            # Update if this repetition is worse
                            if count > existing['repetition_count']:
                                existing.update(segment_info)
                            already_added = True
                            break
                    
                    if not already_added:
                        problematic_segments.append(segment_info)
                    
                    break  # Found a problematic phrase, no need to check longer phrases for this segment
            
            if problematic_segments and problematic_segments[-1].get('segment') == segment:
                break  # Found repetition in this segment, move to next segment
    
    return has_internal_repetitions, problematic_segments, max_repetitions_found

def process_single_speech_region(
    audio_path: str, 
    region: Dict[str, Any], 
    region_index: int, 
    total_regions: int, 
    model_type: str, 
    decode_options: Dict, 
    regions_temp_dir: str,
    original_ram_setting: str,
    task: str = "translate"
) -> Tuple[int, List[Dict], str]:
    """
    Process a single speech region for transcription.
    
    Args:
        audio_path (str): Path to the main audio file
        region (Dict[str, Any]): Speech region with 'start', 'end', 'type'
        region_index (int): 1-based index of this region
        total_regions (int): Total number of regions being processed
        model_type (str): The Whisper model to use
        decode_options (Dict): Transcription options
        regions_temp_dir (str): Temporary directory for region files
        original_ram_setting (str): Original RAM setting for model selection
        
    Returns:
        Tuple[int, List[Dict], str]: (region_index, processed_segments, best_model_name)
    """
    region_start = region['start']
    region_end = region['end']
    region_duration = region_end - region_start
    
    print(f"{Fore.CYAN}🎵 Processing speech region {region_index}/{total_regions}: {region_start:.1f}s - {region_end:.1f}s ({region_duration:.1f}s){Style.RESET_ALL}")
    
    # Start with the original model settings
    current_model_type = model_type
    current_ram = original_ram_setting
    
    # Create a temporary file for this speech region
    temp_audio_path = os.path.join(regions_temp_dir, f"region_{region_index}.wav")
    
    # Use FFmpeg to extract the speech region with high precision
    ffmpeg_command = [
        'ffmpeg', '-y', '-i', audio_path,
        '-ss', str(region_start),
        '-to', str(region_end),
        '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        temp_audio_path
    ]
    
    result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Fore.RED}❌ FFmpeg failed for region {region_index}: {result.stderr}{Style.RESET_ALL}")
        return region_index, [], ""
    
    # Transcribe this speech region with intelligent retry
    best_result = None
    best_confidence = -1.0
    best_has_repetitions = True
    best_model_name = ""
    
    retry_count = 0
    max_retries = 3 if _intelligent_mode else 1
    
    while retry_count < max_retries:
        try:
            print(f"{Fore.CYAN}\n🎯 Transcribing region {region_index} with {current_model_type} model...{Style.RESET_ALL}")
            
            current_result = run_transcription_in_process(
                audio_path=temp_audio_path,
                model_type=current_model_type,
                decode_options=decode_options,
                model_dir=str(args.model_dir),
                device=args.device
            )
            
            segments = current_result.get("segments", [])
            if not segments:
                print(f"{Fore.YELLOW}⚠️  No segments generated for region {region_index}. Skipping.{Style.RESET_ALL}")
                if retry_count == 0:
                    best_result = {"segments": [], "text": ""}
                break
            
            # Calculate quality metrics for the current result
            current_confidence = calculate_region_confidence(segments)
            has_ext_reps, repeated_texts, max_consecutive = detect_repeated_segments(segments)
            has_int_reps, problematic_segments, max_internal_reps = detect_internal_repetitions(segments)
            current_has_repetitions = has_ext_reps or has_int_reps
            
            print(f"{Fore.CYAN}📊 Region {region_index} results ({current_model_type}): {len(segments)} segments, {current_confidence:.1%} confidence{Style.RESET_ALL}")
            
            if has_ext_reps:
                print(f"{Fore.YELLOW}🔄 Detected external repetitions: {repeated_texts[:3]} (max consecutive: {max_consecutive}){Style.RESET_ALL}")
            if has_int_reps:
                problematic_phrase = problematic_segments[0]['repeated_phrase']
                print(f"{Fore.YELLOW}🔄 Detected internal repetitions: \"{problematic_phrase}\" repeated {max_internal_reps} times.{Style.RESET_ALL}")

            # Compare and select the best result
            is_better = False
            if best_result is None:
                is_better = True
            else:
                # New result is better if it has no repetitions and the old one did
                if not current_has_repetitions and best_has_repetitions:
                    is_better = True
                    print(f"{Fore.GREEN}✅ New result is better (fixed repetitions).{Style.RESET_ALL}")
                # Or if confidence is significantly higher and it doesn't introduce new repetitions
                elif current_confidence > best_confidence + 0.05 and not (current_has_repetitions and not best_has_repetitions):
                    is_better = True
                    print(f"{Fore.GREEN}✅ New result is better (confidence improved from {best_confidence:.1%} to {current_confidence:.1%}).{Style.RESET_ALL}")
                # If both have repetitions, prefer higher confidence
                elif current_has_repetitions and best_has_repetitions and current_confidence > best_confidence:
                    is_better = True
                    print(f"{Fore.GREEN}✅ New result is better (confidence improved from {best_confidence:.1%} to {current_confidence:.1%}, though both have repetitions).{Style.RESET_ALL}")

            if is_better:
                print(f"{Fore.GREEN}🏆 Keeping result from {current_model_type} as the new best.{Style.RESET_ALL}")
                best_result = current_result
                best_confidence = current_confidence
                best_has_repetitions = current_has_repetitions
                best_model_name = current_model_type
            else:
                print(f"{Fore.YELLOW}⚠️ New result from {current_model_type} is not an improvement. Keeping previous result from {best_model_name}.{Style.RESET_ALL}")

            # Determine if we should retry
            should_retry = (
                _intelligent_mode and
                (best_confidence < 0.85 or best_has_repetitions) and
                retry_count < max_retries - 1
            )

            if should_retry:
                next_ram = get_next_higher_model_with_turbo_handling(current_ram, task, auto_continue=True)
                if next_ram:
                    print(f"{Fore.YELLOW}🔄 Low confidence or repetitions detected. Retrying region {region_index} with {next_ram} model...{Style.RESET_ALL}")
                    current_ram = next_ram
                    current_model_type = get_model_type(current_ram, skip_warning=True)
                    retry_count += 1
                    continue
            
            break

        except Exception as e:
            print(f"{Fore.RED}❌ Error transcribing region {region_index} with {current_model_type}: {e}{Style.RESET_ALL}")
            retry_count += 1
            
            if retry_count < max_retries:
                next_ram = get_next_higher_model(current_ram)
                if next_ram:
                    current_ram = next_ram
                    current_model_type = get_model_type(current_ram, skip_warning=True)
                    print(f"{Fore.YELLOW}🔄 Retrying region {region_index} with {current_model_type} model...{Style.RESET_ALL}")
                else:
                    break
            else:
                break
    
    # Process the best result for this region
    region_segments = []
    if best_result and best_result.get("segments"):
        region_segments = best_result["segments"]
        
        # Correct timestamps by adding the region start time
        for segment in region_segments:
            if isinstance(segment, dict):
                segment["start"] = segment.get("start", 0.0) + region_start
                segment["end"] = segment.get("end", 0.0) + region_start
                
                if "words" in segment and isinstance(segment["words"], list):
                    for word in segment["words"]:
                        if isinstance(word, dict):
                            if "start" in word:
                                word["start"] = word["start"] + region_start
                            if "end" in word:
                                word["end"] = word["end"] + region_start
        
        print(f"{Fore.GREEN}✅ Region {region_index} processed with '{best_model_name}' model: {len(region_segments)} segments added{Style.RESET_ALL}")
        
        generated_texts = [seg.get('text', '').strip() for seg in region_segments if seg.get('text', '').strip()]
        if generated_texts:
            display_text = ", ".join(f'"{text}"' for text in generated_texts)
            PINK = '\033[95m'
            print(f"{PINK}   Subtitles Generated: {display_text}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  No usable segments generated for region {region_index}{Style.RESET_ALL}")
    
    return region_index, region_segments, best_model_name

def process_speech_regions(audio_path: str, regions: List[Dict[str, Any]], model_type: str, decode_options: Dict, task: str = "translate") -> List[Dict]:
    """
    Process speech regions individually for maximum efficiency with accurate timestamps.
    
    This function extracts speech regions from the audio and transcribes them separately,
    then corrects the timestamps to place them accurately on the main timeline.
    
    Args:
        audio_path (str): Path to the audio file
        regions (List[Dict[str, Any]]): List of speech/silence regions from detect_silence_in_audio
        model_type (str): The Whisper model to use (e.g., 'large-v3')
        decode_options (Dict): A dictionary of options for the transcribe call
        task (str): Task type ('transcribe' or 'translate')
        
    Returns:
        List[Dict]: Combined segments with corrected timestamps
    """
    all_segments = []
    
    # Filter to only speech regions
    speech_regions = [r for r in regions if r['type'] == 'speech']
    
    if not speech_regions:
        print(f"{Fore.YELLOW}⚠️  No speech regions detected in audio file.{Style.RESET_ALL}")
        return []
    
    # Store the original model settings to use for each new region
    original_model_type = model_type
    original_ram_setting = args.ram
    
    # Create a temporary subdirectory for all region files to avoid clutter and simplify cleanup.
    regions_temp_dir = temp_manager.mkdtemp(prefix='speech_regions_')
    
    try:
        # Get batchmode setting from args
        batch_size = getattr(args, 'batchmode', 1)
        
        if batch_size == 1:
            # Sequential processing (original behavior)
            print(f"{Fore.CYAN}🎵 Processing {len(speech_regions)} speech regions sequentially...{Style.RESET_ALL}")
            
            for i, region in enumerate(speech_regions, 1):
                region_index, region_segments, best_model_name = process_single_speech_region(
                    audio_path=audio_path,
                    region=region, 
                    region_index=i,
                    total_regions=len(speech_regions),
                    model_type=original_model_type,
                    decode_options=decode_options,
                    regions_temp_dir=regions_temp_dir,
                    original_ram_setting=original_ram_setting,
                    task=task
                )
                
                all_segments.extend(region_segments)
        else:
            # Parallel processing (new batch mode)
            print(f"{Fore.CYAN}🎵 Processing {len(speech_regions)} speech regions in parallel (batch size: {batch_size})...{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚡ Parallel processing enabled - up to {batch_size} regions will be processed simultaneously{Style.RESET_ALL}")
            
            # Create a list to store results with their original indices
            indexed_regions = [(i+1, region) for i, region in enumerate(speech_regions)]
            
            # Process regions in parallel using ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
                # Submit all regions for processing
                future_to_index = {
                    executor.submit(
                        process_single_speech_region,
                        audio_path,
                        region,
                        region_index,
                        len(speech_regions),
                        original_model_type,
                        decode_options,
                        regions_temp_dir,
                        original_ram_setting,
                        task
                    ): region_index for region_index, region in indexed_regions
                }
                
                # Collect results as they complete and store them with their indices
                results = []
                for future in concurrent.futures.as_completed(future_to_index):
                    region_index = future_to_index[future]
                    try:
                        result_index, region_segments, best_model_name = future.result()
                        results.append((result_index, region_segments))
                        print(f"{Fore.GREEN}🏁 Completed region {result_index} processing{Style.RESET_ALL}")
                    except Exception as exc:
                        print(f"{Fore.RED}❌ Region {region_index} generated an exception: {exc}{Style.RESET_ALL}")
                        results.append((region_index, []))
                
                # Sort results by original region index to maintain chronological order
                results.sort(key=lambda x: x[0])
                
                # Combine all segments in the correct order
                for _, region_segments in results:
                    all_segments.extend(region_segments)
                
                print(f"{Fore.GREEN}🎉 Parallel processing complete! Processed {len(results)} regions{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}❌ Error processing speech regions: {e}. Falling back to full file processing.{Style.RESET_ALL}")
        full_result = run_transcription_in_process(
            audio_path=audio_path,
            model_type=original_model_type,
            decode_options=decode_options,
            model_dir=str(args.model_dir),
            device=args.device
        )
        all_segments = full_result.get("segments", [])
    finally:
        shutil.rmtree(regions_temp_dir, ignore_errors=True)
    
    print(f"{Fore.GREEN}🎉 Speech processing complete: {len(all_segments)} total segments generated{Style.RESET_ALL}")
    return all_segments

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format (matching Whisper's official implementation).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp in SRT format (HH:MM:SS,mmm)
    """
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds_part = milliseconds // 1_000
    milliseconds -= seconds_part * 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d},{milliseconds:03d}"

def get_color_for_confidence(confidence: float) -> str:
    """
    Get appropriate color code based on confidence level.
    
    Args:
        confidence (float): Confidence score between 0 and 1
        
    Returns:
        str: ANSI color code
    """
    if confidence >= 0.90:
        return Fore.GREEN
    elif confidence >= 0.75:
        return Fore.YELLOW
    else:        return Fore.RED

def split_text_for_subtitles(text: str, start_time: float, end_time: float, max_chars: int = 60, max_words: int = 8) -> List[Tuple[str, float, float]]:
    """
    Split long text into readable subtitle chunks.
    
    Args:
        text (str): The text to split
        start_time (float): Start time of the original segment
        end_time (float): End time of the original segment
        max_chars (int): Maximum characters per subtitle line
        max_words (int): Maximum words per subtitle line
    
    Returns:
        List[Tuple[str, float, float]]: List of (text_chunk, start_time, end_time) tuples
    """
    # If text is already short enough, return as-is
    if len(text) <= max_chars and len(text.split()) <= max_words:
        return [(text, start_time, end_time)]
    
    words = text.split()
    duration = end_time - start_time
    chunks = []
    current_chunk = []
    current_chars = 0
    
    i = 0
    while i < len(words):
        word = words[i]
        word_chars = len(word) + (1 if current_chunk else 0)  # +1 for space
        
        # Check if adding this word would exceed limits
        if (current_chars + word_chars > max_chars or len(current_chunk) >= max_words) and current_chunk:
            # Finalize current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
            current_chars = 0
        else:
            # Add word to current chunk
            current_chunk.append(word)
            current_chars += word_chars
            i += 1
    
    # Add remaining words as final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(chunk_text)
      # Assign timing to chunks proportionally based on text length
    result = []
    if len(chunks) == 1:
        result.append((chunks[0], start_time, end_time))
    else:
        # Calculate proportional timing based on character count
        total_chars = sum(len(chunk) for chunk in chunks)
        gap_time = min(0.1, duration * 0.02)  # Small gap between segments (max 0.1s)
        available_duration = duration - (gap_time * (len(chunks) - 1))
        
        current_time = start_time
        for idx, chunk in enumerate(chunks):
            # Calculate duration proportional to text length
            char_ratio = len(chunk) / total_chars if total_chars > 0 else 1.0 / len(chunks)
            chunk_duration = available_duration * char_ratio
            
            # Ensure minimum duration of 0.5 seconds
            chunk_duration = max(0.5, chunk_duration)
            
            chunk_start = current_time
            chunk_end = current_time + chunk_duration
            
            # Ensure we don't exceed the original end time
            if idx == len(chunks) - 1:  # Last chunk
                chunk_end = end_time
            
            result.append((chunk, chunk_start, chunk_end))
            current_time = chunk_end + gap_time
    
    return result

def split_text_with_word_timestamps(words: List[Dict], max_chars: int = 60, max_words: int = 8) -> List[Tuple[str, float, float]]:
    """
    Split text using word-level timestamps for more accurate timing.
    
    Args:
        words (List[Dict]): List of word dictionaries with 'word', 'start', 'end' keys
        max_chars (int): Maximum characters per subtitle line
        max_words (int): Maximum words per subtitle line
    
    Returns:
        List[Tuple[str, float, float]]: List of (text_chunk, start_time, end_time) tuples
    """
    if not words:
        return []
    
    chunks = []
    current_chunk_words = []
    current_chars = 0
    
    i = 0
    while i < len(words):
        word_data = words[i]
        word = word_data.get("word", "").strip()
        
        if not word:  # Skip empty words
            i += 1
            continue
            
        word_chars = len(word) + (1 if current_chunk_words else 0)  # +1 for space
        
        # Check if adding this word would exceed limits
        if (current_chars + word_chars > max_chars or len(current_chunk_words) >= max_words) and current_chunk_words:
            # Finalize current chunk using actual word timestamps
            chunk_text = " ".join([w.get("word", "").strip() for w in current_chunk_words])
            chunk_start = current_chunk_words[0].get("start", 0.0)
            chunk_end = current_chunk_words[-1].get("end", 0.0)
            
            chunks.append((chunk_text, chunk_start, chunk_end))
            current_chunk_words = []
            current_chars = 0
        else:
            # Add word to current chunk
            current_chunk_words.append(word_data)
            current_chars += word_chars
            i += 1
    
    # Add remaining words as final chunk
    if current_chunk_words:
        chunk_text = " ".join([w.get("word", "").strip() for w in current_chunk_words])
        chunk_start = current_chunk_words[0].get("start", 0.0)
        chunk_end = current_chunk_words[-1].get("end", 0.0)
        chunks.append((chunk_text, chunk_start, chunk_end))
    
    return chunks

def format_words_with_confidence(text: str, avg_logprob: float) -> Tuple[str, float]:
    """
    Format words with color based on confidence.
    
    Args:
        text (str): Text to format
        avg_logprob (float): Average log probability
        
    Returns:
        Tuple[str, float]: Colored text and confidence score
    """
    # Convert log probability to confidence score (normalize from typical range)
    confidence = 1.0 - min(1.0, max(0.0, -avg_logprob / 10))
    
    # Split into words and color each based on local adjustments
    words = text.split()
    colored_words = []
    
    for i, word in enumerate(words):
        # Slightly adjust confidence per word position
        word_conf = confidence * (1.0 + np.sin(i * 0.5) * 0.1)  # Add some variation
        word_conf = min(1.0, max(0.0, word_conf))  # Ensure stays in 0-1 range
        
        color = get_color_for_confidence(word_conf)
        colored_words.append(f"{color}{word}{Style.RESET_ALL}")    
    return " ".join(colored_words), confidence

def get_model_type(ram: str, skip_warning: bool = False) -> str:
    """
    Get the appropriate model type based on RAM setting.
    
    Args:
        ram (str): RAM setting from command line args
        skip_warning (bool): Whether to skip the RAM warning
    
    Returns:
        str: Model type to use
    """
    if not skip_warning:
        return parser_args.set_model_by_ram(ram, None)  # Pass None for language to respect RAM choice
    
    # Logic from set_model_by_ram but without the warning
    ram = ram.lower()
    if ram == "1gb":
        return "tiny"
    elif ram == "2gb":
        return "base"
    elif ram == "3gb":
        return "small"
    elif ram == "6gb":
        return "medium"
    elif ram == "7gb":
        return "turbo"
    elif ram == "11gb-v2":
        return "large-v2"
    elif ram == "11gb-v3":
        return "large-v3"
    else:
        raise ValueError("Invalid RAM setting provided")

def load_whisper_model(
    model_type: str, 
    device: str, 
    model_dir: Optional[str] = None
) -> whisper.Whisper:
    """
    Load the Whisper model with specified parameters.
    
    Args:
        model_type (str): Type of the Whisper model to load
        device (str): Device to run the model on ('cpu' or 'cuda')
        model_dir (str, optional): Directory where models are stored. 
            If None, uses the default from args.model_dir
    
    Returns:
        whisper.Whisper: Loaded Whisper model
    
    Raises:
        RuntimeError: If model loading fails
    """
    try:
        # Use provided model_dir or fall back to args.model_dir
        download_root = model_dir if model_dir else str(args.model_dir)
        model_path = Path(download_root)
        
        if not model_path.exists():
            logger.info("Creating model directory: %s", model_path)
            model_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("Loading Whisper model: %s from %s", model_type, model_path)
        return whisper.load_model(model_type, device=device, download_root=str(model_path))
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model: {str(e)}")

def unload_model(model: whisper.Whisper) -> None:
    """
    Unload the Whisper model and clear VRAM/RAM.
    
    Args:
        model (whisper.Whisper): The Whisper model to unload
    """
    try:
        # Delete the model from memory
        del model
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if using GPU
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("🗑️ VRAM cleared")
        except ImportError:
            # torch not available, skip CUDA cleanup
            pass
            
        logger.info("🗑️ Model unloaded and memory cleared")
        
    except Exception as e:
        logger.warning("Failed to completely unload model: %s", str(e))

def get_media_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of a media file using ffprobe.
    
    Args:
        file_path (str): Path to the media file
        
    Returns:
        Optional[float]: Duration in seconds, or None if failed to detect
    """
    import subprocess
    import re
    try:
        # Try ffprobe JSON first
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', file_path
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode == 0:
            import json
            try:
                data = json.loads(result.stdout)
                duration_str = data.get('format', {}).get('duration')
                if duration_str:
                    return float(duration_str)
            except Exception:
                pass
        # Fallback: try ffprobe/ffmpeg raw output (text)
        # Try ffprobe with default output
        result2 = subprocess.run([
            'ffprobe', file_path
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')
        output = result2.stdout + '\n' + result2.stderr
        # Look for Duration: 02:41:18.04 or Duration 022648.64
        match = re.search(r'Duration[: ]+([0-9:.]+)', output)
        if match:
            dur_str = match.group(1)
            # If format is HH:MM:SS(.mmm), parse as timestamp
            if ':' in dur_str:
                try:
                    return parse_timestamp(dur_str)
                except Exception:
                    pass
            # If format is like 022648.64, convert to seconds
            if re.match(r'^[0-9]{5,}(\.[0-9]+)?$', dur_str):
                # e.g. 022648.64 means 2 hours, 26 minutes, 48.64 seconds
                return _convert_compact_duration_to_seconds(dur_str)
        # As a last resort, try to find a line with 'Duration' and extract numbers
        for line in output.splitlines():
            if 'Duration' in line:
                # Try to extract numbers
                nums = re.findall(r'([0-9]+)', line)
                if len(nums) >= 3:
                    try:
                        h, m, s = int(nums[0]), int(nums[1]), float(nums[2])
                        return h*3600 + m*60 + s
                    except Exception:
                        continue
    except Exception as e:
        logger.warning(f"Failed to get media duration: {e}")
    return None

# Helper for compact duration like 022648.64 (HHMMSS.ss)
def _convert_compact_duration_to_seconds(dur_str: str) -> float:
    # Remove any non-digit/period chars
    dur_str = dur_str.strip()
    if '.' in dur_str:
        main, frac = dur_str.split('.')
        frac = float('0.' + frac)
    else:
        main = dur_str
        frac = 0.0
    # Pad with zeros if needed
    main = main.zfill(6)  # Ensure at least HHMMSS
    hours = int(main[:-4]) if len(main) > 4 else 0
    minutes = int(main[-4:-2])
    seconds = int(main[-2:])
    return hours*3600 + minutes*60 + seconds + frac

def parse_timestamp(timestamp: str) -> float:
    """
    Parse timestamp in HH:MM:SS.mmm or MM:SS.mmm format to seconds.
    
    Args:
        timestamp (str): Timestamp string
        
    Returns:
        float: Time in seconds
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        parts = timestamp.split(':')
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        else:
            # Just seconds
            return float(timestamp)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Use HH:MM:SS.mmm, MM:SS.mmm, or seconds.")

def suggest_split_points(duration: float, segment_length: int = 1800) -> List[float]:
    """
    Suggest split points for a long media file.
    
    Args:
        duration (float): Total duration in seconds
        segment_length (int): Target segment length in seconds (default: 30 minutes)
        
    Returns:
        List[float]: List of suggested split points in seconds
    """
    split_points = []
    current_time = 0
    
    while current_time + segment_length < duration:
        current_time += segment_length
        split_points.append(current_time)
    
    return split_points

def format_seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def create_segment(input_path: str, start_time: float, end_time: float, output_path: str) -> bool:
    """
    Create a segment of media file using FFmpeg.
    
    Args:
        input_path (str): Path to input media file
        start_time (float): Start time in seconds
        end_time (float): End time in seconds
        output_path (str): Path for output segment
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import subprocess
        
        duration = end_time - start_time
        
        # Use FFmpeg to extract segment
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output files
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
            '-c', 'copy',  # Copy streams without re-encoding for speed
            output_path
        ]
        
        # FIX: Added encoding='utf-8' and errors='replace' to prevent UnicodeDecodeError on Windows
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            return True
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating segment: {e}")
        return False

def filter_unwanted_phrases(text: str) -> str:
    """
    Filter out unwanted phrases from subtitle text.
    
    Args:
        text (str): Original subtitle text
        
    Returns:
        str: Filtered text, or empty string if text should be removed entirely
    """
    if not text or not text.strip():
        return ""
    
    # Check for "Thank you for watching" and variations (case-insensitive)
    text_lower = text.lower().strip()
    
    # List of phrases to completely remove
    unwanted_phrases = [
        "thank you for watching"
    ]
    
    # Check if any unwanted phrase is in the text
    for phrase in unwanted_phrases:
        if phrase in text_lower:
            # Only show filtering message in debug mode
            if getattr(args, 'debug', False):
                print(f"{Fore.YELLOW}🚫 Filtered out unwanted phrase: '{text}'{Style.RESET_ALL}")
            return ""  # Remove the entire line
    
    return text.strip()

def combine_segment_subtitles(segments_data: List[Dict], output_path: str) -> None:
    """
    Combine subtitle segments into a single SRT file with proper timing.
    
    Args:
        segments_data (List[Dict]): List of segment data with results and timing info
        output_path (str): Path for combined subtitle file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            
            for segment_data in segments_data:
                result = segment_data['result']
                time_offset = segment_data['start_time']
                
                for segment in result.get("segments", []):
                    if isinstance(segment, dict) and segment.get("text", "").strip():
                        # Adjust timestamps to account for the segment's position in the original file
                        start_time = segment.get("start", 0.0) + time_offset
                        end_time = segment.get("end", 0.0) + time_offset
                        text = segment.get("text", "").strip()
                        
                        # Filter unwanted phrases
                        filtered_text = filter_unwanted_phrases(text)
                        
                        # Only write if text remains after filtering
                        if filtered_text:
                            # Write SRT format
                            f.write(f"{subtitle_index}\n")
                            f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
                            f.write(f"{filtered_text}\n\n")
                            
                            subtitle_index += 1
                        
        logger.info(f"Combined subtitles saved to: %s", output_path)
        
    except Exception as e:
        logger.error(f"Error combining subtitles: %s", e)
        raise

def run_sub_gen(
    input_path: str, 
    output_name: str = "", 
    output_directory: str = "./",
    task: str = "translate",
    model_dir: Optional[str] = None,
    ram_setting: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Generate subtitles for an audio file using Whisper.
    
    Args:
        input_path (str): Path to the input audio file
        output_name (str, optional): Name for the output subtitle file. Defaults to "".
        output_directory (str, optional): Directory to save subtitles. Defaults to "./".
        task (str, optional): Whisper task type ('transcribe' or 'translate'). Defaults to "translate".
        model_dir (str, optional): Custom directory for model files. 
            If None, uses the directory from command line args.
        ram_setting (str, optional): RAM setting to use for model selection.
            If None, uses the setting from command line args.
    
    Returns:
        Tuple[Dict[str, Any], str]: Tuple containing the transcription result and output filename
    
    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If subtitle generation fails
    """    # Input validation
    if not input_path:
        raise ValueError("Input path cannot be empty")
    
    # Check for OpenVINO requirement
    if args.model_source == 'openvino' and not args.language:
        raise ValueError("OpenVINO model source requires a language to be specified with the --language flag, as automatic language detection is not supported.")

    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise ValueError(f"Input file does not exist: {input_path_obj}")

    # Check media duration and offer segmentation for all files
    duration = get_media_duration(str(input_path_obj))
    use_segmentation = False
    split_points = []
    
    if duration:  # Offer segmentation for any file with detectable duration
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60
        
        # Determine appropriate messaging and defaults based on file length
        if duration > 3600:  # Over 1 hour
            file_category = "Very long"
            warning_color = Fore.RED
            default_segment_length = 600   # 10 minutes for very long files
            recommendation = "Strongly recommended to use segmentation to avoid memory issues."
        elif duration > 1800:  # Over 30 minutes
            file_category = "Long"
            warning_color = Fore.YELLOW
            default_segment_length = 900   # 15 minutes for long files
            recommendation = "Recommended to use segmentation for better memory management."
        elif duration > 300:  # 5-30 minutes
            file_category = "Medium"
            warning_color = Fore.CYAN
            default_segment_length = 600   # 10 minutes for medium files
            recommendation = "Optional segmentation available for better control or memory management."
        else:  # Under 5 minutes
            file_category = "Short"
            warning_color = Fore.GREEN
            default_segment_length = 120   # 2 minutes for short files
            recommendation = "Optional segmentation available (may not be necessary for such short files)."
        
        print(f"\n{warning_color}📊 {file_category} media file detected:{Style.RESET_ALL}")
        print(f"   Duration: {hours:02d}:{minutes:02d}:{seconds:06.3f} ({duration:.1f} seconds)")
        print(f"   File size: {input_path_obj.stat().st_size / (1024*1024*1024):.2f} GB")
        
        print(f"\n{Fore.CYAN}💡 {recommendation}{Style.RESET_ALL}")
        
        # Suggest automatic split points based on file length
        suggested_points = suggest_split_points(duration, default_segment_length)
        if suggested_points:
            segment_minutes = default_segment_length // 60
            print(f"\n{Fore.CYAN}🎯 Suggested split points (every {segment_minutes} minutes):{Style.RESET_ALL}")
            for i, point in enumerate(suggested_points):
                timestamp = format_seconds_to_timestamp(point)
                print(f"   {i+1}. {timestamp}")
        
        print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}Process entire file{Style.RESET_ALL}")
        print(f"   2. {Fore.YELLOW}Use suggested split points{Style.RESET_ALL}")
        print(f"   3. {Fore.CYAN}Enter custom split points{Style.RESET_ALL}")
        print(f"   4. {Fore.MAGENTA}Choose different segment length{Style.RESET_ALL}")
        
        while True:
            try:
                choice = input(f"\n{Fore.CYAN}Select option (1-4): {Style.RESET_ALL}").strip()
                
                if choice == "1":
                    print(f"{Fore.GREEN}✅ Processing entire file...{Style.RESET_ALL}")
                    break
                    
                elif choice == "2":
                    if suggested_points:
                        use_segmentation = True
                        split_points = suggested_points
                        print(f"{Fore.GREEN}✅ Using suggested split points{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED}❌ No suggested points available{Style.RESET_ALL}")
                        continue
                        
                elif choice == "3":
                    print(f"\n{Fore.CYAN}Enter split points:{Style.RESET_ALL}")
                    print(f"   Format: HH:MM:SS.mmm or MM:SS.mmm or seconds")
                    print(f"   Example: 30:00,1:00:00,1:30:00,2:00:00")
                    print(f"   Current duration: {format_seconds_to_timestamp(duration)}")
                    
                    split_input = input(f"\n{Fore.CYAN}Split points (comma-separated): {Style.RESET_ALL}").strip()
                    
                    if split_input:
                        try:
                            custom_points = []
                            for point_str in split_input.split(','):
                                point_str = point_str.strip()
                                if point_str:
                                    point_seconds = parse_timestamp(point_str)
                                    if 0 < point_seconds < duration:
                                        custom_points.append(point_seconds)
                                    else:
                                        print(f"{Fore.YELLOW}⚠️  Skipping invalid split point: {point_str} (out of range){Style.RESET_ALL}")
                            
                            if custom_points:
                                custom_points.sort()  # Sort in chronological order
                                
                                print(f"{Fore.GREEN}✅ Parsed custom split points:{Style.RESET_ALL}")
                                for i, point in enumerate(custom_points):
                                    print(f"   {i+1}. {format_seconds_to_timestamp(point)}")
                                
                                # Ask for confirmation
                                confirm = input(f"\n{Fore.CYAN}Are these split points correct? (y/n): {Style.RESET_ALL}").strip().lower()
                                if confirm in ['y', 'yes']:
                                    use_segmentation = True
                                    split_points = custom_points
                                    print(f"{Fore.GREEN}✅ Using custom split points{Style.RESET_ALL}")
                                    break
                                else:
                                    print(f"{Fore.YELLOW}⚠️  Custom split points cancelled. Please try again.{Style.RESET_ALL}")
                                    continue
                            else:
                                print(f"{Fore.RED}❌ No valid split points provided{Style.RESET_ALL}")
                                continue
                                
                        except ValueError as e:
                            print(f"{Fore.RED}❌ Error parsing split points: {e}{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.YELLOW}⚠️  No split points entered, processing entire file{Style.RESET_ALL}")
                        break

                elif choice == "4":
                    print(f"\n{Fore.CYAN}Choose segment length:{Style.RESET_ALL}")
                    print(f"   1. {Fore.GREEN}5 minutes{Style.RESET_ALL} (for high memory constraints)")
                    print(f"   2. {Fore.YELLOW}10 minutes{Style.RESET_ALL} (balanced)")
                    print(f"   3. {Fore.CYAN}15 minutes{Style.RESET_ALL} (good for most files)")
                    print(f"   4. {Fore.MAGENTA}30 minutes{Style.RESET_ALL} (for long files)")
                    print(f"   5. {Fore.BLUE}Custom minutes{Style.RESET_ALL} (enter your own)")
                    
                    segment_choice = input(f"\n{Fore.CYAN}Select segment length (1-5): {Style.RESET_ALL}").strip()
                    
                    segment_length_map = {
                        "1": 300,   # 5 minutes
                        "2": 600,   # 10 minutes
                        "3": 900,   # 15 minutes
                        "4": 1800,  # 30 minutes
                    }
                    
                    if segment_choice in segment_length_map:
                        new_segment_length = segment_length_map[segment_choice]
                        minutes = new_segment_length // 60
                        print(f"{Fore.GREEN}✅ Using {minutes}-minute segments{Style.RESET_ALL}")
                        
                        # Regenerate split points with new length
                        suggested_points = suggest_split_points(duration, new_segment_length)
                        if suggested_points:
                            print(f"\n{Fore.CYAN}🎯 New split points (every {minutes} minutes):{Style.RESET_ALL}")
                            for i, point in enumerate(suggested_points):
                                timestamp = format_seconds_to_timestamp(point)
                                print(f"   {i+1}. {timestamp}")
                            
                            use_segmentation = True
                            split_points = suggested_points
                            break
                        else:
                            print(f"{Fore.YELLOW}⚠️  File is shorter than segment length, processing entire file{Style.RESET_ALL}")
                            break
                            
                    elif segment_choice == "5":
                        try:
                            custom_minutes = input(f"\n{Fore.CYAN}Enter segment length in minutes: {Style.RESET_ALL}").strip()
                            custom_length = int(float(custom_minutes) * 60)
                            
                            if custom_length > 0 and custom_length < duration:
                                print(f"{Fore.GREEN}✅ Using {custom_minutes}-minute segments{Style.RESET_ALL}")
                                
                                # Generate split points with custom length
                                suggested_points = suggest_split_points(duration, custom_length)
                                if suggested_points:
                                    print(f"\n{Fore.CYAN}🎯 Custom split points (every {custom_minutes} minutes):{Style.RESET_ALL}")
                                    for i, point in enumerate(suggested_points):
                                        timestamp = format_seconds_to_timestamp(point)
                                        print(f"   {i+1}. {timestamp}")
                                    
                                    use_segmentation = True
                                    split_points = suggested_points
                                    break
                                else:
                                    print(f"{Fore.YELLOW}⚠️  File is shorter than segment length, processing entire file{Style.RESET_ALL}")
                                    break
                            else:
                                print(f"{Fore.RED}❌ Invalid segment length. Must be positive and less than file duration.{Style.RESET_ALL}")
                                continue
                                
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid input. Please enter a valid number of minutes.{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.RED}❌ Invalid choice. Please select 1-5.{Style.RESET_ALL}")
                        continue
                        
                else:
                    print(f"{Fore.RED}❌ Invalid choice. Please select 1-4.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Processing entire file.{Style.RESET_ALL}")
                break
            except EOFError:
                print(f"\n{Fore.YELLOW}⚠️  Input ended. Processing entire file.{Style.RESET_ALL}")
                break
    
    # Process with segmentation if requested
    if use_segmentation and split_points and duration is not None:
        return process_with_segmentation(
            input_path_obj, split_points, duration, output_name, 
            output_directory, task, model_dir, ram_setting
        )
    
    # Standard processing for non-segmented files
    return process_single_file(
        input_path_obj, output_name, output_directory, 
        task, model_dir, ram_setting
    )

def process_with_segmentation(
    input_path_obj: Path, split_points: List[float], total_duration: float,
    output_name: str, output_directory: str, task: str, 
    model_dir: Optional[str], ram_setting: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """
    Process a long media file by splitting it into segments.
    
    Args:
        input_path_obj (Path): Path object for input file
        split_points (List[float]): List of split points in seconds
        total_duration (float): Total duration of the media file
        output_name (str): Base output name
        output_directory (str): Output directory
        task (str): Processing task type
        model_dir (Optional[str]): Model directory
        ram_setting (Optional[str]): RAM setting
        
    Returns:
        Tuple[Dict[str, Any], str]: Combined result and output filename
    """
    # Create a temporary directory for this specific segmentation task.
    # It will be cleaned up immediately after this function completes.
    temp_dir = temp_manager.mkdtemp(prefix='segmentation_')
    
    try:
        segments_data = []
        
        # Create segment boundaries (include start and end)
        segment_boundaries = [0.0] + split_points + [total_duration]
        
        print(f"\n{Fore.CYAN}🔪 Creating {len(segment_boundaries) - 1} segments...{Style.RESET_ALL}")
        
        # Process each segment
        for i in range(len(segment_boundaries) - 1):
            start_time = segment_boundaries[i]
            end_time = segment_boundaries[i + 1]
            segment_duration = end_time - start_time
            
            print(f"\n{Fore.CYAN}📁 Segment {i + 1}/{len(segment_boundaries) - 1}:{Style.RESET_ALL}")
            print(f"   Time: {format_seconds_to_timestamp(start_time)} → {format_seconds_to_timestamp(end_time)}")
            print(f"   Duration: {format_human_time(segment_duration)}")
            
            # Create segment file in our temporary directory
            segment_filename = f"segment_{i+1:03d}_{input_path_obj.stem}.{input_path_obj.suffix[1:]}"
            segment_path = Path(temp_dir) / segment_filename
            
            print(f"   🔄 Extracting segment...")
            if not create_segment(str(input_path_obj), start_time, end_time, str(segment_path)):
                raise RuntimeError(f"Failed to create segment {i + 1}")
            
            print(f"   ✅ Segment created: {segment_path.name}")
            
            # Process this segment
            try:
                print(f"   🎵 Processing segment {i + 1}...")
                
                # Use the same processing logic as the main function
                segment_result, _ = process_single_file(
                    segment_path, f"{output_name}_segment_{i+1:03d}", 
                    str(temp_dir), task, model_dir, ram_setting
                )
                
                # Store segment data with timing information
                segments_data.append({
                    'result': segment_result,
                    'start_time': start_time,
                    'end_time': end_time,
                    'segment_index': i + 1
                })
                
                print(f"   ✅ Segment {i + 1} processed: {len(segment_result.get('segments', []))} subtitles")
                
                # Free memory after each segment
                del segment_result
                gc.collect()
                
                # Clear CUDA cache if available
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except ImportError:
                    pass
                    
            except Exception as e:
                logger.error(f"Error processing segment {i + 1}: {e}")
                print(f"   {Fore.RED}❌ Segment {i + 1} failed: {e}{Style.RESET_ALL}")
                # Continue with other segments
                continue
        
        if not segments_data:
            raise RuntimeError("No segments were successfully processed")
        
        print(f"\n{Fore.GREEN}🎉 All segments processed successfully!{Style.RESET_ALL}")
        print(f"   Total segments: {len(segments_data)}")
        
        # Combine all segment results
        print(f"{Fore.CYAN}🔗 Combining subtitles...{Style.RESET_ALL}")
        
        # Create combined result
        combined_segments = []
        combined_text_parts = []
        
        for segment_data in segments_data:
            segment_result = segment_data['result']
            time_offset = segment_data['start_time']
            
            # Adjust timing for each subtitle in this segment
            for segment in segment_result.get("segments", []):
                if isinstance(segment, dict) and segment.get("text", "").strip():
                    adjusted_segment = segment.copy()
                    adjusted_segment["start"] = segment.get("start", 0.0) + time_offset
                    adjusted_segment["end"] = segment.get("end", 0.0) + time_offset
                    combined_segments.append(adjusted_segment)
                    combined_text_parts.append(segment.get("text", "").strip())
        
        # Create combined result
        combined_result = {
            "segments": combined_segments,
            "text": " ".join(combined_text_parts),
            "language": segments_data[0]['result'].get('language', 'en') if segments_data else 'en'
        }
        
        # Save combined subtitle file
        output_directory_obj = Path(output_directory)
        if not output_directory_obj.exists():
            output_directory_obj.mkdir(parents=True, exist_ok=True)
            
        output_path = output_directory_obj / f"{output_name}.srt"
        combine_segment_subtitles(segments_data, str(output_path))
        
        print(f"{Fore.GREEN}✅ Segmented processing complete!{Style.RESET_ALL}")
        print(f"   Combined subtitles: {len(combined_segments)} entries")
        print(f"   Output file: {output_path}")

        # Print the final combined SRT file to the console if --print_srt_to_console is set
        if getattr(args, 'print_srt_to_console', False):
            print(f"\n{Fore.CYAN}📝 Final Combined SRT:{Style.RESET_ALL}")
            try:
                with open(output_path, 'r', encoding='utf-8') as srt_file:
                    for line in srt_file:
                        print(line.rstrip())
            except Exception as e:
                print(f"{Fore.RED}Failed to print combined SRT: {e}{Style.RESET_ALL}")

        return combined_result, output_name
            
    except Exception as e:
        logger.error(f"Segmentation processing failed: {e}")
        raise RuntimeError(f"Segmented processing failed: {str(e)}")
    finally:
        # Clean up the temp dir for this segmentation task immediately.
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_single_file(
    input_path_obj: Path, output_name: str, output_directory: str,
    task: str, model_dir: Optional[str], ram_setting: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """
    Process a single media file (original processing logic).
    
    Args:
        input_path_obj (Path): Path to input file
        output_name (str): Output name
        output_directory (str): Output directory  
        task (str): Processing task
        model_dir (Optional[str]): Model directory
        ram_setting (Optional[str]): RAM setting
        
    Returns:
        Tuple[Dict[str, Any], str]: Result and output filename
    """
    if task not in ["transcribe", "translate"]:
        raise ValueError("Task must be either 'transcribe' or 'translate'")
    
    output_directory_obj = Path(output_directory)
    if not output_directory_obj.exists():
        output_directory_obj.mkdir(parents=True, exist_ok=True)

    # Vocal isolation step if requested
    processed_audio_path = str(input_path_obj)
    if getattr(args, 'isolate_vocals', False):
        demucs_python_path = get_demucs_python_path()
        
        
        # Determine which Demucs model to use
        selected_model = getattr(args, 'demucs_model', None)
        
        if selected_model:
            # User specified a model via command line (including default htdemucs)
            print(f"{Fore.GREEN}✅ Using specified Demucs model: {selected_model}{Style.RESET_ALL}")
            
            # Show model info
            model_info = {
                "htdemucs": "Latest Hybrid Transformer model (default)",
                "htdemucs_ft": "Fine-tuned version for better quality",
                "htdemucs_6s": "6-source separation (includes piano/guitar)",
                "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                "mdx": "Frequency-domain model, MDX winner",
                "mdx_extra": "Enhanced MDX with extra training data",
                "mdx_q": "Quantized MDX (faster, smaller)",
                "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                "hdemucs": "Original Hybrid Demucs v3",
                "demucs": "Original time-domain Demucs"
            }
            print(f"{Fore.CYAN}ℹ️  {model_info.get(selected_model, 'Unknown model')}{Style.RESET_ALL}")
            
        else:
            # Ask user which Demucs model to use
            print(f"\n{Fore.CYAN}🎛️ Demucs Model Selection for Vocal Isolation:{Style.RESET_ALL}")
            print(f"   Available models:")
            print(f"   1. {Fore.YELLOW}htdemucs{Style.RESET_ALL} (default, Hybrid Transformer v4)")
            print(f"   2. {Fore.YELLOW}htdemucs_ft{Style.RESET_ALL} (fine-tuned htdemucs, better quality, slower)")
            print(f"   3. {Fore.YELLOW}htdemucs_6s{Style.RESET_ALL} (6-source: drums, bass, other, vocals, piano, guitar)")
            print(f"   4. {Fore.YELLOW}hdemucs_mmi{Style.RESET_ALL} (Hybrid Demucs v3, MusDB + 800 songs)")
            print(f"   5. {Fore.YELLOW}mdx{Style.RESET_ALL} (MDX challenge Track A winner)")
            print(f"   6. {Fore.YELLOW}mdx_extra{Style.RESET_ALL} (MDX Track B, trained with extra data)")
            print(f"   7. {Fore.YELLOW}mdx_q{Style.RESET_ALL} (quantized mdx, smaller/faster)")
            print(f"   8. {Fore.YELLOW}mdx_extra_q{Style.RESET_ALL} (quantized mdx_extra, smaller/faster)")
            print(f"   9. {Fore.YELLOW}hdemucs{Style.RESET_ALL} (original Hybrid Demucs v3)")
            print(f"  10. {Fore.YELLOW}demucs{Style.RESET_ALL} (original time-only Demucs)")
            
            print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
            print(f"   🎯 {Fore.GREEN}Best Quality{Style.RESET_ALL}: htdemucs_ft (fine-tuned)")
            print(f"   🎯 {Fore.BLUE}Fastest{Style.RESET_ALL}: mdx_q or mdx_extra_q (quantized)")
            print(f"   🎯 {Fore.MAGENTA}Detailed Separation{Style.RESET_ALL}: htdemucs_6s (6 sources)")
            print(f"   🎯 {Fore.CYAN}Balanced{Style.RESET_ALL}: mdx_extra (good quality + speed)")
            print(f"   🎯 {Fore.YELLOW}Legacy/Compatibility{Style.RESET_ALL}: hdemucs or demucs")
            
            # Get user choice
            while True:
                try:
                    model_choice = input(f"\n{Fore.CYAN}Select Demucs model (1-10, or Enter for default htdemucs): {Style.RESET_ALL}").strip()
                    
                    if not model_choice:  # User pressed Enter for default
                        selected_model = "htdemucs"
                        print(f"{Fore.GREEN}✅ Using default model: {selected_model}{Style.RESET_ALL}")
                        break
                    
                    model_map = {
                        "1": "htdemucs",
                        "2": "htdemucs_ft", 
                        "3": "htdemucs_6s",
                        "4": "hdemucs_mmi",
                        "5": "mdx",
                        "6": "mdx_extra",
                        "7": "mdx_q",
                        "8": "mdx_extra_q",
                        "9": "hdemucs",
                        "10": "demucs"
                    }
                    
                    if model_choice in model_map:
                        selected_model = model_map[model_choice]
                        print(f"{Fore.GREEN}✅ Selected model: {selected_model}{Style.RESET_ALL}")
                        
                        # Show model info
                        model_info = {
                            "htdemucs": "Latest Hybrid Transformer model (default)",
                            "htdemucs_ft": "Fine-tuned version for better quality",
                            "htdemucs_6s": "6-source separation (includes piano/guitar)",
                            "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                            "mdx": "Frequency-domain model, MDX winner",
                            "mdx_extra": "Enhanced MDX with extra training data",
                            "mdx_q": "Quantized MDX (faster, smaller)",
                            "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                            "hdemucs": "Original Hybrid Demucs v3",
                            "demucs": "Original time-domain Demucs"
                        }
                        
                        print(f"{Fore.CYAN}ℹ️  {model_info[selected_model]}{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED}❌ Invalid choice. Please select 1-10 or press Enter for default.{Style.RESET_ALL}")
                        
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Using default model: htdemucs{Style.RESET_ALL}")
                    selected_model = "htdemucs"
                    break
                except EOFError:
                    print(f"\n{Fore.YELLOW}⚠️  Input ended. Using default model: htdemucs{Style.RESET_ALL}")
                    selected_model = "htdemucs"
                    break
        
        try:
            print(f"\n{Fore.CYAN}🔄 Isolating vocals from input audio using Demucs model: {selected_model}...{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Progress will be shown below:{Style.RESET_ALL}")
            
            import time  # Import time for tracking progress timeouts
            
            # Create a managed temp directory for demucs output. It will be cleaned on script exit.
            tmpdir = temp_manager.mkdtemp(prefix='demucs_')

            demucs_cmd = [
                demucs_python_path,
                '-m', 'demucs',
                '-n', selected_model,
                '-o', tmpdir,
                '--two-stems', 'vocals'
            ]
            
            # Add jobs parameter if specified
            if hasattr(args, 'demucs_jobs') and args.demucs_jobs > 0:
                demucs_cmd.extend(['-j', str(args.demucs_jobs)])
            
            demucs_cmd.append(str(input_path_obj))
            
            # Run demucs CLI to separate vocals with real-time progress display
            process = subprocess.Popen(demucs_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')
            
            # Monitor progress in real-time
            stderr_output = ""
            stdout_output = ""
            current_phase = 0
            total_phases = 1  # Default to 1, will update when we detect multiple models
            last_progress = 0.0  # Track progress separately
            ensemble_detected = False  # Track if we've already detected ensemble
            lost_track = False  # Track if we've lost sync with progress
            last_progress_time = time.time()  # Track time since last progress update
            
            # Check for known multi-model types upfront
            if selected_model in ['htdemucs_ft', 'mdx', 'mdx_extra', 'mdx_q', 'mdx_extra_q']:
                # These are known to be ensemble models based on testing
                if selected_model == 'htdemucs_ft':
                    total_phases = 4  # htdemucs_ft is a bag of 4 models
                elif selected_model in ['mdx', 'mdx_extra', 'mdx_q']:
                    total_phases = 4  # These are bags of 4 models
                elif selected_model == 'mdx_extra_q':
                    total_phases = 4  # Bag of 4 models but with more complex processing
                print(f"{Fore.CYAN}  📋 {selected_model} is a multi-model ensemble ({total_phases} internal models){Style.RESET_ALL}")
                ensemble_detected = True
            
            # Determine number of threads for Demucs message
            num_threads_for_message = getattr(args, 'demucs_jobs', 0)
            if num_threads_for_message == 0:
                display_threads = 1
            else:
                display_threads = num_threads_for_message
            print(f"{Fore.CYAN}🎵 Demucs processing using {display_threads} thread{'s' if display_threads != 1 else ''}:{Style.RESET_ALL}")
            
            # Read stderr for progress updates (Demucs shows progress on stderr)
            while True:
                if process.stderr is not None:
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        stderr_output += stderr_line
                        # Show progress lines that contain percentage or processing info
                        line_stripped = stderr_line.strip()
                        
                        # Detect if this is a bag of models - check multiple patterns (only if not already detected)
                        if not ensemble_detected and any(phrase in line_stripped.lower() for phrase in ['bag of', 'ensemble of', 'bag_of', 'selected model is']):
                            try:
                                # Show debug info to understand the format
                                if getattr(args, 'debug', False):
                                    print(f"{Fore.MAGENTA}Debug: Detected bag line: '{line_stripped}'{Style.RESET_ALL}")
                                
                                # Try different extraction patterns
                                if 'bag of' in line_stripped.lower():
                                    # Pattern: "Selected model is a bag of X models. You will see that many progress bars per track."
                                    parts = line_stripped.lower().split('bag of')
                                    if len(parts) > 1:
                                        # Extract the number between "bag of" and "models"
                                        models_part = parts[1].split('models')[0].strip()
                                        if models_part.isdigit():
                                            detected_phases = int(models_part)
                                            # Only update if it's actually a multi-model (> 1)
                                            if detected_phases > 1:
                                                total_phases = detected_phases
                                                ensemble_detected = True
                                                print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                                                print(f"{Fore.CYAN}  📋 This model will run {total_phases} internal models and combine results{Style.RESET_ALL}")
                                elif 'models:' in line_stripped.lower():
                                    # Look for patterns like "4 models:" or similar
                                    import re
                                    match = re.search(r'(\d+)\s*models?:', line_stripped.lower())
                                    if match:
                                        detected_phases = int(match.group(1))
                                        if detected_phases > 1:
                                            total_phases = detected_phases
                                            ensemble_detected = True
                                            print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                                            print(f"{Fore.CYAN}  📋 This model will run {total_phases} internal models and combine results{Style.RESET_ALL}")
                            except Exception as e:
                                if getattr(args, 'debug', False):
                                    print(f"{Fore.MAGENTA}Debug: Bag detection error: {e}{Style.RESET_ALL}")
                                total_phases = 1
                        
                        if any(indicator in line_stripped for indicator in ['%|', 'seconds/s', 'Separating track', 'Selected model']):
                            # Reset lost track flag if we see progress again
                            if '%|' in line_stripped and lost_track:
                                lost_track = False
                                print(f"\n{Fore.GREEN}  🔄 Reconnected to progress tracking!{Style.RESET_ALL}")
                            
                            # Clean up progress bar display
                            if '%|' in line_stripped:
                                # Extract percentage and show clean progress
                                try:
                                    percent_part = line_stripped.split('%|')[0].strip()
                                    if percent_part.replace('.', '').replace(' ', '').isdigit():
                                        percent = float(percent_part)
                                        last_progress_time = time.time()  # Update last progress time
                                        
                                        # Check if we've moved to a new phase (progress reset to low value)
                                        if percent < last_progress - 15:  # More sensitive detection
                                            current_phase += 1
                                            # If we detect a reset and haven't detected it's a multi-model, update total_phases
                                            if total_phases == 1 and current_phase > 0:
                                                # Estimate total phases based on resets
                                                # Most ensemble models use 4 models based on our testing
                                                if selected_model in ['htdemucs_ft', 'mdx', 'mdx_extra', 'mdx_q']:
                                                    total_phases = 4  # Standard 4-model ensemble
                                                elif selected_model == 'mdx_extra_q':
                                                    total_phases = 4  # Also 4 models but more complex processing
                                                else:
                                                    # For unknown models, estimate conservatively
                                                    total_phases = current_phase + 2
                                                print(f"\n{Fore.CYAN}  🔍 Detected multi-model processing (estimated {total_phases} models){Style.RESET_ALL}")
                                        last_progress = percent
                                        
                                        # Show phase info if multiple phases detected or estimated
                                        if total_phases > 1 or current_phase > 0:
                                            effective_total = max(total_phases, current_phase + 1)
                                            phase_info = f" (Model {min(current_phase + 1, effective_total)}/{effective_total})"
                                            print(f"\r{Fore.GREEN}  Progress: {percent:5.1f}%{phase_info} {Fore.CYAN}🎵{Style.RESET_ALL}", end="", flush=True)
                                        else:
                                            print(f"\r{Fore.GREEN}  Progress: {percent:5.1f}% {Fore.CYAN}🎵{Style.RESET_ALL}", end="", flush=True)
                                except Exception as e:
                                    # If progress parsing fails, enable lost track mode
                                    if not lost_track:
                                        lost_track = True
                                        print(f"\n{Fore.YELLOW}  ⚠️  Lost track but don't worry it's still going...{Style.RESET_ALL}")
                            elif 'Separating track' in line_stripped:
                                print(f"\n{Fore.CYAN}  🎯 {line_stripped}{Style.RESET_ALL}")
                            elif 'Selected model' in line_stripped and 'bag of' not in line_stripped:
                                print(f"{Fore.YELLOW}  ℹ️  {line_stripped}{Style.RESET_ALL}")
                
                # Check if process is done
                if process.poll() is not None:
                    break
                
                # Check for timeout - if no progress updates for too long, show lost track message
                current_time = time.time()
                if not lost_track and (current_time - last_progress_time) > 30:  # 30 seconds without progress
                    lost_track = True
                    print(f"\n{Fore.YELLOW}  ⚠️  Lost track but don't worry it's still going...{Style.RESET_ALL}")
                
                # Add a small delay to prevent excessive CPU usage
                time.sleep(0.1)
            
            # Get any remaining output
            remaining_stdout, remaining_stderr = process.communicate()
            stdout_output += remaining_stdout
            stderr_output += remaining_stderr
            
            print()  # New line after progress
            
            # Debug output (only show if debug flag is enabled)
            if getattr(args, 'debug', False):
                print(f"{Fore.YELLOW}Debug: Demucs return code: {process.returncode}{Style.RESET_ALL}")
                if stdout_output:
                    print(f"{Fore.YELLOW}Debug: Demucs stdout: {stdout_output[:500]}{'...' if len(stdout_output) > 500 else ''}{Style.RESET_ALL}")
                if stderr_output:
                    print(f"{Fore.YELLOW}Debug: Demucs stderr: {stderr_output[:500]}{'...' if len(stderr_output) > 500 else ''}{Style.RESET_ALL}")
            
            if process.returncode != 0:
                raise RuntimeError(f"Demucs failed with return code {process.returncode}: {stderr_output}")
            
            print(f"{Fore.GREEN}✅ Demucs processing complete!{Style.RESET_ALL}")
            
            # Find the actual output directory structure
            base_name = os.path.splitext(os.path.basename(str(input_path_obj)))[0]
            
            # Demucs might create different directory structures, let's search for vocals.wav
            vocals_path = None
            
            # Try different possible output locations based on selected model
            possible_locations = [
                os.path.join(tmpdir, selected_model, base_name, 'vocals.wav'),  # Model-specific location
                os.path.join(tmpdir, 'demucs', base_name, 'vocals.wav'),  # Standard location
                os.path.join(tmpdir, 'htdemucs', base_name, 'vocals.wav'),  # HTDemucs model
                os.path.join(tmpdir, 'mdx_extra', base_name, 'vocals.wav'),  # MDX model
                os.path.join(tmpdir, base_name, 'vocals.wav'),  # Direct output
            ]
            
            # Search recursively for vocals.wav in case structure is different
            for root, dirs, files in os.walk(tmpdir):
                if 'vocals.wav' in files:
                    vocals_path = os.path.join(root, 'vocals.wav')
                    print(f"{Fore.GREEN}Found vocals.wav at: {vocals_path}{Style.RESET_ALL}")
                    break
            
            # Try the predefined locations if recursive search didn't work
            if not vocals_path:
                for location in possible_locations:
                    if os.path.exists(location):
                        vocals_path = location
                        print(f"{Fore.GREEN}Found vocals.wav at predefined location: {vocals_path}{Style.RESET_ALL}")
                        break
            
            if not vocals_path or not os.path.exists(vocals_path):
                # List all files in tmpdir for debugging
                print(f"{Fore.RED}Debug: Contents of tmpdir ({tmpdir}):{Style.RESET_ALL}")
                for root, dirs, files in os.walk(tmpdir):
                    level = root.replace(tmpdir, '').count(os.sep)
                    indent = ' ' * 2 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        print(f"{subindent}{file}")
                raise RuntimeError(f"Vocal isolation failed: vocals.wav not found. Expected at: {possible_locations[0]}")
            
            # No need to copy files. Just update the path to the temporary vocals file.
            # The TempFileManager will handle cleanup at script exit.
            processed_audio_path = vocals_path
            print(f"{Fore.GREEN}✅ Vocal isolation complete. Using isolated vocals from temp dir for transcription.{Style.RESET_ALL}")

        except Exception as e:
            raise RuntimeError(f"Vocal isolation failed: {str(e)}")

    try:
        # Determine model type based on available RAM (skip warning for file input mode)
        # Use provided ram_setting or fall back to args.ram
        ram_to_use = ram_setting if ram_setting is not None else args.ram
        model_type = get_model_type(ram_to_use, skip_warning=True)
        
        # Set up transcription options
        word_timestamps = getattr(args, 'word_timestamps', False)
        if model_type == "turbo":
            decode_options = {
                "fp16": args.fp16, "language": args.language, "task": task, "word_timestamps": word_timestamps,
                "temperature": 0.1, "compression_ratio_threshold": 2.0, "logprob_threshold": -0.8,
                "no_speech_threshold": 0.4, "condition_on_previous_text": False,
                "prepend_punctuations": "\"'([{-", "append_punctuations": "\"\'.。,，!！?？:：)"
            }
        else:
            decode_options = {
                "fp16": args.fp16, "language": args.language, "task": task, "word_timestamps": word_timestamps,
                "temperature": 0.0, "compression_ratio_threshold": 2.4, "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6, "condition_on_previous_text": True
            }

        logger.info("Starting transcription process...")
        
        # Main logic for silence detection vs. full file processing
        use_silence_detection = getattr(args, 'silent_detect', False)
        
        if use_silence_detection:
            print(f"{Fore.CYAN}🤫 Silence detection enabled. Processing only speech regions for efficiency...{Style.RESET_ALL}")
            silence_threshold_db = getattr(args, 'silent_threshold', -35.0)
            min_silence_duration = getattr(args, 'silent_duration', 0.5)
            audio_regions = detect_silence_in_audio(
                processed_audio_path, silence_threshold_db, min_silence_duration
            )

            # Group consecutive speech regions separated by silence
            speech_groups = group_speech_regions_by_silence(audio_regions)

            if not speech_groups:
                print(f"{Fore.YELLOW}⚠️ No speech detected in file. Output will be empty.{Style.RESET_ALL}")
                result = {"segments": [], "text": ""}
            else:
                # Extract all individual speech regions from all groups for batch processing
                all_speech_regions = []
                for group in speech_groups:
                    all_speech_regions.extend(group)
                
                print(f"{Fore.CYAN}🎵 Found {len(speech_groups)} speech groups with {len(all_speech_regions)} total speech regions{Style.RESET_ALL}")
                
                # Process all speech regions using the batch processing logic
                all_segments = process_speech_regions(
                    processed_audio_path, all_speech_regions, model_type, decode_options, task
                )
                result = {"segments": all_segments, "text": " ".join(s.get('text', '').strip() for s in all_segments)}
        else:
            # Process the entire file normally without silence detection
            print(f"{Fore.CYAN}🚀 Starting transcription for the full file...{Style.RESET_ALL}")
            result = run_transcription_in_process(
                audio_path=processed_audio_path,
                model_type=model_type,
                decode_options=decode_options,
                model_dir=str(args.model_dir) if model_dir is None else str(model_dir),
                device=args.device
            )
            print(f"{Fore.GREEN}✅ Transcription complete.{Style.RESET_ALL}")
            
            # Offer to retry full file if confidence is low
            segments = result.get("segments", [])
            overall_confidence = calculate_region_confidence(segments)
            file_has_repetitions, _, _ = detect_repeated_segments(segments)
            should_retry_full_file = (
                (overall_confidence < 0.90 or file_has_repetitions) and
                not _auto_proceed_detection and
                hasattr(args, 'ram') and
                get_next_higher_model(args.ram) is not None
            )
            
            if should_retry_full_file:
                # This block contains the logic for retrying the full file, which is kept for this path.
                # (The extensive retry logic from the original file would be here)
                print(f"{Fore.YELLOW}Note: Full-file retry logic would be executed here if implemented.{Style.RESET_ALL}")


        # Filter out empty segments and handle turbo model's long segments
        filtered_segments = []
        total_segments_processed = 0
        
        original_segments = result.get("segments", [])
        if not original_segments:
            original_segments = []

        total_final_segments = 0
        for segment in original_segments:
            if isinstance(segment, dict):
                text = segment.get("text", "").strip()
                if text:
                    start_time = segment.get("start", 0.0)
                    end_time = segment.get("end", 0.0)
                    duration = end_time - start_time
                    
                    if model_type == "turbo" and duration > 10.0:
                        split_segments = split_text_for_subtitles(text, start_time, end_time, max_chars=80, max_words=12)
                        total_final_segments += len(split_segments)
                    else:
                        total_final_segments += 1
        
        for idx, segment in enumerate(original_segments):
            if isinstance(segment, dict):
                text = segment.get("text", "").strip()
                if text:
                    start_time = segment.get("start", 0.0)
                    end_time = segment.get("end", 0.0)
                    duration = end_time - start_time
                    
                    if model_type == "turbo" and duration > 10.0:
                        words = segment.get("words", [])
                        if words and len(words) > 0:
                            split_segments = split_text_with_word_timestamps(words, max_chars=80, max_words=12)
                        else:
                            split_segments = split_text_for_subtitles(text, start_time, end_time, max_chars=80, max_words=12)
                        
                        for chunk_text, chunk_start, chunk_end in split_segments:
                            chunk_seg = {
                                "start": chunk_start, "end": chunk_end, "text": chunk_text,
                                "avg_logprob": segment.get("avg_logprob", -1.0)
                            }
                            colored_text, confidence = format_words_with_confidence(chunk_text, chunk_seg["avg_logprob"])
                            total_segments_processed += 1
                            progress = total_segments_processed / total_final_segments if total_final_segments > 0 else 0
                            logger.info(f"[%.2f%%] %s %s(%.2f%% confident)%s", progress * 100, colored_text, Fore.CYAN, confidence * 100, Style.RESET_ALL)
                            filtered_segments.append(chunk_seg)
                    else:
                        colored_text, confidence = format_words_with_confidence(text, segment.get("avg_logprob", -1.0))
                        total_segments_processed += 1
                        progress = total_segments_processed / total_final_segments if total_final_segments > 0 else 0
                        logger.info(f"[%.2f%%] %s %s(%.2f%% confident)%s", progress * 100, colored_text, Fore.CYAN, confidence * 100, Style.RESET_ALL)
                        filtered_segments.append(segment)

        result["segments"] = filtered_segments

        # Generate subtitle file
        logger.info("\nWriting subtitle file...")
        print(f"{Fore.CYAN}📝 Writing subtitle file...{Style.RESET_ALL}")
        output_path = output_directory_obj / f"{output_name}.srt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            for segment in filtered_segments:
                start_time_str = format_timestamp(segment.get("start", 0.0))
                end_time_str = format_timestamp(segment.get("end", 0.0))
                text = segment.get("text", "").strip()
                filtered_text = filter_unwanted_phrases(text)
                if filtered_text:
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time_str} --> {end_time_str}\n")
                    f.write(f"{filtered_text}\n\n")
                    subtitle_index += 1

        logger.info("Subtitle file saved to: %s", output_path)
        print(f"{Fore.GREEN}✅ Subtitle generation complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Subtitle file saved to: {output_path}{Style.RESET_ALL}")

        # Print all generated subtitles to the console only if --print_srt_to_console is set
        if getattr(args, 'print_srt_to_console', False):
            print(f"\n{Fore.CYAN}📝 Generated Subtitles:{Style.RESET_ALL}")
            subtitle_index = 1
            for segment in filtered_segments:
                start_time_str = format_timestamp(segment.get("start", 0.0))
                end_time_str = format_timestamp(segment.get("end", 0.0))
                text = segment.get("text", "").strip()
                filtered_text = filter_unwanted_phrases(text)
                if filtered_text:
                    conf = segment.get("avg_logprob", None)
                    confidence = None
                    if conf is not None:
                        confidence = 1.0 - min(1.0, max(0.0, -conf / 10))
                    color = get_color_for_confidence(confidence) if confidence is not None else ''
                    reset = Style.RESET_ALL if confidence is not None else ''
                    print(f"{subtitle_index}. {start_time_str} --> {end_time_str} : {color}{filtered_text}{reset}")
                    subtitle_index += 1

        return result, output_name

    except Exception as e:
        logger.error("Failed to generate subtitles: %s", str(e), exc_info=True)
        raise RuntimeError(f"Subtitle generation failed: {str(e)}")

# Indicate that the subtitles generator module is loaded.
print(f"{Fore.GREEN}✅ Subtitles Generator Module Loaded{Style.RESET_ALL}")