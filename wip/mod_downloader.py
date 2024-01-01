import subprocess
import yt_dlp
import os

# URLs to download
urls = ['https://www.youtube.com/watch?v=BaW_jenozKc']

# Configuration for yt-dlp
ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '%(id)s.%(ext)s'  # Using video ID as filename
}

# Download the audio and extract information
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info_dict = ydl.extract_info(urls[0], download=True)
    audio_file = ydl.prepare_filename(info_dict)

# Adjust the file extension to mp3 as yt-dlp changes it after processing
audio_file = audio_file.replace(".webm", ".mp3")

# Check if the MP3 file exists
if os.path.exists(audio_file):
    # Construct Whisper CLI command
    whisper_command = [
        "whisper",
        "--model", "base",
        "--output_format", "srt",
        "--language", "English",
        audio_file
    ]

    # Run the Whisper command
    subprocess.run(whisper_command)
    print(f"Generated SRT file for: {audio_file}")
else:
    print(f"File not found: {audio_file}")
