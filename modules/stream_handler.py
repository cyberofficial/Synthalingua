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
    
    hls_url = subprocess.check_output(yt_dlp_command).decode("utf-8").strip()
    print(f"Found the Stream URL:\n{hls_url}")
    
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