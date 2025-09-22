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
import tempfile
import subprocess
import re  # Import regex for normalization
from datetime import datetime
from modules.discord import send_to_discord_webhook, send_error_notification
from colorama import Fore, Style, init

# Initialize colorama for Windows compatibility
init(autoreset=True)

def print_warning_message(message):
    """Print a warning message with styling."""
    print(f"{Fore.YELLOW}{Style.BRIGHT}[WARNING]{Style.RESET_ALL} {message}")

def print_info_message(message):
    """Print an info message with styling."""
    print(f"{Fore.CYAN}{Style.BRIGHT}[INFO]{Style.RESET_ALL} {message}")

def print_success_message(message):
    """Print a success message with styling."""
    print(f"{Fore.GREEN}{Style.BRIGHT}[SUCCESS]{Style.RESET_ALL} {message}")

def print_error_message(message):
    """Print an error message with styling."""
    print(f"{Fore.RED}{Style.BRIGHT}[ERROR]{Style.RESET_ALL} {message}")

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
                # Skip empty lines only
                if word:
                    blacklist.append(word)
    except FileNotFoundError:
        print_warning_message(f"Ignorelist file '{filename}' not found.")
        print_info_message("An ignorelist file helps filter out unwanted words or phrases from transcriptions.")
        
        # Ask user if they want to create the file
        try:
            user_input = input(f"\n{Fore.YELLOW}Would you like to create an ignorelist file at '{filename}'? (y/n): {Style.RESET_ALL}").lower().strip()
            
            if user_input == 'y' or user_input == 'yes':
                try:
                    # Create directory if it doesn't exist
                    directory = os.path.dirname(filename)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory)
                        print_info_message(f"Created directory: {directory}")
                    
                    # Create the file with basic example content (no comments)
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write("thanks for watching\n")
                        f.write("please subscribe\n")
                        f.write("like and subscribe\n")
                    
                    print_success_message(f"Ignorelist file created at '{filename}'")
                    print_info_message("You can edit this file to add words or phrases you want to filter out.")
                    print_info_message("Each word or phrase should be on a separate line.")
                    
                except Exception as e:
                    print_error_message(f"Failed to create ignorelist file: {e}")
            else:
                print_info_message("Continuing without ignorelist file. No filtering will be applied.")
                
        except KeyboardInterrupt:
            print_info_message("\nContinuing without ignorelist file.")
        except EOFError:
            print_info_message("Continuing without ignorelist file.")
    
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
    transcriptions exist.    Args:
        transcription (list): List of tuples containing (original_text,
            translated_text, transcribed_text, detected_language)
        args: Command line arguments containing output directory settings
    """
    if not args.save_folder:
        out = "out"
    else:
        out = args.save_folder
    
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

def load_cookies_from_browser(browser_name):
    """
    Load cookies from a browser using yt-dlp's cookie extraction functionality.
    
    Args:
        browser_name (str): Name of the browser to extract cookies from
        
    Returns:
        str: Path to the temporary cookies file, or None if extraction failed
        
    This function uses yt-dlp's built-in browser cookie extraction to create
    a temporary Netscape-format cookies file. The file should be cleaned up
    by the caller when no longer needed.
    """
    try:
        # Create a temporary file for cookies
        temp_fd, temp_path = tempfile.mkstemp(suffix='.txt', prefix='synthalingua_cookies_')
        os.close(temp_fd)  # Close the file descriptor as we'll let yt-dlp write to it
        
        print_info_message(f"Extracting cookies from {browser_name} browser...")
        
        # Use yt-dlp to extract cookies from browser
        # We'll use a dummy URL to trigger cookie extraction
        yt_dlp_command = [
            "yt-dlp",
            "--cookies-from-browser", browser_name,
            "--cookies", temp_path,
            "--simulate",
            "--no-warnings",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Dummy URL
        ]
        
        result = subprocess.run(yt_dlp_command, 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        # Check if the command was successful and cookies file was created
        if result.returncode == 0 and os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print_success_message(f"Successfully extracted cookies from {browser_name}")
            return temp_path
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            print_error_message(f"Failed to extract cookies from {browser_name}: {error_msg}")
            # Clean up the temporary file if it was created but empty/invalid
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None
            
    except subprocess.TimeoutExpired:
        print_error_message(f"Timeout while extracting cookies from {browser_name}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None
    except Exception as e:
        print_error_message(f"Error extracting cookies from {browser_name}: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None

def cleanup_temp_cookie_file(cookie_file_path):
    """
    Clean up temporary cookie file created by load_cookies_from_browser.
    
    Args:
        cookie_file_path (str): Path to the temporary cookie file
        
    This function safely removes temporary cookie files created during
    browser cookie extraction. It checks if the file is in a temp directory
    to avoid accidentally removing user's permanent cookie files.
    """
    if cookie_file_path and os.path.exists(cookie_file_path):
        try:
            # Only delete if it's a temporary file (contains temp in path)
            if 'temp' in cookie_file_path.lower() or cookie_file_path.startswith(tempfile.gettempdir()):
                os.remove(cookie_file_path)
                print_info_message("Cleaned up temporary cookie file")
        except Exception as e:
            print_warning_message(f"Could not clean up temporary cookie file: {str(e)}")

def resolve_cookie_file_path(cookies_arg, cookies_from_browser=None):
    """
    Resolve cookie file path with multiple search locations or extract from browser.
    
    This function searches for cookie files in the following order:
    1. If cookies_from_browser is specified, extract cookies from browser
    2. If cookies_arg is an absolute path to an existing file, use it directly
    3. If cookies_arg is a filename with extension that exists in current directory, use it
    4. If cookies_arg (with .txt appended if needed) exists in cookies/ folder, use that
    
    Args:
        cookies_arg (str): The cookies argument value from command line
        cookies_from_browser (str, optional): Browser name to extract cookies from
        
    Returns:
        str: Resolved path to the cookie file, or None if not found
        
    Examples:
        resolve_cookie_file_path("C:\\path\\to\\youtube.txt")  # Returns absolute path if exists
        resolve_cookie_file_path("youtube.txt")               # Checks current dir, then cookies/youtube.txt
        resolve_cookie_file_path("youtube")                   # Checks cookies/youtube.txt
        resolve_cookie_file_path(None, "chrome")              # Extracts cookies from Chrome browser
    """
    # Handle browser cookie extraction
    if cookies_from_browser:
        return load_cookies_from_browser(cookies_from_browser)
    
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

# Caching the blocklist to avoid reading the file on every check
_blocklist_cache = {}
_blocklist_mtime = {}

def is_phrase_in_blocklist(phrase: str, blocklist_path: str | None) -> bool:
    """
    Robustly check if any phrase from the blocklist is present in the text.
    This check is case-insensitive and ignores punctuation.
    """
    if not phrase or not blocklist_path:
        return False
    
    try:
        # Check if the file needs to be reloaded
        current_mtime = os.path.getmtime(blocklist_path)
        if blocklist_path not in _blocklist_cache or _blocklist_mtime.get(blocklist_path) != current_mtime:
            with open(blocklist_path, 'r', encoding='utf-8') as f:
                # Normalize and store the blocklist phrases
                lines = [re.sub(r'[^a-z0-9\s]', '', line.lower()).strip() for line in f]
                _blocklist_cache[blocklist_path] = [line for line in lines if line] # Filter out empty lines
            _blocklist_mtime[blocklist_path] = current_mtime
            
        blocklist = _blocklist_cache.get(blocklist_path, [])
        if not blocklist:
            return False

        # Normalize the input phrase for comparison
        normalized_phrase = re.sub(r'[^a-z0-9\s]', '', phrase.lower()).strip()
        
        # Check if any blocked phrase is a substring of the normalized phrase
        for blocked_item in blocklist:
            if blocked_item in normalized_phrase:
                return True
                
        return False
    except FileNotFoundError:
        # If the file doesn't exist, it can't contain the phrase
        return False
    except Exception as e:
        print_error_message(f"Error checking blocklist: {e}")
        return False

def add_phrase_to_blocklist(phrase: str, blocklist_path: str | None) -> bool:
    """Adds a phrase to the blocklist file if it's not already there."""
    if not phrase or not blocklist_path:
        # Cannot add to blocklist if path is not provided
        return False

    phrase = phrase.strip()
    if not phrase:
        return True  # Treat empty as already blocked

    try:
        # Use the same robust checking logic to see if it's already blocked
        if is_phrase_in_blocklist(phrase, blocklist_path):
            return True  # Already present, do not add again

        # If not present, append the original (non-normalized) phrase
        with open(blocklist_path, 'a', encoding='utf-8') as f:
            f.write(f"\n{phrase}")

        # Invalidate cache so it gets reloaded on next check
        if blocklist_path in _blocklist_cache:
            del _blocklist_cache[blocklist_path]
        if blocklist_path in _blocklist_mtime:
            del _blocklist_mtime[blocklist_path]

        print_info_message(f"Auto-added phrase to blocklist: '{phrase}'")
        return False # Indicates the phrase was newly added
    except Exception as e:
        print_error_message(f"Could not add phrase to blocklist: {e}")
        return False