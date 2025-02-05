import os
import subprocess
from modules.stream_transcription_module import start_stream_transcription, stop_transcription
import threading

def handle_stream_setup(args, audio_model, temp_dir, webhook_url=None):
    """Set up and initialize stream processing."""
    
    # Get stream parameters
    stream_language = args.stream_language
    target_language = args.stream_target_language if args.stream_target_language else "en"
    translate_task = bool(args.stream_translate)
    transcribe_task = bool(args.stream_transcribe)
    
    # Handle cookies if specified
    cookie_file_path = None
    if args.cookies:
        cookie_file_path = f"cookies\\{args.cookies}.txt"
    
    # Get HLS URL using yt-dlp
    yt_dlp_command = ["yt-dlp", args.stream, "-g"]
    if cookie_file_path:
        yt_dlp_command.extend(["--cookies", cookie_file_path])
    
    try:
        urls = subprocess.check_output(yt_dlp_command).decode("utf-8").strip().split('\n')
        
        # Filter for audio stream URL (usually contains itag=140 for YouTube)
        audio_urls = [url for url in urls if 'itag=140' in url]
        hls_url = audio_urls[0] if audio_urls else urls[0]
        
        if args.debug:
            print("\n[DEBUG] Found URLs:")
            for url in urls:
                print(f"[DEBUG] - {url}")
            print(f"\n[DEBUG] Selected URL for processing:\n{hls_url}")
        else:
            print(f"Found the Stream URL:\n{hls_url}")
    except subprocess.CalledProcessError as e:
        print(f"Error fetching stream URL: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error processing stream URL: {e}")
        raise
    
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