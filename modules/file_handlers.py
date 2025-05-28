"""
File handling module for managing files and directories.

This module provides utilities for file operations including:
- Managing blacklist files
- Handling temporary directories for audio processing
- Saving transcription results
- Error logging and reporting
- Cookie file path resolution
"""

import os
from datetime import datetime
from modules.discord import send_to_discord_webhook, send_error_notification

def load_blacklist(filename):
    """
    Load and parse the blacklist file.

    Reads a text file containing blacklisted terms or phrases, with each entry
    on a new line. Skips empty lines.

    Args:
        filename (str): Path to the blacklist file (.txt format)

    Returns:
        list: List of blacklisted terms

    Raises:
        ValueError: If the file extension is not .txt
    """
    if not filename.endswith(".txt"):
        raise ValueError("Blacklist file must be in .txt format.")

    blacklist = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    blacklist.append(word)
    except FileNotFoundError:
        print(f"Warning: Blacklist file '{filename}' not found.")
    return blacklist

def setup_temp_directory():
    """
    Set up temporary directory for audio files.

    Creates a 'temp' directory if it doesn't exist, used for storing
    temporary audio files during processing.

    Returns:
        str: Path to the temporary directory
    """
    if not os.path.exists("temp"):
        os.makedirs("temp")
    return "temp"

def clean_temp_directory(temp_dir):
    """
    Clean temporary directory of non-recording files.

    Removes all files in the temporary directory that don't start with 'rec_',
    which are used to identify active recording files.

    Args:
        temp_dir (str): Path to the temporary directory
    """
    try:
        for file in os.listdir(temp_dir):
            if not file.startswith("rec_"):
                os.remove(os.path.join(temp_dir, file))
    except Exception:
        pass

def save_transcript(transcription, args):
    """
    Save transcription to a file.

    Saves the transcription results including original text, translations,
    and transcriptions to a text file. Creates numbered files if multiple
    transcriptions exist.

    Args:
        transcription (list): List of tuples containing (original_text,
            translated_text, transcribed_text, detected_language)
        args: Command line arguments containing output directory settings
    """
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
    """
    Handle and log errors.

    Logs errors to a file and optionally sends them to a Discord webhook.
    Handles keyboard interrupts differently from other errors.

    Args:
        e (Exception): The error to handle
        webhook_url (str, optional): Discord webhook URL for error reporting    Returns:
        bool: True if the error was a KeyboardInterrupt, False otherwise
    """
    if not isinstance(e, KeyboardInterrupt):
        print(e)
        if os.path.isfile('error_report.txt'):
            mode = 'a'
        else:
            mode = 'w'
        
        with open('error_report.txt', mode) as error_report_file:
            error_report_file.write(str(e))
            
        if webhook_url:
            send_error_notification(webhook_url, str(e))
    return isinstance(e, KeyboardInterrupt)

def resolve_cookie_file_path(cookies_arg):
    """
    Resolve cookie file path with multiple search locations.
    
    This function searches for cookie files in the following order:
    1. If cookies_arg is an absolute path to an existing file, use it directly
    2. If cookies_arg is a filename with extension that exists in current directory, use it
    3. If cookies_arg (with .txt appended if needed) exists in cookies/ folder, use that
    
    Args:
        cookies_arg (str): The cookies argument value from command line
        
    Returns:
        str: Resolved path to the cookie file, or None if not found
        
    Examples:
        resolve_cookie_file_path("C:\\path\\to\\youtube.txt")  # Returns absolute path if exists
        resolve_cookie_file_path("youtube.txt")               # Checks current dir, then cookies/youtube.txt
        resolve_cookie_file_path("youtube")                   # Checks cookies/youtube.txt
    """
    if not cookies_arg:
        return None
    
    # 1. Check if it's an absolute path to an existing file
    if os.path.isabs(cookies_arg) and os.path.isfile(cookies_arg):
        return cookies_arg
    
    # 2. Check if it's a filename (with extension) in the current directory
    if os.path.isfile(cookies_arg):
        return cookies_arg
    
    # 3. Check in cookies/ folder
    # If the argument doesn't have .txt extension, add it
    cookies_filename = cookies_arg if cookies_arg.endswith('.txt') else f"{cookies_arg}.txt"
    cookies_folder_path = os.path.join("cookies", cookies_filename)
    
    if os.path.isfile(cookies_folder_path):
        return cookies_folder_path
    
    # If none of the above locations work, return None
    return None