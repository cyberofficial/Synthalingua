import os
from datetime import datetime
from modules.discord import send_to_discord_webhook

def load_blacklist(filename):
    """Load and parse the blacklist file."""
    if not filename.endswith(".txt"):
        raise ValueError("Blacklist file must be in .txt format.")

    blacklist = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                blacklist.append(line.strip())
    except FileNotFoundError:
        print(f"Warning: Blacklist file '{filename}' not found.")
    return blacklist

def setup_temp_directory():
    """Set up temporary directory for audio files."""
    if not os.path.exists("temp"):
        os.makedirs("temp")
    return "temp"

def clean_temp_directory(temp_dir):
    """Clean temporary directory of non-recording files."""
    try:
        for file in os.listdir(temp_dir):
            if not file.startswith("rec_"):
                os.remove(os.path.join(temp_dir, file))
    except Exception:
        pass

def save_transcript(transcription, args):
    """Save transcription to a file."""
    if not args.output:
        out = "out"
    else:
        out = args.output
    
    if not os.path.isdir(out):
        os.mkdir(out)

    transcript = os.path.join(os.getcwd(), out, 'transcription.txt')
    if os.path.isfile(transcript):
        transcript = os.path.join(os.getcwd(), out, 'transcription_' + str(len(os.listdir(out))) + '.txt')
    
    with open(transcript, 'w', encoding='utf-8') as transcription_file:
        for original_text, translated_text, transcribed_text, detected_language in transcription:
            transcription_file.write(f"-=-=-=-=-=-=-=-\nOriginal ({detected_language}): {original_text}\n")
            if translated_text:
                transcription_file.write(f"Translation: {translated_text}\n")
            if transcribed_text:
                transcription_file.write(f"Transcription: {transcribed_text}\n")
    
    print(f"Transcription was saved to {transcript}")

def handle_error(e, webhook_url=None):
    """Handle and log errors."""
    if not isinstance(e, KeyboardInterrupt):
        print(e)
        if os.path.isfile('error_report.txt'):
            mode = 'a'
        else:
            mode = 'w'
        
        with open('error_report.txt', mode) as error_report_file:
            error_report_file.write(str(e))
            
        if webhook_url:
            send_to_discord_webhook(webhook_url, f"Error occurred: {str(e)}")
    return isinstance(e, KeyboardInterrupt)