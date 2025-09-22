"""
Stream Transcription Module

This module handles real-time transcription and translation of HLS audio streams.
It provides functionality to:
- Download and process HLS stream segments
- Transcribe audio in original language
- Translate audio to English
- Send transcriptions/translations via Discord webhooks or API
- Support for authenticated streams via cookies or stream keys

The module uses a threaded approach to handle concurrent downloading and processing
of audio segments, with support for retry logic and error handling.
"""


import threading
import queue
import time
import requests
import hashlib
import os
from modules.demucs_path_helper import get_demucs_python_path
import m3u8
import http.client
import http.cookiejar
import whisper
from modules import parser_args
import subprocess
import shutil
import tempfile
from modules.discord import send_to_discord_webhook, send_transcription_to_discord
from modules import api_backend
import difflib
from modules.similarity_utils import is_similar
from collections import deque
from colorama import Fore, Back, Style, init
from urllib.parse import urlparse
from modules.rate_limiter import global_rate_limiter
from modules.file_handlers import is_phrase_in_blocklist, add_phrase_to_blocklist

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Console formatting helper functions
def print_styled_header(title, color=Fore.CYAN, width=80):
    """Print a styled header with border."""
    border = "═" * (width - 4)
    print(f"{color}╔{border}╗")
    padding = (width - len(title) - 4) // 2
    left_pad = " " * padding
    right_pad = " " * (width - len(title) - 4 - padding)
    print(f"{color}║ {Style.BRIGHT}{title}{Style.RESET_ALL}{color}{left_pad}{right_pad} ║")
    print(f"{color}╚{border}╝{Style.RESET_ALL}")

def print_transcription_result(language, content, result_type="Original"):
    """Print transcription results with beautiful formatting."""
    import textwrap
    
    if result_type == "Original":
        color = Fore.GREEN
        title = f"{language} {result_type}"
    elif result_type == "Translation":
        color = Fore.BLUE
        title = f"EN {result_type}"
    elif result_type == "Transcription":
        color = Fore.MAGENTA
        title = f"{language} {result_type}"
    else:
        color = Fore.YELLOW
        title = result_type

    # Set maximum width for readability (80 characters is optimal for reading)
    max_width = 80
    min_width = 50
    
    # Calculate width based on title and content, but cap at max_width
    title_width = len(title) + 4
    content_width = len(content) + 4
    box_width = max(min_width, min(max_width, title_width, content_width))
    
    # If content is longer than box width, we'll wrap it
    content_area_width = box_width - 4  # Account for borders and padding
    
    # Wrap content to fit within the box
    wrapped_lines = textwrap.wrap(content.strip(), width=content_area_width)
    if not wrapped_lines:  # Handle empty content
        wrapped_lines = [""]
    
    title_padding = box_width - len(title) - 4

    # Print the box
    print(f"\n{color}┌{'─' * box_width}┐")
    print(f"│ {Style.BRIGHT}{title:<{title_padding}}{Style.RESET_ALL}{color} │")
    print(f"├{'─' * box_width}┤")
    
    # Print each wrapped line
    for line in wrapped_lines:
        print(f"│ {Style.RESET_ALL}{line:<{content_area_width}}{color} │")
    
    print(f"└{'─' * box_width}┘{Style.RESET_ALL}\n")

def print_info_message(message):
    """Print an info message with styling."""
    print(f"{Fore.CYAN}{Style.BRIGHT}[INFO]{Style.RESET_ALL} {message}")

def print_warning_message(message):
    """Print a warning message with styling."""
    print(f"{Fore.YELLOW}{Style.BRIGHT}[WARNING]{Style.RESET_ALL} {message}")

def print_error_message(message):
    """Print an error message with styling."""
    print(f"{Fore.RED}{Style.BRIGHT}[ERROR]{Style.RESET_ALL} {message}")

def print_debug_message(message):
    """Print a debug message with styling."""
    print(f"{Fore.LIGHTBLACK_EX}{Style.DIM}[DEBUG]{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{message}{Style.RESET_ALL}")

def print_success_message(message):
    """Print a success message with styling."""
    print(f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} {message}")

def print_progress_message(message):
    """Print a progress message with styling."""
    print(f"{Fore.BLUE}{Style.BRIGHT}[PROGRESS]{Style.RESET_ALL} {message}")

# Global shutdown flag
shutdown_flag = False
args = parser_args.parse_arguments()
kill = False

# Toggle debug output for similar message blocking
DEBUG_BLOCK_SIMILAR = False  # Set to False to hide debug output

# Enable similar message protection if --condition_on_previous_text is used
ENABLE_SIMILAR_PROTECTION = args.condition_on_previous_text

# Set debug to true
# args.debug = True

# Semaphore for limiting concurrent downloads (adjust as needed)
max_concurrent_downloads = 4
download_semaphore = threading.Semaphore(max_concurrent_downloads)

# Track combined files in queue
combined_files_in_queue = []
MAX_COMBINED_FILES = 5

def check_and_clean_temp(temp_dir):
    """
    Check if temp directory has leftover files and ask user if they want to clean it.
    
    Args:
        temp_dir (str): Path to the temporary directory
        
    This function checks for any leftover files from improper program termination
    and offers to clean them, reminding users about proper shutdown procedure.
    """
    if not os.path.exists(temp_dir):
        return
        
    files = os.listdir(temp_dir)
    if files:
        print_warning_message("Leftover files found in temp directory.")
        print_info_message("This usually happens if the program didn't close properly.")
        print_info_message("Remember to use 'Ctrl+C' in the console to close the program properly.")
        user_input = input(f"\n{Fore.YELLOW}Would you like to clean the temp directory? (y/n): {Style.RESET_ALL}").lower()
        
        if user_input == 'y':
            print_progress_message("Cleaning temp directory...")
            cleaned_files = 0
            for file in files:
                try:
                    os.remove(os.path.join(temp_dir, file))
                    cleaned_files += 1
                except Exception as e:
                    print_error_message(f"Error removing {file}: {e}")
            print_success_message(f"Temp directory cleaned! Removed {cleaned_files} files.")
        else:
            print_info_message("Keeping existing temp files.")

def load_cookies_from_file(cookie_file_path):
    """
    Load cookies from a Mozilla format cookies file.

    Args:
        cookie_file_path (str): Path to the cookie file in Mozilla format

    Returns:
        http.cookiejar.MozillaCookieJar: Loaded cookie jar object containing the cookies

    This function is used for authenticated streams that require cookies for access.
    The cookies are loaded with both discarded and expired cookies included.
    """
    cookie_jar = http.cookiejar.MozillaCookieJar()
    cookie_jar.load(cookie_file_path, ignore_discard=True, ignore_expires=True)
    return cookie_jar



def start_stream_transcription(
    task_id,
    hls_url,
    model_name,
    temp_dir,
    segments_max,
    target_language,
    stream_language,
    tasktranslate_task,
    tasktranscribe_task,
    webhook_url,
    cookie_file_path=None,
    streamkey=None,
):
    """
    Start transcription and translation of an HLS audio stream.

    Args:
        task_id (str): Unique identifier for this transcription task
        hls_url (str): URL of the HLS stream to process
        model_name (object): Loaded Whisper model instance
        temp_dir (str): Directory path for temporary files
        segments_max (int): Maximum number of segments to process at once
        target_language (str): Target language code for transcription
        stream_language (str): Source language code of the stream
        tasktranslate_task (bool): Whether to translate to English
        tasktranscribe_task (bool): Whether to transcribe in target language
        webhook_url (str, optional): Discord webhook URL for sending results
        cookie_file_path (str, optional): Path to Mozilla format cookies file
        streamkey (str, optional): Authentication key for protected streams

    The function handles downloading stream segments, combining them into
    processable chunks, and running transcription/translation based on
    the specified tasks. It uses threading for concurrent processing and
    includes retry logic for robust operation.
    """

    # Check and clean temp directory before starting when using debug mode.
    if args.debug:
        check_and_clean_temp(temp_dir)
    
    if streamkey:
        keyid = args.remote_hls_password_id
        key = args.remote_hls_password
        params = {keyid: key}
    else:
        params = None

    global shutdown_flag
    audio_queue = queue.Queue()    # Load cookies if a cookie file path is provided
    cookies = None
    if cookie_file_path:
        cookies = load_cookies_from_file(cookie_file_path)
        
    def download_segment(
        segment_url, output_path, max_retries=3, retry_delay=0.5, segment_delay=0
    ):
        """
        Download an HLS segment with retry logic and error handling.

        Args:
            segment_url (str): URL of the segment to download
            output_path (str): Path where the downloaded segment will be saved
            max_retries (int, optional): Maximum number of retry attempts. Defaults to 3
            retry_delay (float, optional): Initial delay between retries in seconds. Defaults to 0.5
            segment_delay (float, optional): Delay after successful download. Defaults to 0

        Returns:
            bool: True if download was successful, False otherwise
        
        This function attempts to download a segment with retry logic for robustness.
        It handles authentication via cookies or stream keys, and includes proper
        error handling for network issues and invalid credentials.
        When 429 errors are encountered, the delay will be increased using the rate_limiter.
        """
        global kill
        # Get host from URL for rate limiting
        host = urlparse(segment_url).netloc
        
        with download_semaphore:
            for retry_count in range(max_retries + 1):
                if shutdown_flag:
                    if args.debug:
                        print_debug_message("Shutdown requested, aborting segment download.")
                    break
                try:
                    # show downloading segments if args debug is set
                    if args.debug:
                        print_debug_message(f"Downloading segment: {segment_url}")
                    
                    response = (
                        requests.get(
                            segment_url, stream=True, cookies=cookies, params=params
                        )
                        if cookies
                        else requests.get(segment_url, stream=True, params=params)
                    )

                    # Check for successful response
                    if response.status_code == 200:
                        with open(output_path, "wb") as file:
                            for chunk in response.iter_content(chunk_size=16000):
                                file.write(chunk)
                        # Reset delay on successful request
                        global_rate_limiter.reset_delay(host)
                        # time.sleep(segment_delay)  # Optional delay
                        return True
                    elif response.status_code == 401:
                        print_error_message("Invalid credentials. Please check your cookies/streamkey and try again.")
                        input(f"{Fore.RED}Press CTRL+C to exit...{Style.RESET_ALL}")
                        kill = True
                        raise Exception("Exiting due to invalid credentials")
                    elif response.status_code == 429:
                        # Use rate limiter to increase delay
                        delay = global_rate_limiter.increase_delay(host)
                        print_error_message(f"Rate limit exceeded (HTTP 429). Increasing delay to {delay:.1f} seconds...")
                        time.sleep(delay)
                    else:
                        print_warning_message(f"Failed to download segment, status code: {response.status_code}. Retrying {retry_count}/{max_retries}")
                except requests.exceptions.RequestException as e:
                    # Check if it's a 429 error
                    is_rate_limited = "429" in str(e) or "Too Many Requests" in str(e)
                    
                    if is_rate_limited:
                        delay = global_rate_limiter.increase_delay(host)
                        print_error_message(f"Rate limit exceeded (HTTP 429). Increasing delay to {delay:.1f} seconds...")
                    else:
                        delay = global_rate_limiter.get_delay(host)
                        print_error_message(f"Network error: {e}. Retrying {retry_count}/{max_retries} in {delay:.1f} seconds...")
                    
                    time.sleep(delay)
                except Exception as e:
                    # Check if it's a 429 error
                    is_rate_limited = "429" in str(e) or "Too Many Requests" in str(e)
                    
                    if is_rate_limited:
                        delay = global_rate_limiter.increase_delay(host)
                        print_error_message(f"Rate limit exceeded (HTTP 429). Increasing delay to {delay:.1f} seconds...")
                        time.sleep(delay)
                    else:
                        print_error_message(f"Unexpected error downloading segment: {e}")
                        break

            print_error_message(f"Failed to download segment {segment_url} after {max_retries} retries. Skipping.")
            # Clean up partial file if exists
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def load_m3u8_with_retry(hls_url, retry_delay=5):
        """
        Load and parse an M3U8 playlist with retry logic.

        Args:
            hls_url (str): URL of the M3U8 playlist to load
            retry_delay (int, optional): Initial delay between retries in seconds. Defaults to 5

        Returns:
            m3u8.M3U8: Parsed M3U8 playlist object, or None if loading fails or shutdown is requested
            
        This function handles various network errors that may occur while loading
        the M3U8 playlist, implementing adaptive retry logic with rate limiting support.
        It uses the rate_limiter module to automatically adjust delays when 429 errors occur.
        It also supports multi-line URLs by taking the first line.
        """        # Get host from URL for rate limiting
        cleaned_url = hls_url.strip().split('\n')[0]
        host = urlparse(cleaned_url).netloc
        
        while not shutdown_flag:
            if shutdown_flag:
                if args.debug:
                    print_debug_message("Shutdown requested, aborting m3u8 load.")
                break
            try:
                if args.debug:
                    print_debug_message(f"Loading m3u8 from URL: {cleaned_url}")
                
                m3u8_obj = m3u8.load(cleaned_url)
                # Reset delay on successful request
                global_rate_limiter.reset_delay(host)
                return m3u8_obj
            except (
                http.client.RemoteDisconnected,
                http.client.IncompleteRead,
                requests.exceptions.RequestException,
            ) as e:
                # Check if it's a 429 error
                is_rate_limited = "429" in str(e) or "Too Many Requests" in str(e)
                
                if is_rate_limited:
                    delay = global_rate_limiter.increase_delay(host)
                    print_error_message(f"Rate limit exceeded (HTTP 429). Increasing delay to {delay:.1f} seconds...")
                else:
                    delay = global_rate_limiter.get_delay(host)
                    print_error_message(f"Error loading m3u8 file: {e}. Retrying in {delay:.1f} seconds...")
                
                time.sleep(delay)
            except Exception as e:
                # Check if it's a 429 error
                is_rate_limited = "429" in str(e) or "Too Many Requests" in str(e)
                
                if is_rate_limited:
                    delay = global_rate_limiter.increase_delay(host)
                    print_error_message(f"Rate limit exceeded (HTTP 429). Increasing delay to {delay:.1f} seconds...")
                else:
                    delay = global_rate_limiter.get_delay(host)
                    print_error_message(f"Unexpected error loading m3u8 file: {e}")
                
                time.sleep(delay)
        return None

    def generate_segment_filename(url, counter, task_id):
        """
        Generate a unique filename for a downloaded HLS segment.

        Args:
            url (str): URL of the HLS segment
            counter (int): Sequential counter for segment ordering
            task_id (str): Unique identifier for the transcription task

        Returns:
            str: Generated filename including task ID, counter, and URL hash

        The function creates a filename that includes:
        - Task ID to group segments from the same transcription
        - Counter for sequential ordering (zero-padded to 5 digits)
        - MD5 hash of URL to ensure uniqueness
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(temp_dir, f"{task_id}_{counter:05d}_{url_hash}.ts")

    def combine_audio_segments(segment_paths, output_path, keep_segments=None):
        """
        Combine multiple HLS segments into a single audio file.

        Args:
            segment_paths (list[str]): List of paths to segment files to combine
            output_path (str): Path where the combined file will be saved
            keep_segments (list[str], optional): List of segment paths to keep (not delete)

        The function reads each segment file in binary mode and writes them
        sequentially to create a single combined file. It handles missing
        files gracefully and cleans up individual segment files after combining,
        except for those specified in keep_segments.
        """
        if keep_segments is None:
            keep_segments = []
        
        with open(output_path, "wb") as outfile:
            for segment_path in segment_paths:
                if not os.path.exists(segment_path):
                    print(f"Warning: File {segment_path} does not exist, skipping.")
                    continue
                try:
                    with open(segment_path, "rb") as infile:
                        outfile.write(infile.read())
                    # Only remove if not in keep_segments list
                    if segment_path not in keep_segments:
                        os.remove(segment_path)
                except Exception as e:
                    print(f"Error combining audio segments: {e}")

    def translate_audio(file_path, model):
        """
        Translate audio content to English using Whisper model.

        Args:
            file_path (str): Path to the audio file to translate
            model (object): Loaded Whisper model instance

        Returns:
            str: Translated text in English, or empty string if translation fails        Uses Whisper's translate task to directly translate audio to English text.
        Includes fp16 optimization and previous text conditioning based on arguments.
        """
        try:
            return model.transcribe(file_path, task="translate", fp16=args.fp16, language="English", condition_on_previous_text=args.condition_on_previous_text)
        except RuntimeError as e:
            print_error_message(f"Error translating audio: {e}")
            return ""

    def transcribe_audio(file_path, model, language):
        """
        Transcribe audio content in a specified language using Whisper model.

        Args:
            file_path (str): Path to the audio file to transcribe
            model (object): Loaded Whisper model instance
            language (str): Language code for transcription

        Returns:
            str: Transcribed text in specified language, or empty string if transcription fails        Uses Whisper's transcribe task with specified language, fp16 optimization,
        and previous text conditioning based on arguments.
        """
        try:
            return model.transcribe(file_path, language=language, fp16=args.fp16, condition_on_previous_text=args.condition_on_previous_text, task="transcribe")
        except IndexError:
            print_error_message(f"Audio decoding error for segment: {os.path.basename(file_path)} (IndexError).")
            print_warning_message("This is likely due to a corrupted or empty audio segment from the stream. Skipping this chunk.")
            return ""
        except Exception as e:
            # Catch other potential decoding errors from PyAV
            if "av." in str(e):
                print_error_message(f"Audio decoding error for segment: {os.path.basename(file_path)} ({type(e).__name__}).")
                print_warning_message("This is likely due to a corrupted audio segment from the stream. Skipping this chunk.")
                return ""
            else:
                print_error_message(f"An unexpected error occurred during transcription: {e}")
                return ""

    def detect_language(file_path, model, device=args.device):
        """
        Detect the language of audio content using Whisper model.

        Args:
            file_path (str): Path to the audio file to analyze
            model (object): Loaded Whisper model instance
            device (str): Device to run inference on (CPU/CUDA/iGPU/dGPU/NPU). Defaults to args.device

        Returns:
            str: Detected language code, or "n/a" if detection fails

        Processes audio through mel spectrogram generation with adaptive n_mels
        based on RAM configuration (128 for 11gb-v3, 80 otherwise) before
        performing language detection.
        """
        try:
            language_probs = model.detect_language(file_path, ram=args.ram, device=device)
            detected_language = max(language_probs, key=language_probs.get)
            return detected_language
        except RuntimeError as e:
            print_error_message(f"Error detecting language: {e}")
            detected_language = "n/a"
            return detected_language


    def process_audio(file_path, model):
        """
        Process audio file through transcription, translation, and output handling.

        Args:
            file_path (str): Path to the audio file to process
            model (object): Loaded Whisper model instance

        This function orchestrates the complete audio processing workflow:
        1. Original language transcription (if enabled)
        2. English translation (if tasktranslate_task is True)
        3. Target language transcription (if tasktranscribe_task is True)
        
        Results are:
        - Printed to console with visual separators
        - Sent to Discord webhook if configured
        - Updated in API backend if port number is set
        
        The audio file is automatically cleaned up after processing.
        """
        global combined_files_in_queue
        global DEBUG_BLOCK_SIMILAR

        # Store last messages for each type
        if not hasattr(process_audio, "last_transcription"):
            process_audio.last_transcription = None
        if not hasattr(process_audio, "last_translation"):
            process_audio.last_translation = None
        if not hasattr(process_audio, "last_target_transcription"):
            process_audio.last_target_transcription = None
        import os
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping.")
            return

        # Remove from tracking if it's a combined file
        if "_combined_" in file_path:
            try:
                combined_files_in_queue.remove(file_path)
            except ValueError:
                pass  # File might not be in list if tracking started after file was created

        # --- Vocal isolation for HLS chunk (Demucs) ---
        processed_audio_path = file_path
        if getattr(args, 'isolate_vocals', False):
            try:
                if args.debug:
                    print_info_message(" Isolating vocals from HLS chunk using Demucs... This may take additional time.")
                with tempfile.TemporaryDirectory() as tmpdir:
                    demucs_python_path = get_demucs_python_path()
                    demucs_cmd = [
                        demucs_python_path,
                        '-m', 'demucs',
                        '-n', getattr(args, 'demucs_model', 'htdemucs'),
                        '-o', tmpdir,
                        '--two-stems', 'vocals',
                    ]
                    if getattr(args, 'device', None) == 'cuda':
                        demucs_cmd += ['-d', 'cuda']
                    # Add jobs parameter if specified
                    if hasattr(args, 'demucs_jobs') and args.demucs_jobs > 0:
                        demucs_cmd.extend(['-j', str(args.demucs_jobs)])
                    demucs_cmd.append(str(file_path))
                    result = subprocess.run(
                        demucs_cmd,
                        capture_output=True, text=True, encoding='utf-8', errors='replace')
                    if args.debug:
                        print_debug_message(f"Demucs return code: {result.returncode}")
                        if result.stdout:
                            print_debug_message(f"Demucs stdout: {result.stdout[:500]}...")
                        if result.stderr:
                            print_debug_message(f"Demucs stderr: {result.stderr[:500]}...")
                    if result.returncode != 0:
                        print_error_message(f"Demucs failed with return code {result.returncode}: {result.stderr}")
                    else:
                        base_name = os.path.splitext(os.path.basename(str(file_path)))[0]
                        vocals_path = None
                        demucs_model = getattr(args, 'demucs_model', 'htdemucs')
                        possible_locations = [
                            os.path.join(tmpdir, demucs_model, base_name, 'vocals.wav'),
                            os.path.join(tmpdir, 'demucs', base_name, 'vocals.wav'),
                            os.path.join(tmpdir, 'htdemucs', base_name, 'vocals.wav'),
                            os.path.join(tmpdir, 'mdx_extra', base_name, 'vocals.wav'),
                            os.path.join(tmpdir, base_name, 'vocals.wav'),
                        ]
                        for root, dirs, files in os.walk(tmpdir):
                            if 'vocals.wav' in files:
                                vocals_path = os.path.join(root, 'vocals.wav')
                                if args.debug:
                                    print_success_message(f"Found vocals.wav at: {vocals_path}")
                                break
                        if not vocals_path:
                            for location in possible_locations:
                                if os.path.exists(location):
                                    vocals_path = location
                                    if args.debug:
                                        print_success_message(f"Found vocals.wav at predefined location: {vocals_path}")
                                    break
                        if not vocals_path or not os.path.exists(vocals_path):
                            print_error_message(f"Vocal isolation failed: vocals.wav not found. Expected at: {possible_locations[0]}")
                        else:
                            # Use absolute path for temp/audio/ folder
                            from datetime import datetime
                            utc_folder = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            dest_dir = os.path.join(script_dir, 'temp', 'audio', utc_folder)
                            os.makedirs(dest_dir, exist_ok=True)
                            for file in os.listdir(os.path.dirname(vocals_path)):
                                src_file = os.path.join(os.path.dirname(vocals_path), file)
                                if os.path.isfile(src_file):
                                    shutil.copy2(src_file, os.path.join(dest_dir, file))
                            processed_audio_path = os.path.join(dest_dir, 'vocals.wav')
                            if args.debug:
                                print_success_message(f" Vocal isolation complete. Using isolated vocals for transcription. Split files saved to {dest_dir}")
                                print_info_message(f"Using vocals file: {processed_audio_path}")
            except Exception as e:
                print_error_message(f"Vocal isolation failed: {str(e)}")

        transcription = None
        translation = None
        detected_language = stream_language if stream_language else 'en'

        if args.stream_original_text:
            if not stream_language:
                detected_language = detect_language(processed_audio_path, model)
            
            transcription = transcribe_audio(
                processed_audio_path, model, language=detected_language
            )

            # Check original transcription against blocklist
            if is_phrase_in_blocklist(transcription, BLOCKLIST_PATH):
                if DEBUG_BLOCK_SIMILAR: print(f"[DEBUG] Original transcription blocked by list: '{transcription}'")
                transcription = ""  # Clear the text

            if ENABLE_SIMILAR_PROTECTION:
                is_new = transcription and not is_similar(transcription, process_audio.last_transcription)
            else:
                is_new = bool(transcription)
            
            if is_new:
                print_transcription_result(detected_language, transcription, "Original")
                process_audio.last_transcription = transcription
                if args.portnumber and transcription.strip():
                    new_header = f"{transcription}"
                    api_backend.update_header(new_header)
            else:
                already_blocked = False
                if AUTO_BLOCKLIST_ENABLED and BLOCKLIST_PATH and transcription:
                    msg = transcription.strip()
                    blocked_phrase_history["original"].append(msg)
                    if blocked_phrase_history["original"].count(msg) >= 3:
                        already_blocked = add_phrase_to_blocklist(msg, BLOCKLIST_PATH)
                if DEBUG_BLOCK_SIMILAR and not already_blocked and transcription:
                    print(f"[DEBUG] Blocked similar original message: {transcription}")

        if tasktranslate_task:
            translation = translate_audio(processed_audio_path, model)

            # Check translation against blocklist
            if is_phrase_in_blocklist(translation, BLOCKLIST_PATH):
                if DEBUG_BLOCK_SIMILAR: print(f"[DEBUG] Translation blocked by list: '{translation}'")
                translation = "" # Clear the text

            if ENABLE_SIMILAR_PROTECTION:
                is_new = translation and not is_similar(translation, process_audio.last_translation)
            else:
                is_new = bool(translation)
            
            if is_new:
                print_transcription_result("EN", translation, "Translation")
                process_audio.last_translation = translation
                if webhook_url:
                    send_transcription_to_discord(
                        webhook_url, detected_language, translation, "Translation"
                    )
                if args.portnumber:
                    new_header = f"{translation}"
                    api_backend.update_translated_header(new_header)
            else:
                already_blocked = False
                if AUTO_BLOCKLIST_ENABLED and BLOCKLIST_PATH and translation:
                    msg = translation.strip()
                    blocked_phrase_history["translation"].append(msg)
                    if blocked_phrase_history["translation"].count(msg) >= 3:
                        already_blocked = add_phrase_to_blocklist(msg, BLOCKLIST_PATH)
                if DEBUG_BLOCK_SIMILAR and not already_blocked and translation:
                    print(f"[DEBUG] Blocked similar translation message: {translation}")

        if tasktranscribe_task:
            transcription = transcribe_audio(
                processed_audio_path, model, language=target_language
            )
            
            # Check target transcription against blocklist
            if is_phrase_in_blocklist(transcription, BLOCKLIST_PATH):
                if DEBUG_BLOCK_SIMILAR: print(f"[DEBUG] Target transcription blocked by list: '{transcription}'")
                transcription = "" # Clear the text

            if ENABLE_SIMILAR_PROTECTION:
                is_new = transcription and not is_similar(transcription, process_audio.last_target_transcription)
            else:
                is_new = bool(transcription)

            if is_new:
                print_transcription_result(target_language, transcription, "Transcription")
                process_audio.last_target_transcription = transcription
                if webhook_url:
                    send_transcription_to_discord(
                        webhook_url, target_language, transcription, "Transcription"
                    )
                if args.portnumber and transcription.strip():
                    new_header = f"{transcription}"
                    api_backend.update_transcribed_header(new_header)
            else:
                already_blocked = False
                if AUTO_BLOCKLIST_ENABLED and BLOCKLIST_PATH and transcription:
                    msg = transcription.strip()
                    blocked_phrase_history["target"].append(msg)
                    if blocked_phrase_history["target"].count(msg) >= 3:
                        already_blocked = add_phrase_to_blocklist(msg, BLOCKLIST_PATH)
                if DEBUG_BLOCK_SIMILAR and not already_blocked and transcription:
                    print(f"[DEBUG] Blocked similar target transcription message: {transcription}")

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

    def process_audio_thread():
        """
        Background thread function for processing audio segments.

        This thread continuously monitors the audio queue for new segments to process.
        When a segment is available, it calls process_audio() to handle transcription
        and translation. The thread runs until either:
        - shutdown_flag is set to True
        - None is received in the queue (signal to stop)

        This threaded approach allows concurrent downloading and processing of audio
        segments, improving overall throughput of the transcription system.
        """
        while not shutdown_flag:
            file_path = audio_queue.get()
            if file_path is None:
                break
            process_audio(file_path, model_name)

    # Start processing thread
    processing_thread = threading.Thread(target=process_audio_thread)
    processing_thread.daemon = True
    processing_thread.start()    # --- Auto HLS Adjustment Feature ---
    if getattr(args, 'auto_hls', False):
        print_styled_header("Auto HLS Adjustment", Fore.YELLOW, 76)
        print_info_message("Sampling the stream to determine segment duration...")
        m3u8_obj = load_m3u8_with_retry(hls_url)
        if m3u8_obj and m3u8_obj.segments:
            first_segment = m3u8_obj.segments[0]
            segment_duration = getattr(first_segment, 'duration', None)
            if segment_duration is not None:
                print_success_message(f"Detected segment duration: {segment_duration:.2f} seconds")
                print_info_message(f"Current chunk size (segments per batch): {segments_max}")
                print_info_message(f"Each batch will cover ~{segments_max * segment_duration:.2f} seconds of audio")
                if args.paddedaudio and args.paddedaudio > 0:
                    print_info_message(f"Each batch will include ~{args.paddedaudio * segment_duration:.2f} seconds of padded audio making the total ~{(segments_max + args.paddedaudio) * segment_duration:.2f} seconds")
                user_input = input(f"{Fore.CYAN}🔧 Would you like to set a new chunk size? (y/n): {Style.RESET_ALL}").strip().lower()
                if user_input == 'y':
                    while True:
                        try:
                            new_chunk = int(input(f"{Fore.CYAN} Enter new chunk size (number of segments per batch): {Style.RESET_ALL}").strip())
                            if new_chunk > 0:
                                est_time = new_chunk * segment_duration
                                # if padded audio is enabled, account for padding
                                if args.paddedaudio and args.paddedaudio > 0:
                                    est_time += args.paddedaudio * segment_duration
                                    print_info_message("Padded audio will be included in the chunk duration")
                                print_info_message(f"If chunk size is {new_chunk}, each batch will cover ~{est_time:.2f} seconds")
                                confirm = input(f"{Fore.YELLOW} Confirm this chunk size? (y to confirm, n to set again, c to cancel): {Style.RESET_ALL}").strip().lower()
                                if confirm == 'y':
                                    segments_max = new_chunk
                                    print_success_message(f"Chunk size set to {segments_max} (covers ~{segments_max * segment_duration:.2f} seconds per batch)")
                                    break
                                elif confirm == 'c':
                                    print_info_message("Keeping existing chunk size")
                                    break
                                # else loop again for new input
                            else:
                                print_warning_message("Please enter a positive integer")
                        except ValueError:
                            print_error_message("Invalid input. Please enter a number")
                else:
                    print_info_message("Keeping existing chunk size")
            else:
                print_warning_message("Could not determine segment duration. Proceeding with default chunk size")
        else:
            print_error_message("Could not load playlist or no segments found. Proceeding with default chunk size")    # Main loop for downloading and combining segments
    try:
        downloaded_segments = set()
        counter = 0
        accumulated_segments = []
        previous_batch_segments = []  # Store segments from previous batch for padding
        padded_audio_count = getattr(args, 'paddedaudio', 0)

        while not shutdown_flag:
            m3u8_obj = load_m3u8_with_retry(hls_url)
            if not m3u8_obj:
                print_error_message("Failed to load m3u8 after retries, stopping")
                break

            # Get total segments and calculate starting point
            total_segments = len(m3u8_obj.segments)
            if total_segments == 0:
                if args.debug:
                    print_debug_message("Playlist is empty, waiting for segments...")
                time.sleep(1)  # Wait if playlist is empty
                continue

            # Start from the most recent segments on first run
            if len(downloaded_segments) == 0:
                start_idx = max(0, total_segments - segments_max)
                if args.debug:
                    print_debug_message(f"First run:")
                    print_debug_message(f"Total segments in playlist: {total_segments}")
                    print_debug_message(f"Starting from segment index: {start_idx}")
                    print_debug_message(f"Will process {total_segments - start_idx} segments")
            else:
                start_idx = 0
                if args.debug:
                    print_debug_message(f"Continuing run:")
                    print_debug_message(f"Total segments in playlist: {total_segments}")
                    print_debug_message(f"Previously downloaded segments: {len(downloaded_segments)}")
                    print_debug_message(f"Starting from beginning to check for new segments")

            # Process segments from the calculated starting point
            for idx in range(start_idx, total_segments):
                segment = m3u8_obj.segments[idx]
                if segment.uri in downloaded_segments:
                    continue  # Skip already downloaded segments

                segment_path = generate_segment_filename(
                    segment.uri, counter, task_id
                )
                counter += 1
                try:
                    if args.debug:
                        print_debug_message(f"Attempting to download segment {counter}:")
                        print_debug_message(f"Segment URI: {segment.uri}")

                    if download_segment(segment.absolute_uri, segment_path):
                        if kill:
                            break
                        downloaded_segments.add(segment.uri)
                        accumulated_segments.append(segment_path)

                        if args.debug:
                            print_debug_message(f"Successfully downloaded segment {counter}")
                            print_debug_message(f"Accumulated segments: {len(accumulated_segments)}/{segments_max}")

                        if len(accumulated_segments) >= segments_max:
                            if args.debug:
                                print_debug_message(f"Reached max segments ({segments_max}), processing batch...")
                            
                            # Prepare segments for combination including padding
                            segments_to_combine = []
                            keep_segments = []
                            
                            # Add previous batch segments for padding if enabled
                            if padded_audio_count > 0 and previous_batch_segments:
                                padding_segments = previous_batch_segments[-padded_audio_count:]
                                segments_to_combine.extend(padding_segments)
                                keep_segments.extend(padding_segments)  # Keep padding segments for reuse
                                if args.debug:
                                    print_debug_message(f"Adding {len(padding_segments)} padded segments from previous batch")                            # Store current batch for next iteration's padding BEFORE combining/deleting
                            if padded_audio_count > 0:
                                previous_batch_segments = accumulated_segments.copy()
                                # Also keep the last few segments from current batch for next iteration
                                padding_segments_to_keep = accumulated_segments[-padded_audio_count:]
                                keep_segments.extend(padding_segments_to_keep)
                            
                            # Add current batch segments
                            segments_to_combine.extend(accumulated_segments)
                            

                            combined_path = os.path.join(
                                temp_dir, f"{task_id}_combined_{counter}.ts"
                            )
                            combine_audio_segments(
                                segments_to_combine, combined_path, keep_segments
                            )
                            
                            # Track combined file and check queue size
                            combined_files_in_queue.append(combined_path)
                            if args.debug:
                                if len(combined_files_in_queue) > MAX_COMBINED_FILES:
                                    print_warning_message("More than 5 combined files are waiting to be processed")
                                    print_warning_message("This may indicate that your GPU cannot keep up with transcription load")
                                    print_info_message("Consider using a smaller model or increasing processing power")

                            audio_queue.put(combined_path)
                            
                            accumulated_segments = []
                except Exception as e:  # Catch the raised exception
                    print_error_message(f"Error during download: {e}")
                    break  # Exit the loop

    except KeyboardInterrupt:
        shutdown_flag = True  # Signal to shut down

    except Exception as e:
        exit(0)

    # Cleanup
    combined_files_in_queue.clear()  # Clear the tracking list
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    audio_queue.put(None)  # Signal processing thread to stop
    processing_thread.join()


def stop_transcription():
    """
    Stop the transcription process gracefully.

    Sets the global shutdown flag to True, which signals various components to stop:
    - M3U8 playlist loading loop
    - Audio processing thread
    - Main segment downloading loop
    
    After this is called, the transcription system will:
    1. Complete processing of current segments
    2. Clean up temporary files
    3. Join the processing thread
    4. Exit cleanly
    """
    global shutdown_flag
    shutdown_flag = True


print(f"{Fore.GREEN}Stream Transcription Module Loaded{Style.RESET_ALL}")

# Track repeated blocked phrases for auto-blocking (rolling window)
blocked_phrase_history = {
    "original": deque(maxlen=10),
    "translation": deque(maxlen=10),
    "target": deque(maxlen=10),
}

# Check if auto-blocking is enabled and blocklist is set
AUTO_BLOCKLIST_ENABLED = getattr(args, 'auto_blocklist', False)
BLOCKLIST_PATH = getattr(args, 'ignorelist', None)