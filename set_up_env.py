import os
import platform
import requests
import subprocess
import zipfile
import sys
from tqdm import tqdm

# URLs for downloading files
FFMPEG_URL = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2024.08.06/yt-dlp_win.zip'
SEVEN_ZIP_URL = 'https://www.7-zip.org/a/7zr.exe'

# Paths
FFMPEG_ROOT_PATH = os.path.join(os.getcwd(), 'ffmpeg')
YTDLP_PATH = os.path.join(os.getcwd(), 'yt-dlp_win')
FFMPEG_ARCHIVE = 'ffmpeg.7z'
YTDLP_ARCHIVE = 'yt-dlp_win.zip'
SEVEN_ZIP_EXEC = '7zr.exe'


def download_file(url, filename):
    """Download a file from a URL with progress display."""
    print(f"Downloading {filename} from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    with open(filename, 'wb') as file, tqdm(
            desc=filename,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
            bar.update(len(chunk))

    print(f"{filename} downloaded successfully.")


def extract_7z(file_path, extract_to):
    """Extract a .7z file using 7zr.exe."""
    print(f"Extracting {file_path} with 7zr...")
    subprocess.run([SEVEN_ZIP_EXEC, 'x', file_path, f'-o{extract_to}'], check=True)
    print(f"{file_path} extracted successfully.")


def extract_zip(file_path, extract_to):
    """Extract a .zip file to a specified directory."""
    print(f"Extracting {file_path}...")
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"{file_path} extracted successfully.")


def find_ffmpeg_bin_path(root_path):
    """Find the bin directory containing ffmpeg.exe."""
    print("Finding path for ffmpeg...")
    try:
        for root, dirs, files in os.walk(root_path):
            if 'ffmpeg.exe' in files:
                bin_path = os.path.join(root, 'ffmpeg.exe')
                print(f"Found ffmpeg.exe at: {bin_path}")
                return os.path.dirname(bin_path)
        raise FileNotFoundError("No ffmpeg.exe found in the specified path.")
    except Exception as e:
        print(f"Error finding ffmpeg.exe: {e}")
        return None


def main():

    print("This script will download the following tools:")
    print("1. FFmpeg: A multimedia framework for processing audio and video files.")
    print("2. yt-dlp: A video downloader for YouTube and other sites.")
    print("3. 7zr: A tool for extracting .7z files.")

    # Ask if user wants to provide their own 7zr
    use_own_7zr = input("Do you want to provide your own version of 7zr.exe? (yes/no): ").strip().lower()
    if use_own_7zr == 'yes':
        sevens_zip_path = input("Please enter the path to your 7zr.exe file: ").strip()
        if os.path.isfile(sevens_zip_path):
            global SEVEN_ZIP_EXEC
            SEVEN_ZIP_EXEC = sevens_zip_path
            print(f"Using provided 7zr.exe at {SEVEN_ZIP_EXEC}.")
        else:
            print("The specified 7zr.exe file does not exist.")
            return
    elif not os.path.isfile(SEVEN_ZIP_EXEC):
        download_file(SEVEN_ZIP_URL, SEVEN_ZIP_EXEC)
    else:
        print("7zr.exe already exists, skipping download.")

    # Ask if user wants to provide their own FFmpeg
    use_own_ffmpeg = input("Do you already have FFmpeg? (yes/no): ").strip().lower()
    if use_own_ffmpeg == 'yes':
        use_system_ffmpeg = input("Do you want to use the system default FFmpeg? (yes/no): ").strip().lower()
        if use_system_ffmpeg == 'yes':
            ffmpeg_path_to_use = None  # Indicate using system default
        else:
            ffmpeg_path = input("Please enter the path to your FFmpeg bin folder: ").strip()
            if os.path.isdir(ffmpeg_path):
                global FFMPEG_ROOT_PATH
                FFMPEG_ROOT_PATH = ffmpeg_path
                ffmpeg_path_to_use = find_ffmpeg_bin_path(FFMPEG_ROOT_PATH)
            else:
                print("The specified FFmpeg folder does not exist.")
                return
    elif not os.path.isdir(FFMPEG_ROOT_PATH):
        download_file(FFMPEG_URL, FFMPEG_ARCHIVE)
        extract_7z(FFMPEG_ARCHIVE, FFMPEG_ROOT_PATH)
        os.remove(FFMPEG_ARCHIVE)
        ffmpeg_path_to_use = find_ffmpeg_bin_path(FFMPEG_ROOT_PATH)
    else:
        print("FFmpeg folder already exists, skipping download.")
        ffmpeg_path_to_use = find_ffmpeg_bin_path(FFMPEG_ROOT_PATH)

    # Ask if user wants to provide their own yt-dlp
    use_own_ytdlp = input("Do you already have yt-dlp? (yes/no): ").strip().lower()
    if use_own_ytdlp == 'yes':
        use_system_ytdlp = input("Do you want to use the system default yt-dlp? (yes/no): ").strip().lower()
        if use_system_ytdlp == 'yes':
            ytdlp_path_to_use = None  # Indicate using system default
        else:
            ytdlp_path = input("Please enter the path to your yt-dlp folder: ").strip()
            if os.path.isdir(ytdlp_path):
                global YTDLP_PATH
                YTDLP_PATH = ytdlp_path
                ytdlp_path_to_use = YTDLP_PATH  # Assuming yt-dlp.exe is directly in the folder
            else:
                print("The specified yt-dlp folder does not exist.")
                return
    elif not os.path.isdir(YTDLP_PATH):
        download_file(YTDLP_URL, YTDLP_ARCHIVE)
        extract_zip(YTDLP_ARCHIVE, YTDLP_PATH)
        os.remove(YTDLP_ARCHIVE)
        ytdlp_path_to_use = YTDLP_PATH
    else:
        print("yt-dlp folder already exists, skipping download.")
        ytdlp_path_to_use = YTDLP_PATH

    # Construct the PATH string
    path_string = ""
    if ffmpeg_path_to_use:
        path_string += f"{ffmpeg_path_to_use};"
    if ytdlp_path_to_use:
        path_string += f"{ytdlp_path_to_use};"

    config_content = f'''
@echo off
:: Set Global Path Temporary
set "PATH={path_string}%PATH%"
echo PATH updated in this session.
'''
    with open('ffmpeg_path.bat', 'w') as file:
        file.write(config_content)
    print("ffmpeg_path file created with path settings.")


if __name__ == "__main__":
    print("Version 0.0.33")  # Updated version number
    system = platform.system()

    if os.path.exists("ffmpeg_path.bat"):
        print("Config file already exists. Exiting...")
        sys.exit()

    if system == "Windows":
        version_info = platform.version().split('.')
        major_version = int(version_info[0])

        if major_version >= 10:
            main()
        else:
            print("This script is for Windows 10 or newer only.")
            sys.exit(1)
    elif system == "Linux":
        print("This script isn't compatible with Linux yet.")
        sys.exit(1)
    else:
        print(f"This script is not compatible with {system}.")
        sys.exit(1)