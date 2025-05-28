"""
Stream handling module for processing audio/video streams.

This module provides functionality for setting up and managing stream processing,
including:
- URL extraction from various streaming platforms
- Cookie handling for authenticated streams
- Stream transcription thread management
- Support for translation and transcription tasks

The module uses yt-dlp for URL extraction and handles both direct and HLS streams.
"""

import os
import subprocess
from colorama import Fore, Style
from modules.languages import get_valid_languages

# Define a constant variable for valid language choices
VALID_LANGUAGES = get_valid_languages()
from modules.stream_transcription_module import start_stream_transcription, stop_transcription
import threading

def get_available_streams(stream_url, cookie_file_path=None):
    """Get detailed information about available streams.
    
    Args:
        stream_url (str): URL of the stream
        cookie_file_path (str, optional): Path to cookies file
        
    Returns:
        str: Stream information output from yt-dlp
    """
    yt_dlp_command = ["yt-dlp", stream_url, "-F", "--no-warnings"]
    if cookie_file_path:
        yt_dlp_command.extend(["--cookies", cookie_file_path])
    
    try:
        output = subprocess.check_output(yt_dlp_command, stderr=subprocess.DEVNULL).decode("utf-8")
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error getting stream information: {e}")
        return None

def select_stream_interactive(stream_url, cookie_file_path=None):
    """Interactive stream selection with audio stream filtering.
    
    Args:
        stream_url (str): URL of the stream
        cookie_file_path (str, optional): Path to cookies file
        
    Returns:
        str: Selected format ID or format string
    """
    print("\n🔍 Fetching available streams...")
    stream_info = get_available_streams(stream_url, cookie_file_path)
    
    if not stream_info:
        print("❌ Could not fetch stream information. Using default audio format.")
        return "bestaudio"
    
    print("\n📺 Available Audio Streams:")
    print("=" * 80)
    print(stream_info)
    print("=" * 80)
    
    print("\n💡 Common audio format suggestions:")
    print("  • 'bestaudio' - Best available audio quality")
    print("  • 'worst' - Lowest bandwidth option")
    print("  • '140' - YouTube medium quality audio (m4a)")
    print("  • '139' - YouTube low quality audio (m4a)")
    print("  • '251' - YouTube high quality audio (webm)")
    print("  • Or enter any format ID from the list above")
    
    while True:
        choice = input("\n🎯 Enter format ID or format string (or press Enter for 'bestaudio'): ").strip()
        
        if not choice:
            choice = "bestaudio"
            print(f"✅ Using default: {choice}")
            break
        elif choice.lower() in ['q', 'quit', 'exit']:
            print("❌ Exiting...")
            return None
        else:
            print(f"✅ Selected: {choice}")
            break
    
    return choice

def handle_stream_setup(args, audio_model, temp_dir, webhook_url=None):
    """Set up and initialize stream processing.
    
    This function handles the complete setup process for stream transcription:
    1. Extracts stream parameters from arguments
    2. Handles cookie-based authentication if needed
    3. Extracts the HLS stream URL using yt-dlp
    4. Initializes and starts the stream transcription thread
    
    Args:
        args: Command line arguments containing stream configuration
        audio_model: Loaded Whisper model instance for transcription
        temp_dir: Directory for temporary files
        webhook_url (str, optional): URL for webhook notifications
        
    Returns:
        threading.Thread: The started stream processing thread
        
    Raises:
        subprocess.CalledProcessError: If stream URL extraction fails
        Exception: For other unexpected errors during setup
    """
      # Get stream parameters
    stream_language = args.stream_language
    
    # Handle target language (support both deprecated and new format)
    if args.stream_target_language:
        print(f"{Fore.YELLOW}Warning:{Style.RESET_ALL} --stream_target_language is deprecated. Please use --stream_transcribe <language> instead.")
        target_language = args.stream_target_language
    elif isinstance(args.stream_transcribe, str) and args.stream_transcribe in VALID_LANGUAGES:
        target_language = args.stream_transcribe
    else:
        target_language = "en"  # Default to English
        
    translate_task = bool(args.stream_translate)
    # If stream_transcribe is a string (language name), it means transcribe is enabled
    transcribe_task = args.stream_transcribe is not False
      # Handle cookies if specified
    cookie_file_path = None
    if args.cookies:
        cookie_file_path = f"cookies\\{args.cookies}.txt"
    
    # Determine format selection method
    selected_format = "bestaudio"  # default
    
    if hasattr(args, 'selectsource') and args.selectsource is not None:
        if args.selectsource == 'interactive':
            # Interactive mode
            selected_format = select_stream_interactive(args.stream, cookie_file_path)
            if selected_format is None:
                print("❌ Stream selection cancelled.")
                return None
        else:
            # Direct format specification
            selected_format = args.selectsource
            print(f"🎯 Using specified format: {selected_format}")
    else:
        print(f"🎵 Using default audio format: {selected_format}")
    
    # Get HLS URL using yt-dlp with selected format
    yt_dlp_command = ["yt-dlp", args.stream, "-g", "-f", selected_format]
    if cookie_file_path:
        yt_dlp_command.extend(["--cookies", cookie_file_path])
    
    try:
        urls = subprocess.check_output(yt_dlp_command).decode("utf-8").strip().split('\n')
        hls_url = urls[0] if urls else None
        
        if not hls_url:
            print("❌ No stream URL found with selected format.")
            return None
        
        if args.debug:
            print(f"\n[DEBUG] Selected format: {selected_format}")
            print(f"[DEBUG] Stream URL: {hls_url}")
        else:
            print(f"✅ Found stream URL with format '{selected_format}'")
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching stream URL with format '{selected_format}': {e}")
        print("💡 Tip: Try using 'bestaudio' or check available formats with --selectsource")
        return None
    except Exception as e:
        print(f"❌ Unexpected error processing stream URL: {e}")
        return None
    
    # Generate random task ID
    import random
    task_id = random.randint(100000, 999999)
    
    # Set up stream parameters
    segments_max = args.stream_chunks if hasattr(args, 'stream_chunks') else 1
    stream_key = bool(args.remote_hls_password_id)
    
    # Start stream transcription in a new thread
    stream_thread = threading.Thread(
        target=start_stream_transcription,
        args=(
            task_id,
            hls_url,
            audio_model,
            temp_dir,
            segments_max,
            target_language,
            stream_language,
            translate_task,
            transcribe_task,
            webhook_url,
            cookie_file_path,
            stream_key
        )
    )
    stream_thread.start()
    
    return stream_thread