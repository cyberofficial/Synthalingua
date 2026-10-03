"""Environment setup script for Synthalingua.

This script handles the installation and configuration of required tools:
- FFmpeg: A multimedia framework for processing audio and video files
- yt-dlp: A video downloader for YouTube and other sites
- 7zr/p7zip: A tool for extracting .7z files

The script will create a batch file (Windows) or shell script (Linux/macOS) that sets up the
necessary PATH environment variables for these tools to work with Synthalingua.

Vocal isolation (demucs) is built into Synthalingua itself and needs no separate Python
environment, so this script no longer installs Python embedded or demucs. Existing installs can
still be cleaned up with --uninstall.

Usage:
    python set_up_env.py                          # Basic setup (FFmpeg, yt-dlp, 7zr)
    python set_up_env.py --reinstall              # Reinstall basic tools
    python set_up_env.py --uninstall              # Remove a legacy Python embedded install (Windows only)
    python set_up_env.py --uninstall steam        # Same, without prompts (Windows only)
    python set_up_env.py --steam                  # Install basic tools without prompts (Windows only)
"""

import argparse
import os
import platform
import requests
import subprocess
import sys
import zipfile
import shutil
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm
from datetime import datetime


# Version number for the setup script.
VERSION_NUMBER = "0.0.54"
PORTABLE_PYTHON_VERSION = "3.12.10"
APP_NAME = "Synthalingua"
APP_VERSION = "1.2.6"

@dataclass
class Config:
    """Configuration settings for the environment setup."""
    def __init__(self, python_embedded_path: Optional[Path]):
        self.OS_TYPE = platform.system().lower()
        self.ASSETS_PATH: Path = Path.cwd() / 'downloaded_assets'
        self.FFMPEG_ROOT_PATH: Path = self.ASSETS_PATH / 'ffmpeg'
        self.PYTHON_EMBEDDED_PATH: Path = python_embedded_path if python_embedded_path else Path.cwd() / 'python_embedded'
        self.GET_PIP_URL = 'https://bootstrap.pypa.io/get-pip.py'
        
        # Platform-specific configurations
        if self.OS_TYPE == 'windows':
            self.FFMPEG_URL = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.09.26/yt-dlp_win.zip'
            self.SEVEN_ZIP_URL = 'https://www.7-zip.org/a/7zr.exe'
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_win'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg.7z')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_win.zip')
            self.SEVEN_ZIP_EXEC = '7zr.exe'
            self.CONFIG_FILE = 'ffmpeg_path.bat'
            self.PYTHON_EMBEDDED_ARCHIVE = str(self.ASSETS_PATH / 'python_embedded.zip')
        elif self.OS_TYPE == 'linux':
            self.FFMPEG_URL = 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.09.26/yt-dlp_linux'
            self.SEVEN_ZIP_URL = None  # Use system package manager
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_linux'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg-release-amd64-static.tar.xz')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_linux')
            self.SEVEN_ZIP_EXEC = 'p7zip'  # Use system p7zip
            self.CONFIG_FILE = 'ffmpeg_path.sh'
            self.PYTHON_EMBEDDED_ARCHIVE = str(self.ASSETS_PATH / 'python_embedded.tgz')
        elif self.OS_TYPE == 'darwin':  # macOS
            self.FFMPEG_URL = 'https://evermeet.cx/ffmpeg/getrelease/zip'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.09.26/yt-dlp_macos'
            self.SEVEN_ZIP_URL = None  # Use system package manager (brew)
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_macos'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg_macos.zip')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_macos')
            self.SEVEN_ZIP_EXEC = '7z'  # Use system 7z (via brew)
            self.CONFIG_FILE = 'ffmpeg_path.sh'
            self.PYTHON_EMBEDDED_ARCHIVE = str(self.ASSETS_PATH / 'python_embedded.tgz')
        else:
            raise OSError(f"Unsupported operating system: {self.OS_TYPE}")


class DownloadManager:
    """Handles file downloads and extractions."""

    @staticmethod
    def download_file(url: str, filename: str) -> None:
        """Download a file from a URL with progress display."""
        print(f"Downloading {Path(filename).name} from {url}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            with open(filename, 'wb') as file, tqdm(
                    desc=Path(filename).name,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    bar.update(len(chunk))

            print(f"{Path(filename).name} downloaded successfully.")
        except requests.exceptions.RequestException as e:
            print(f"\n Error downloading {Path(filename).name}: {e}")
            raise # Re-raise the exception to be caught by the caller
        except IOError as e:
            print(f"\n Error writing file {filename}: {e}")
            raise # Re-raise the exception to be caught by the caller
        except Exception as e:
            print(f"\n An unexpected error occurred during download: {e}")
            raise # Re-raise the exception to be caught by the caller

    @staticmethod
    def extract_7z(file_path: str, extract_to: str, seven_zip_exec: str) -> None:
        """Extract a .7z file using 7zr.exe or p7zip."""
        print(f"Extracting {file_path} with {seven_zip_exec}...")
        if platform.system().lower() == 'windows':
            subprocess.run([seven_zip_exec, 'x', file_path, f'-o{extract_to}'], check=True, capture_output=True)
        else:
            # Use p7zip on Linux/macOS
            subprocess.run(['7z', 'x', file_path, f'-o{extract_to}'], check=True, capture_output=True)
        print(f"{Path(file_path).name} extracted successfully.")

    @staticmethod
    def extract_zip(file_path: str, extract_to: str) -> None:
        """Extract a .zip file to a specified directory."""
        print(f"Extracting {file_path}...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"{Path(file_path).name} extracted successfully.")

    @staticmethod
    def extract_tar_xz(file_path: str, extract_to: str) -> None:
        """Extract a .tar.xz file to a specified directory."""
        print(f"Extracting {file_path}...")
        with tarfile.open(file_path, 'r:xz') as tar_ref:
            tar_ref.extractall(extract_to)
        print(f"{Path(file_path).name} extracted successfully.")

    @staticmethod
    def make_executable(file_path: str) -> None:
        """Make a file executable on Unix-like systems."""
        if platform.system().lower() != 'windows':
            os.chmod(file_path, 0o755)


class EnvironmentSetup:
    """Handles the setup of required tools and environment."""

    def __init__(self, python_embedded_path: Optional[Path]):
        self.config = Config(python_embedded_path)
        self.downloader = DownloadManager()
        
        # Bug report tracking variables
        self.ffmpeg_source = None  # 'custom' or 'downloaded'
        self.ytdlp_source = None  # 'custom' or 'downloaded'
        self.seven_zip_source = None  # 'system' or 'downloaded'
        self.os_type = self.config.OS_TYPE
        self.version = APP_VERSION
        self.datetime = datetime.now().isoformat()

    def find_ffmpeg_bin_path(self, root_path: Path) -> Optional[Path]:
        """Find the bin directory containing ffmpeg.exe."""
        print("Finding path for ffmpeg...")
        try:
            for ffmpeg_exe in root_path.rglob('ffmpeg.exe'):
                print(f"Found ffmpeg.exe at: {ffmpeg_exe}")
                return ffmpeg_exe.parent
            raise FileNotFoundError("No ffmpeg.exe found in the specified path.")
        except Exception as e:
            print(f"Error finding ffmpeg.exe: {e}")
            return None

    def setup_7zr(self, skip_prompts: bool = False) -> Optional[str]:
        """Set up 7zr.exe or p7zip depending on platform."""
        # Early detection of a local 7zr executable in the current working directory
        exe_name = '7zr.exe' if self.config.OS_TYPE == 'windows' else '7z'  # appropriate name for Linux/macOS
        candidate_path = Path.cwd() / exe_name
        if candidate_path.is_file():
            print("Found existing 7zr executable in working directory; using it.")
            self.seven_zip_source = 'downloaded'
            return str(candidate_path)
        # On Linux/macOS, check if p7zip is installed
        if self.config.OS_TYPE in ['linux', 'darwin']:
            try:
                subprocess.run(['7z'], capture_output=True, check=False)
                print("Found system p7zip installation.")
                self.seven_zip_source = 'system'
                return '7z'
            except FileNotFoundError:
                if skip_prompts:
                    print("p7zip not found. Please install it manually or ensure it's in PATH.")
                    return None
                print("p7zip not found. Please install it using your package manager:")
                if self.config.OS_TYPE == 'linux':
                    print("  Ubuntu/Debian: sudo apt-get install p7zip-full")
                    print("  CentOS/RHEL: sudo yum install p7zip")
                    print("  Arch: sudo pacman -S p7zip")
                elif self.config.OS_TYPE == 'darwin':
                    print("  macOS: brew install p7zip")

                # Ask user to install it
                input("Please install p7zip and press Enter to continue...")
                try:
                    subprocess.run(['7z'], capture_output=True, check=False)
                    print("p7zip installation verified.")
                    self.seven_zip_source = 'system'
                    return '7z'
                except FileNotFoundError:
                    print(" p7zip still not found. Please install it manually.")
                    return None

        # Windows-specific 7zr.exe handling
        self.config.ASSETS_PATH.mkdir(exist_ok=True)
        seven_zip_path = self.config.ASSETS_PATH / '7zr.exe'

        # If skip_prompts is True, just download fresh
        if skip_prompts:
            if seven_zip_path.exists():
                seven_zip_path.unlink()
            # Download 7zr.exe for Windows
            if self.config.SEVEN_ZIP_URL:
                try:
                    self.downloader.download_file(self.config.SEVEN_ZIP_URL, str(seven_zip_path))
                    self.seven_zip_source = 'downloaded'
                    return str(seven_zip_path)
                except requests.exceptions.RequestException as e:
                    print(f"\n Error downloading 7zr.exe: {e}")
                    print("Please check your internet connection.")
                    return None
            else:
                print(" No download URL configured for this platform.")
                return None

        # Check if 7zr.exe exists in downloaded_assets and ask user
        if seven_zip_path.exists():
            while True:
                reuse = input(f"Found existing 7zr.exe at {seven_zip_path}. Use it or download fresh? (use/download): ").strip().lower()
                if reuse in ("use", "u"):
                    print(f"Using existing 7zr.exe: {seven_zip_path}")
                    self.seven_zip_source = 'downloaded'
                    return str(seven_zip_path)
                elif reuse in ("download", "d"):
                    print("Downloading fresh 7zr.exe...")
                    try:
                        seven_zip_path.unlink()  # Remove old file first
                    except OSError as e:
                        print(f"Warning: Could not remove existing 7zr.exe: {e}")
                    break
                else:
                    print("Please answer 'use' or 'download'.")
        else:
            # Only ask about providing own version if no downloaded version exists
            while True:
                use_own_7zr = input("Do you want to provide your own version of 7zr.exe? (yes/no): ").strip().lower()
                if use_own_7zr in ('yes', 'y'):
                    sevens_zip_path = input("Please enter the full path to your 7zr.exe file: ").strip()
                    if os.path.isfile(sevens_zip_path):
                        print(f"Using provided 7zr.exe at {sevens_zip_path}.")
                        self.seven_zip_source = 'custom'
                        return sevens_zip_path
                    else:
                        print("The specified 7zr.exe file does not exist. Please try again.")
                elif use_own_7zr in ('no', 'n'):
                    print("Proceeding with download.")
                    break
                else:
                    print("Please answer 'yes' or 'no'.")

        # Download 7zr.exe for Windows
        if self.config.SEVEN_ZIP_URL:
            try:
                self.downloader.download_file(self.config.SEVEN_ZIP_URL, str(seven_zip_path))
                self.seven_zip_source = 'downloaded'
                return str(seven_zip_path)
            except requests.exceptions.RequestException as e:
                print(f"\n Error downloading 7zr.exe: {e}")
                print("Please check your internet connection or try providing your own 7zr.exe.")
                return None
        else:
            print(" No download URL configured for this platform.")
            return None

    def setup_ffmpeg(self, seven_zip_exec: str, force_download: bool = False, skip_prompts: bool = False) -> Optional[Path]:
        """Set up FFmpeg either from user input or download."""
        # If skip_prompts is True, just download fresh
        if skip_prompts:
            if self.config.FFMPEG_ROOT_PATH.is_dir():
                # Remove existing folder for fresh download
                shutil.rmtree(self.config.FFMPEG_ROOT_PATH)
            # Download and extract
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)
                self.downloader.download_file(self.config.FFMPEG_URL, self.config.FFMPEG_ARCHIVE)
                temp_extract_path = self.config.ASSETS_PATH / "_temp_ffmpeg"
                temp_extract_path.mkdir(exist_ok=True)

                # Choose extraction method based on file extension and platform
                if self.config.FFMPEG_ARCHIVE.endswith('.tar.xz'):
                    self.downloader.extract_tar_xz(self.config.FFMPEG_ARCHIVE, str(temp_extract_path))
                elif self.config.FFMPEG_ARCHIVE.endswith('.zip'):
                    self.downloader.extract_zip(self.config.FFMPEG_ARCHIVE, str(temp_extract_path))
                else:
                    # Use 7z for .7z files
                    self.downloader.extract_7z(self.config.FFMPEG_ARCHIVE, str(temp_extract_path), seven_zip_exec)

                print(f"{Path(self.config.FFMPEG_ARCHIVE).name} extracted successfully.")

                extracted_folders = [d for d in temp_extract_path.iterdir() if d.is_dir()]
                if not extracted_folders:
                    raise FileNotFoundError("Could not find the main folder inside the FFmpeg archive.")

                # Find the actual ffmpeg folder inside the extracted content
                ffmpeg_extracted_path = None
                for item in temp_extract_path.iterdir():
                    if item.is_dir() and "ffmpeg" in item.name.lower():
                        ffmpeg_extracted_path = item
                        break

                if not ffmpeg_extracted_path:
                     raise FileNotFoundError("Could not find the FFmpeg folder inside the extracted archive.")

                ffmpeg_extracted_path.rename(self.config.FFMPEG_ROOT_PATH)

                try:
                    shutil.rmtree(temp_extract_path)
                except OSError as e:
                    print(f"Warning: Could not remove temporary extraction folder: {e}")

                self.ffmpeg_source = 'downloaded'
                return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)
            except (requests.exceptions.RequestException, FileNotFoundError) as e:
                print(f"\n Error setting up FFmpeg: {e}")
                print("Please check your internet connection or try providing your own FFmpeg.")
                return None
            except subprocess.CalledProcessError as e:
                print(f"\n Error extracting FFmpeg archive: {e}")
                print(f"Command: {' '.join(e.cmd)}")
                print(f"Return Code: {e.returncode}")
                if e.stdout:
                    print(f"Stdout:\n{e.stdout.decode()}")
                if e.stderr:
                    print(f"Stderr:\n{e.stderr.decode()}")
                print("Please check the error messages and try again.")
                return None
            except Exception as e:
                print(f"\n An unexpected error occurred during FFmpeg setup: {e}")
                return None

        # Auto-detect existing FFmpeg installation
        if self.config.FFMPEG_ROOT_PATH.is_dir():
            ffmpeg_bin = self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)
            if ffmpeg_bin:
                print("Found existing FFmpeg installation; using it.")
                self.ffmpeg_source = 'downloaded'
                return ffmpeg_bin
        
        while True:
            use_own_ffmpeg = input("Do you already have FFmpeg installed and in your PATH? (yes/no): ").strip().lower()
            if use_own_ffmpeg in ('yes', 'y'):
                print("Assuming FFmpeg is available in your PATH.")
                self.ffmpeg_source = 'system'
                return None # Indicate using system FFmpeg
            elif use_own_ffmpeg in ('no', 'n'):
                break
            else:
                print("Please answer 'yes' or 'no'.")

        while True:
            provide_path = input("Do you want to provide the path to your FFmpeg bin folder? (yes/no): ").strip().lower()
            if provide_path in ('yes', 'y'):
                ffmpeg_path = input("Please enter the full path to your FFmpeg bin folder: ").strip()
                if os.path.isdir(ffmpeg_path):
                    ffmpeg_bin_path = self.find_ffmpeg_bin_path(Path(ffmpeg_path))
                    if ffmpeg_bin_path:
                        print(f"Using provided FFmpeg bin folder at {ffmpeg_bin_path}.")
                        self.ffmpeg_source = 'custom'
                        return ffmpeg_bin_path
                    else:
                        print("Could not find ffmpeg.exe in the specified folder. Please check the path and try again.")
                else:
                    print("The specified FFmpeg folder does not exist. Please try again.")
            elif provide_path in ('no', 'n'):
                print("Proceeding with download.")
                break
            else:
                print("Please answer 'yes' or 'no'.")

        # Only download/extract if force_download is True or the folder doesn't exist
        if force_download or not self.config.FFMPEG_ROOT_PATH.is_dir():
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)

                # Check if archive exists and ask user (only if not forcing download)
                ffmpeg_archive_path = Path(self.config.FFMPEG_ARCHIVE)
                if not force_download and ffmpeg_archive_path.exists():
                    while True:
                        reuse = input(f"Found existing FFmpeg archive at {self.config.FFMPEG_ARCHIVE}. Use it or download fresh? (use/download): ").strip().lower()
                        if reuse in ("use", "u"):
                            print(f"Using existing FFmpeg archive: {self.config.FFMPEG_ARCHIVE}")
                            break
                        elif reuse in ("download", "d"):
                            print("Downloading fresh FFmpeg archive...")
                            try:
                                ffmpeg_archive_path.unlink()  # Remove old archive first
                            except OSError as e:
                                print(f"Warning: Could not remove existing FFmpeg archive: {e}")
                            self.downloader.download_file(self.config.FFMPEG_URL, self.config.FFMPEG_ARCHIVE)
                            break
                        else:
                            print("Please answer 'use' or 'download'.")
                else:
                    self.downloader.download_file(self.config.FFMPEG_URL, self.config.FFMPEG_ARCHIVE)

                temp_extract_path = self.config.ASSETS_PATH / "_temp_ffmpeg"
                temp_extract_path.mkdir(exist_ok=True)
                
                # Choose extraction method based on file extension and platform
                if self.config.FFMPEG_ARCHIVE.endswith('.tar.xz'):
                    self.downloader.extract_tar_xz(self.config.FFMPEG_ARCHIVE, str(temp_extract_path))
                elif self.config.FFMPEG_ARCHIVE.endswith('.zip'):
                    self.downloader.extract_zip(self.config.FFMPEG_ARCHIVE, str(temp_extract_path))
                else:
                    # Use 7z for .7z files
                    self.downloader.extract_7z(self.config.FFMPEG_ARCHIVE, str(temp_extract_path), seven_zip_exec)
                
                print(f"{Path(self.config.FFMPEG_ARCHIVE).name} extracted successfully.")

                extracted_folders = [d for d in temp_extract_path.iterdir() if d.is_dir()]
                if not extracted_folders:
                    raise FileNotFoundError("Could not find the main folder inside the FFmpeg archive.")

                # Find the actual ffmpeg folder inside the extracted content
                ffmpeg_extracted_path = None
                for item in temp_extract_path.iterdir():
                    if item.is_dir() and "ffmpeg" in item.name.lower():
                        ffmpeg_extracted_path = item
                        break

                if not ffmpeg_extracted_path:
                     raise FileNotFoundError("Could not find the FFmpeg folder inside the extracted archive.")

                ffmpeg_extracted_path.rename(self.config.FFMPEG_ROOT_PATH)

                try:
                    shutil.rmtree(temp_extract_path)
                except OSError as e:
                    print(f"Warning: Could not remove temporary extraction folder: {e}")

                self.ffmpeg_source = 'downloaded'
                return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)
            except (requests.exceptions.RequestException, FileNotFoundError) as e:
                print(f"\n Error setting up FFmpeg: {e}")
                print("Please check your internet connection or try providing your own FFmpeg.")
                return None
            except subprocess.CalledProcessError as e:
                print(f"\n Error extracting FFmpeg archive: {e}")
                print(f"Command: {' '.join(e.cmd)}")
                print(f"Return Code: {e.returncode}")
                if e.stdout:
                    print(f"Stdout:\n{e.stdout.decode()}")
                if e.stderr:
                    print(f"Stderr:\n{e.stderr.decode()}")
                print("Please check the error messages and try again.")
                return None
            except Exception as e:
                print(f"\n An unexpected error occurred during FFmpeg setup: {e}")
                return None
        else:
            print("FFmpeg folder already exists, skipping download and extraction.")
            self.ffmpeg_source = 'downloaded'
            return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)

    def setup_ytdlp(self, force_download: bool = False, skip_prompts: bool = False) -> Optional[Path]:
        """Set up yt-dlp either from user input or download."""
        # If skip_prompts is True, just download fresh
        if skip_prompts:
            exe_name = 'yt-dlp.exe' if self.config.OS_TYPE == 'windows' else 'yt-dlp'
            if self.config.YTDLP_PATH.is_dir():
                # Remove existing folder for fresh download
                shutil.rmtree(self.config.YTDLP_PATH)
            # Download and extract
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)
                self.downloader.download_file(self.config.YTDLP_URL, self.config.YTDLP_ARCHIVE)
                self.config.YTDLP_PATH.mkdir(exist_ok=True)

                if self.config.OS_TYPE == 'windows':
                    # Windows: Extract zip file
                    self.downloader.extract_zip(self.config.YTDLP_ARCHIVE, str(self.config.YTDLP_PATH))
                    ytdlp_exe = self.config.YTDLP_PATH / 'yt-dlp.exe'
                else:
                    # Linux/macOS: Direct binary download, make executable
                    ytdlp_binary = self.config.YTDLP_PATH / 'yt-dlp'
                    # Copy the downloaded binary to the target location
                    shutil.copy2(self.config.YTDLP_ARCHIVE, str(ytdlp_binary))
                    self.downloader.make_executable(str(ytdlp_binary))
                    ytdlp_exe = ytdlp_binary

                # Keep the archive for reuse: os.remove(self.config.YTDLP_ARCHIVE)
                ytdlp_exe = self.config.YTDLP_PATH / 'yt-dlp.exe'
                if ytdlp_exe.exists():
                    try:
                        subprocess.run([str(ytdlp_exe), '-U'], check=True, capture_output=True)
                        print("yt-dlp updated to the latest version automatically.")
                    except subprocess.CalledProcessError as e:
                        print("\n Warning: Failed to auto‑update yt-dlp.")
                        # Optionally print error details for debugging
                self.ytdlp_source = 'downloaded'
                return self.config.YTDLP_PATH
            except (requests.exceptions.RequestException, zipfile.BadZipFile) as e:
                print(f"\n Error setting up yt-dlp: {e}")
                print("Please check your internet connection or try providing your own yt-dlp.")
                return None
            except Exception as e:
                print(f"\n An unexpected error occurred during yt-dlp setup: {e}")
                return None

        # Auto-detect existing yt-dlp installation
        exe_name = 'yt-dlp.exe' if self.config.OS_TYPE == 'windows' else 'yt-dlp'
        if self.config.YTDLP_PATH.is_dir():
            ytdlp_exe = self.config.YTDLP_PATH / exe_name
            if ytdlp_exe.exists():
                print("Found existing yt-dlp installation; using it.")
                self.ytdlp_source = 'downloaded'
                return self.config.YTDLP_PATH
        
        while True:
            use_own_ytdlp = input("Do you already have yt-dlp installed and in your PATH? (yes/no): ").strip().lower()
            if use_own_ytdlp in ('yes', 'y'):
                print("Assuming yt-dlp is available in your PATH.")
                self.ytdlp_source = 'system'
                return None # Indicate using system yt-dlp
            elif use_own_ytdlp in ('no', 'n'):
                break
            else:
                print("Please answer 'yes' or 'no'.")

        while True:
            provide_path = input("Do you want to provide the path to your yt-dlp folder? (yes/no): ").strip().lower()
            if provide_path in ('yes', 'y'):
                ytdlp_path = input("Please enter the full path to your yt-dlp folder: ").strip()
                if os.path.isdir(ytdlp_path):
                    ytdlp_exe = Path(ytdlp_path) / 'yt-dlp.exe'
                    if ytdlp_exe.exists():
                        print(f"Using provided yt-dlp folder at {ytdlp_path}.")
                        self.ytdlp_source = 'custom'
                        return Path(ytdlp_path)
                    else:
                        print("Could not find yt-dlp.exe in the specified folder. Please check the path and try again.")
                else:
                    print("The specified yt-dlp folder does not exist. Please try again.")
            elif provide_path in ('no', 'n'):
                print("Proceeding with download.")
                break
            else:
                print("Please answer 'yes' or 'no'.")

        # Only download/extract if force_download is True or the folder doesn't exist
        if force_download or not self.config.YTDLP_PATH.is_dir():
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)

                # Check if archive exists and ask user (only if not forcing download)
                ytdlp_archive_path = Path(self.config.YTDLP_ARCHIVE)
                if not force_download and ytdlp_archive_path.exists():
                    while True:
                        reuse = input(f"Found existing yt-dlp archive at {self.config.YTDLP_ARCHIVE}. Use it or download fresh? (use/download): ").strip().lower()
                        if reuse in ("use", "u"):
                            print(f"Using existing yt-dlp archive: {self.config.YTDLP_ARCHIVE}")
                            break
                        elif reuse in ("download", "d"):
                            print("Downloading fresh yt-dlp archive...")
                            try:
                                ytdlp_archive_path.unlink()  # Remove old archive first
                            except OSError as e:
                                print(f"Warning: Could not remove existing yt-dlp archive: {e}")
                            self.downloader.download_file(self.config.YTDLP_URL, self.config.YTDLP_ARCHIVE)
                            break
                        else:
                            print("Please answer 'use' or 'download'.")
                else:
                    self.downloader.download_file(self.config.YTDLP_URL, self.config.YTDLP_ARCHIVE)

                self.config.YTDLP_PATH.mkdir(exist_ok=True)
                
                if self.config.OS_TYPE == 'windows':
                    # Windows: Extract zip file
                    self.downloader.extract_zip(self.config.YTDLP_ARCHIVE, str(self.config.YTDLP_PATH))
                    ytdlp_exe = self.config.YTDLP_PATH / 'yt-dlp.exe'
                else:
                    # Linux/macOS: Direct binary download, make executable
                    ytdlp_binary = self.config.YTDLP_PATH / 'yt-dlp'
                    # Copy the downloaded binary to the target location
                    shutil.copy2(self.config.YTDLP_ARCHIVE, str(ytdlp_binary))
                    self.downloader.make_executable(str(ytdlp_binary))
                    ytdlp_exe = ytdlp_binary
                
                # Keep the archive for reuse: os.remove(self.config.YTDLP_ARCHIVE)
                ytdlp_exe = self.config.YTDLP_PATH / 'yt-dlp.exe'
                if ytdlp_exe.exists():
                    try:
                        subprocess.run([str(ytdlp_exe), '-U'], check=True, capture_output=True)
                        print("yt-dlp updated to the latest version automatically.")
                    except subprocess.CalledProcessError as e:
                        print("\n Warning: Failed to auto‑update yt-dlp.")
                        # Optionally print error details for debugging
                self.ytdlp_source = 'downloaded'
                return self.config.YTDLP_PATH
            except (requests.exceptions.RequestException, zipfile.BadZipFile) as e:
                print(f"\n Error setting up yt-dlp: {e}")
                print("Please check your internet connection or try providing your own yt-dlp.")
                return None
            except Exception as e:
                print(f"\n An unexpected error occurred during yt-dlp setup: {e}")
                return None
        else:
            print("yt-dlp folder already exists, skipping download.")
            self.ytdlp_source = 'downloaded'
            return self.config.YTDLP_PATH

    def _get_installed_packages(self) -> str:
        """Get the package list for the interpreter running this setup script."""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                                    capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            return "Unable to retrieve package list"

    def _create_bug_report_info(self) -> None:
        """Create a bug report info file with system and setup information."""
        installed_packages = self._get_installed_packages()
        
        bug_report_content = f"""Synthalingua Bug Report Information
=====================================

Setup Date/Time: {self.datetime}
Synthalingua Version: {self.version}
Operating System: {self.os_type}

Setup Configuration:
-------------------
FFmpeg Source: {self.ffmpeg_source or 'Not configured'}
yt-dlp Source: {self.ytdlp_source or 'Not configured'}
7-Zip Source: {self.seven_zip_source or 'Not configured'}

Installed Packages:
------------------
{installed_packages}

Setup Notes:
-----------
- This file was generated automatically during Synthalingua environment setup
- Include this information when reporting bugs or issues
"""

        with open('bugreportinfo.txt', 'w', encoding='utf-8') as f:
            f.write(bug_report_content)
        
        print("\nBug report information saved to 'bugreportinfo.txt'")

    def create_config_file(self, ffmpeg_path: Optional[Path], ytdlp_path: Optional[Path]) -> None:
        """Create the batch file (Windows) or shell script (Linux/macOS) for setting PATH environment variable."""
        path_parts = []
        if ffmpeg_path: path_parts.append(str(ffmpeg_path.resolve()))
        if ytdlp_path: path_parts.append(str(ytdlp_path.resolve()))

        if self.config.OS_TYPE == 'windows':
            # Windows batch file
            path_string = ";".join(path_parts)

            config_content = (
                f'@echo off\n'
                f'set "PATH={path_string};%PATH%"\n'
                f'echo FFmpeg and yt-dlp are available in this session.\n'
            )
        else:
            # Linux/macOS shell script
            path_string = ":".join(path_parts)

            config_content = (
                f'#!/bin/bash\n'
                f'export PATH="{path_string}:$PATH"\n'
                f'echo "FFmpeg and yt-dlp are available in this session."\n'
            )
        
        with open(self.config.CONFIG_FILE, 'w', encoding='utf-8') as file:
            file.write(config_content)
        
        # Make shell script executable on Unix-like systems
        if self.config.OS_TYPE in ['linux', 'darwin']:
            self.downloader.make_executable(self.config.CONFIG_FILE)
        
        print(f"\n{self.config.CONFIG_FILE} created with path settings.")

    def run(self, force_ffmpeg_download: bool = False, force_ytdlp_download: bool = False, reuse_ffmpeg: bool = False, reuse_ytdlp: bool = False, reuse_7zr: bool = False, skip_all_prompts: bool = False) -> None:
        """Run the environment setup process."""
        print("This script will download the following tools to 'downloaded_assets/' folder:")
        print("1. FFmpeg, 2. yt-dlp, 3. 7zr")
        print("\nAll installers and tools will be saved locally for reuse.")

        seven_zip_exec = self.setup_7zr(skip_prompts=skip_all_prompts or reuse_7zr)
        if not seven_zip_exec:
            print("Failed to set up 7zr.exe. Exiting...")
            return

        ffmpeg_path = self.setup_ffmpeg(seven_zip_exec, force_download=force_ffmpeg_download, skip_prompts=skip_all_prompts or reuse_ffmpeg)
        ytdlp_path = self.setup_ytdlp(force_download=force_ytdlp_download, skip_prompts=skip_all_prompts or reuse_ytdlp)

        self.create_config_file(ffmpeg_path, ytdlp_path)

        # Create bug report info file
        self._create_bug_report_info()


def main() -> None:
    """Main entry point of the script."""
    print(f"Synthalingua Environment Setup Version {VERSION_NUMBER}")
    parser = argparse.ArgumentParser(description="Synthalingua Environment Setup")
    parser.add_argument('--reinstall', action='store_true', help='Wipe all tool folders/files and redownload fresh')
    parser.add_argument('--using_vocal_isolation', action='store_true', help='Deprecated, vocal isolation is built into Synthalingua and needs no separate environment')
    parser.add_argument('--uninstall', nargs='?', const='', help='Remove a legacy Python embedded install. Add "steam" to skip prompts.')
    parser.add_argument('--steam', action='store_true', help='Skip all prompts and install the basic tools to the current folder.')
    args = parser.parse_args()

    # Handle uninstall first
    if args.uninstall is not None:
        if platform.system().lower() != 'windows':
            print("--uninstall is only supported on Windows.")
            return
        python_embedded_path = Path.cwd() / 'python_embedded'
        if not python_embedded_path.exists():
            print(f"Python embedded not found at {python_embedded_path}")
            return
        if args.uninstall == 'steam':
            print("Uninstalling Python embedded without prompt...")
            try:
                shutil.rmtree(python_embedded_path)
                print("Python embedded uninstalled successfully.")
            except Exception as e:
                print(f"Error uninstalling: {e}")
        else:
            confirm = input(f"Remove Python embedded at {python_embedded_path}? (yes/no): ").strip().lower()
            if confirm in ('yes', 'y'):
                try:
                    shutil.rmtree(python_embedded_path)
                    print("Python embedded uninstalled successfully.")
                except Exception as e:
                    print(f"Error uninstalling: {e}")
            else:
                print("Uninstall cancelled.")
        return

    # Check if this is a fresh install (no config file exists)
    config_exists = False
    if platform.system().lower() == 'windows':
        config_exists = os.path.exists("ffmpeg_path.bat")
    else:
        config_exists = os.path.exists("ffmpeg_path.sh")


    # Handle steam
    skip_all_prompts = False
    if args.steam:
        if platform.system().lower() != 'windows':
            print("--steam is only supported on Windows.")
            return
        print("Steam mode: Installing basic tools without prompts...")
        # Only reinstall if config file doesn't exist (fresh install)
        args.reinstall = not config_exists
        skip_all_prompts = True
        # For steam, always treat as not fresh to skip prompts

        # Early exit if config already exists in steam mode
        if config_exists:
            print("\nSteam mode: Config file already exists. Setup completed previously.")
            print("To reinstall, delete 'ffmpeg_path.bat' and run setup again.")
            return

    # Vocal isolation is built into Synthalingua now, so the flag that used to
    # install Python embedded and demucs is accepted but does nothing.
    if args.using_vocal_isolation:
        print("\n--using_vocal_isolation is no longer needed.")
        print("Vocal isolation ships inside Synthalingua and needs no separate Python environment.")
        print("Continuing with the basic tools setup (FFmpeg, yt-dlp, 7zr).")

    # Early exit if config already exists and no reinstall requested
    if config_exists and not args.reinstall and not skip_all_prompts:
        print("\nConfig file already exists. Use --reinstall to set up again.")
        return

    # Legacy Python embedded path, kept so older installs can be cleaned up on --reinstall
    python_embedded_path = Path.cwd() / 'python_embedded'
    cfg = Config(python_embedded_path)

    assets_to_check = [
        ('FFmpeg folder', cfg.FFMPEG_ROOT_PATH),
        ('FFmpeg archive', Path(cfg.FFMPEG_ARCHIVE)),
        ('yt-dlp folder', cfg.YTDLP_PATH),
        ('yt-dlp archive', Path(cfg.YTDLP_ARCHIVE)),
        ('7zr.exe', cfg.ASSETS_PATH / '7zr.exe'),
        ('Python embedded archive', Path(cfg.PYTHON_EMBEDDED_ARCHIVE)),
    ]

    assets_to_remove = []
    reuse_ffmpeg_folder = False
    reuse_ytdlp_folder = False
    reuse_7zr = False
    
    if args.reinstall:
        print("\n--reinstall specified: Removing all tool folders/files for a fresh setup...")
        # Add all existing assets to the removal list if --reinstall is used
        for name, path in assets_to_check:
            if path.exists():
                assets_to_remove.append(path)
        # Remove legacy Python embedded installs, they are no longer used
        if python_embedded_path.exists():
            assets_to_remove.append(python_embedded_path)
            print(f"Found a legacy Python embedded install, it will be removed: {python_embedded_path}")
        # Automatic detection of existing assets (no interactive prompts)
        print("\nChecking for existing assets...")
        for name, path in assets_to_check:
            if path.exists():
                # Set reuse flags based on the asset type
                if name == 'FFmpeg folder':
                    reuse_ffmpeg_folder = True
                elif name == 'yt-dlp folder':
                    reuse_ytdlp_folder = True
                elif name == '7zr.exe':
                    reuse_7zr = True
                # Archives are left untouched; they will be downloaded if needed later
            # If the asset does not exist, do nothing – download will occur later

    if assets_to_remove:
        print("\nRemoving selected tool folders/files...")
        import shutil
        for path in assets_to_remove:
            if path.exists():
                if path.is_dir():
                    print(f"Attempting to remove folder: {path}")
                    try:
                        shutil.rmtree(path)
                        print(f"Successfully removed folder: {path}")
                    except OSError as e:
                        print(f" Error removing folder {path}: {e}")
                        print("Please ensure you have the necessary permissions to delete this folder.")
                else:
                    print(f"Attempting to remove file: {path}")
                    try:
                        path.unlink()
                        print(f"Successfully removed file: {path}")
                    except OSError as e:
                        print(f" Error removing file {path}: {e}")
                        print("Please ensure you have the necessary permissions to delete this file.")
        print("Finished attempting to remove selected tool folders/files.")

    # Always include config file for removal if it exists
    if platform.system().lower() == 'windows':
        config_file_path = Path.cwd() / 'ffmpeg_path.bat'
    else:
        config_file_path = Path.cwd() / 'ffmpeg_path.sh'
    
    if config_file_path.exists():
        print(f"Attempting to remove existing config file: {config_file_path}")
        try:
            config_file_path.unlink()
            print(f"Successfully removed config file: {config_file_path}")
        except OSError as e:
            print(f" Error removing config file {config_file_path}: {e}")
            print("Please ensure you have the necessary permissions to delete this file.")

    # Determine if FFmpeg and yt-dlp should be force downloaded
    force_ffmpeg = cfg.FFMPEG_ROOT_PATH in assets_to_remove
    force_ytdlp = cfg.YTDLP_PATH in assets_to_remove

    setup = EnvironmentSetup(python_embedded_path)
    setup.run(force_ffmpeg_download=force_ffmpeg, force_ytdlp_download=force_ytdlp, reuse_ffmpeg=reuse_ffmpeg_folder, reuse_ytdlp=reuse_ytdlp_folder, reuse_7zr=reuse_7zr, skip_all_prompts=skip_all_prompts)

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()
