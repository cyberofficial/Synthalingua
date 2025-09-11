import argparse
"""Environment setup script for Synthalingua.

This script handles the installation and configuration of required tools:
- FFmpeg: A multimedia framework for processing audio and video files
- yt-dlp: A video downloader for YouTube and other sites
- 7zr/p7zip: A tool for extracting .7z files
- Miniconda: Python environment manager for creating isolated environments (optional with --using_vocal_isolation)
- Demucs: Audio source separation library for vocal isolation (optional with --using_vocal_isolation)

The script will create a batch file (Windows) or shell script (Linux/macOS) that sets up the 
necessary PATH environment variables for these tools to work with Synthalingua. For vocal 
isolation features, use the --using_vocal_isolation flag to download and install Miniconda, 
create a data_whisper environment with Python 3.12, and install the demucs package.

Usage:
    python set_up_env.py                          # Basic setup (FFmpeg, yt-dlp, 7zr)
    python set_up_env.py --using_vocal_isolation  # Include vocal isolation setup
    python set_up_env.py --reinstall              # Reinstall basic tools
    python set_up_env.py --reinstall --using_vocal_isolation  # Reinstall everything
"""

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


# Version number for the setup script.
VERSION_NUMBER = "0.0.48"

@dataclass
class Config:
    """Configuration settings for the environment setup."""
    def __init__(self, miniconda_path: Path):
        self.OS_TYPE = platform.system().lower()
        self.ASSETS_PATH: Path = Path.cwd() / 'downloaded_assets'
        self.FFMPEG_ROOT_PATH: Path = self.ASSETS_PATH / 'ffmpeg'
        self.MINICONDA_PATH: Path = miniconda_path
        
        # Platform-specific configurations
        if self.OS_TYPE == 'windows':
            self.FFMPEG_URL = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.30/yt-dlp_win.zip'
            self.SEVEN_ZIP_URL = 'https://www.7-zip.org/a/7zr.exe'
            self.MINICONDA_URL = 'https://repo.anaconda.com/miniconda/Miniconda3-py312_25.5.1-0-Windows-x86_64.exe'
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_win'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg.7z')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_win.zip')
            self.SEVEN_ZIP_EXEC = '7zr.exe'
            self.CONFIG_FILE = 'ffmpeg_path.bat'
            self.MINICONDA_INSTALLER = 'miniconda_installer.exe'
        elif self.OS_TYPE == 'linux':
            self.FFMPEG_URL = 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.30/yt-dlp_linux'
            self.SEVEN_ZIP_URL = None  # Use system package manager
            self.MINICONDA_URL = 'https://repo.anaconda.com/miniconda/Miniconda3-py312_25.5.1-0-Linux-x86_64.sh'
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_linux'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg-release-amd64-static.tar.xz')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_linux')
            self.SEVEN_ZIP_EXEC = 'p7zip'  # Use system p7zip
            self.CONFIG_FILE = 'ffmpeg_path.sh'
            self.MINICONDA_INSTALLER = 'miniconda_installer.sh'
        elif self.OS_TYPE == 'darwin':  # macOS
            self.FFMPEG_URL = 'https://evermeet.cx/ffmpeg/getrelease/zip'
            self.YTDLP_URL = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.30/yt-dlp_macos'
            self.SEVEN_ZIP_URL = None  # Use system package manager (brew)
            self.MINICONDA_URL = 'https://repo.anaconda.com/miniconda/Miniconda3-py312_25.5.1-0-MacOSX-x86_64.sh'
            self.YTDLP_PATH = self.ASSETS_PATH / 'yt-dlp_macos'
            self.FFMPEG_ARCHIVE = str(self.ASSETS_PATH / 'ffmpeg_macos.zip')
            self.YTDLP_ARCHIVE = str(self.ASSETS_PATH / 'yt-dlp_macos')
            self.SEVEN_ZIP_EXEC = '7z'  # Use system 7z (via brew)
            self.CONFIG_FILE = 'ffmpeg_path.sh'
            self.MINICONDA_INSTALLER = 'miniconda_installer.sh'
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
            print(f"\n❌ Error downloading {Path(filename).name}: {e}")
            raise # Re-raise the exception to be caught by the caller
        except IOError as e:
            print(f"\n❌ Error writing file {filename}: {e}")
            raise # Re-raise the exception to be caught by the caller
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during download: {e}")
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

    def __init__(self, miniconda_path: Path):
        self.config = Config(miniconda_path)
        self.downloader = DownloadManager()
        self.use_system_python = False  # Default to Miniconda

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

    def setup_7zr(self) -> Optional[str]:
        """Set up 7zr.exe or p7zip depending on platform."""
        # On Linux/macOS, check if p7zip is installed
        if self.config.OS_TYPE in ['linux', 'darwin']:
            try:
                subprocess.run(['7z'], capture_output=True, check=False)
                print("Found system p7zip installation.")
                return '7z'
            except FileNotFoundError:
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
                    return '7z'
                except FileNotFoundError:
                    print("❌ p7zip still not found. Please install it manually.")
                    return None
        
        # Windows-specific 7zr.exe handling
        self.config.ASSETS_PATH.mkdir(exist_ok=True)
        seven_zip_path = self.config.ASSETS_PATH / '7zr.exe'

        # Check if 7zr.exe exists in downloaded_assets and ask user
        if seven_zip_path.exists():
            while True:
                reuse = input(f"Found existing 7zr.exe at {seven_zip_path}. Use it or download fresh? (use/download): ").strip().lower()
                if reuse in ("use", "u"):
                    print(f"Using existing 7zr.exe: {seven_zip_path}")
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
                return str(seven_zip_path)
            except requests.exceptions.RequestException as e:
                print(f"\n❌ Error downloading 7zr.exe: {e}")
                print("Please check your internet connection or try providing your own 7zr.exe.")
                return None
        else:
            print("❌ No download URL configured for this platform.")
            return None

    def setup_ffmpeg(self, seven_zip_exec: str, force_download: bool = False) -> Optional[Path]:
        """Set up FFmpeg either from user input or download."""
        while True:
            use_own_ffmpeg = input("Do you already have FFmpeg installed and in your PATH? (yes/no): ").strip().lower()
            if use_own_ffmpeg in ('yes', 'y'):
                print("Assuming FFmpeg is available in your PATH.")
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

                return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)
            except (requests.exceptions.RequestException, FileNotFoundError) as e:
                print(f"\n❌ Error setting up FFmpeg: {e}")
                print("Please check your internet connection or try providing your own FFmpeg.")
                return None
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Error extracting FFmpeg archive: {e}")
                print(f"Command: {' '.join(e.cmd)}")
                print(f"Return Code: {e.returncode}")
                if e.stdout:
                    print(f"Stdout:\n{e.stdout.decode()}")
                if e.stderr:
                    print(f"Stderr:\n{e.stderr.decode()}")
                print("Please check the error messages and try again.")
                return None
            except Exception as e:
                print(f"\n❌ An unexpected error occurred during FFmpeg setup: {e}")
                return None
        else:
            print("FFmpeg folder already exists, skipping download and extraction.")
            return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)

    def setup_ytdlp(self, force_download: bool = False) -> Optional[Path]:
        """Set up yt-dlp either from user input or download."""
        while True:
            use_own_ytdlp = input("Do you already have yt-dlp installed and in your PATH? (yes/no): ").strip().lower()
            if use_own_ytdlp in ('yes', 'y'):
                print("Assuming yt-dlp is available in your PATH.")
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
                    while True:
                        update_choice = input("Would you like to check for yt-dlp updates now? (yes/no): ").strip().lower()
                        if update_choice in ("yes", "y"):
                            print("Updating yt-dlp to the latest version...")
                            try:
                                # Use capture_output=True for better error reporting
                                subprocess.run([str(ytdlp_exe), '-U'], check=True, capture_output=True)
                                print("yt-dlp updated to the latest version.")
                            except subprocess.CalledProcessError as e:
                                print(f"\n❌ Warning: Failed to auto-update yt-dlp: {e}")
                                print(f"Command: {' '.join(e.cmd)}")
                                print(f"Return Code: {e.returncode}")
                                if e.stdout:
                                    print(f"Stdout:\n{e.stdout.decode()}")
                                if e.stderr:
                                    print(f"Stderr:\n{e.stderr.decode()}")
                            except FileNotFoundError as e:
                                print(f"\n❌ Warning: Could not find yt-dlp executable to update: {e}")
                            except Exception as e:
                                print(f"\n❌ An unexpected error occurred during yt-dlp update: {e}")
                            break
                        elif update_choice in ("no", "n"):
                            print("Skipping yt-dlp update check.")
                            break
                        else:
                            print("Please answer 'yes' or 'no'.")
                return self.config.YTDLP_PATH
            except (requests.exceptions.RequestException, zipfile.BadZipFile) as e:
                print(f"\n❌ Error setting up yt-dlp: {e}")
                print("Please check your internet connection or try providing your own yt-dlp.")
                return None
            except Exception as e:
                print(f"\n❌ An unexpected error occurred during yt-dlp setup: {e}")
                return None
        else:
            print("yt-dlp folder already exists, skipping download.")
            return self.config.YTDLP_PATH

    def check_miniconda_installed(self) -> bool:
        """Check if miniconda is installed and conda executable is available."""
        if not (self.config.MINICONDA_PATH.exists() and self.config.MINICONDA_PATH.is_dir()):
            return False
        
        # Check if conda executable exists
        possible_paths = [
            self.config.MINICONDA_PATH / 'Scripts' / 'conda.exe', 
            self.config.MINICONDA_PATH / 'condabin' / 'conda.bat'
        ]
        for path in possible_paths:
            if path.exists():
                return True
        return False

    def download_miniconda(self) -> Optional[str]:
        """Download miniconda installer for the current platform."""
        self.config.ASSETS_PATH.mkdir(exist_ok=True)
        installer_path = self.config.ASSETS_PATH / self.config.MINICONDA_INSTALLER
        
        # Check if installer exists and ask user
        if installer_path.exists():
            while True:
                reuse = input(f"Found existing Miniconda installer. Use it or download fresh? (use/download): ").strip().lower()
                if reuse in ("use", "u"):
                    print(f"Using existing Miniconda installer: {installer_path}")
                    return str(installer_path)
                elif reuse in ("download", "d"):
                    print("Downloading fresh Miniconda installer...")
                    installer_path.unlink()  # Remove old installer first
                    break
                else:
                    print("Please answer 'use' or 'download'.")
        
        url = self.config.MINICONDA_URL
        print(f"Using miniconda installer: {url.split('/')[-1]}")
        try:
            self.downloader.download_file(url, str(installer_path))
            if self.config.OS_TYPE in ['linux', 'darwin']:
                # Make shell script executable
                self.downloader.make_executable(str(installer_path))
            return str(installer_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download miniconda: {e}")
            return None

    def install_miniconda(self, installer_path: str) -> bool:
        """Install miniconda using the downloaded installer."""
        miniconda_install_path = str(self.config.MINICONDA_PATH)

        if self.config.OS_TYPE == 'windows':
            print("Installing miniconda for Windows...")
            print(f"Installation path: {miniconda_install_path}")
            # Ensure parent directories exist
            try:
                Path(miniconda_install_path).parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"\n❌ Error creating parent directory for Miniconda installation: {e}")
                print(f"Please ensure you have write permissions to {Path(miniconda_install_path).parent}.")
                return False
            
            env = os.environ.copy()
            env['CONDA_YES'] = 'true'
            env['CONDA_ALWAYS_YES'] = 'true'

            command = [
                installer_path,
                '/InstallationType=JustMe',
                '/RegisterPython=0',
                '/AddToPath=0',
                '/S',
                f'/D={miniconda_install_path}'
            ]
        else:
            # Linux/macOS installation
            print(f"Installing miniconda for {self.config.OS_TYPE}...")
            print(f"Installation path: {miniconda_install_path}")
            # Ensure parent directories exist
            try:
                Path(miniconda_install_path).parent.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"\n❌ Error creating parent directory for Miniconda installation: {e}")
                print(f"Please ensure you have write permissions to {Path(miniconda_install_path).parent}.")
                return False
            
            env = os.environ.copy()
            env['CONDA_YES'] = 'true'
            env['CONDA_ALWAYS_YES'] = 'true'

            command = [
                'bash', installer_path, '-b', '-p', miniconda_install_path
            ]

        try:
            # Capture stdout and stderr for better error reporting
            result = subprocess.run(command, check=True, capture_output=True, text=True, env=env)
            print("Miniconda installation completed.")
            if Path(miniconda_install_path).exists():
                print(f"✅ Miniconda successfully installed to: {Path(miniconda_install_path).resolve()}")
                return True
            else:
                print(f"❌ ERROR: Miniconda installation directory not found at: {Path(miniconda_install_path).resolve()}")
                print("Please check the installer output for details.")
                return False
        except FileNotFoundError:
             print(f"\n❌ Error: Miniconda installer not found at {installer_path}.")
             print("Please ensure the installer file exists.")
             return False
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error installing miniconda. Exit code: {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            if e.stdout:
                print(f"Installer stdout:\n{e.stdout}")
            if e.stderr:
                print(f"Installer stderr:\n{e.stderr}")
            print("\n💡 Suggestions:")
            if self.config.OS_TYPE == 'windows':
                print("   1. Check for leftover Miniconda/Anaconda installations or registry keys.")
            else:
                print("   1. Check if bash is available and the installer is executable.")
            print(f"   2. Make sure you have write permissions to {Path(miniconda_install_path).parent}.")
            return False
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during Miniconda installation: {e}")
            return False

    def _get_conda_exe(self) -> Optional[str]:
        """Find the conda executable for the current platform."""
        if not self.check_miniconda_installed(): return None
        
        if self.config.OS_TYPE == 'windows':
            possible_paths = [
                self.config.MINICONDA_PATH / 'Scripts' / 'conda.exe', 
                self.config.MINICONDA_PATH / 'condabin' / 'conda.bat'
            ]
        else:
            # Linux/macOS paths
            possible_paths = [
                self.config.MINICONDA_PATH / 'bin' / 'conda',
                self.config.MINICONDA_PATH / 'condabin' / 'conda'
            ]
        
        for path in possible_paths:
            if path.exists():
                return str(path)
        print(f"Error: conda executable not found in {self.config.MINICONDA_PATH}")
        return None

    def create_data_whisper_env(self) -> bool:
        """Create the data_whisper environment using miniconda (in the default envs folder)."""
        import re
        conda_exe = self._get_conda_exe()
        if not conda_exe:
            print("❌ Error: conda executable not found. Cannot create environment.")
            return False
        def try_create():
            return subprocess.run([conda_exe, 'create', '-n', 'data_whisper', 'python=3.12', '-y'], check=True, capture_output=True, text=True)
        try:
            print("Creating data_whisper environment with Python 3.12...")
            result = try_create()
            print("data_whisper environment created successfully.")
            return True
        except FileNotFoundError:
            print(f"\n❌ Error: conda executable not found at {conda_exe}.")
            print("Please ensure Miniconda is installed correctly and the path is accessible.")
            return False
        except subprocess.CalledProcessError as e:
            stderr = e.stderr or ""
            if "Terms of Service have not been accepted" in stderr:
                # Parse channels from error message
                print("Detected Conda ToS acceptance error. Attempting to accept ToS for required channels...")
                channels = []
                # Find all lines with a bullet and a URL
                for line in stderr.splitlines():
                    m = re.search(r"\u2022\s*(https?://\S+)", line)
                    if m:
                        channels.append(m.group(1))
                if not channels:
                    print("Could not parse channels from error message. Please accept ToS manually.")
                    print(f"To accept, run (replace CHANNEL with the URL):\n    \"{conda_exe}\" tos accept --override-channels --channel CHANNEL")
                    return False
                # Try to accept ToS for each channel
                all_accepted = True
                for ch in channels:
                    print(f"Accepting ToS for channel: {ch}")
                    try:
                        subprocess.run([conda_exe, 'tos', 'accept', '--override-channels', '--channel', ch], check=True, capture_output=True, text=True)
                        print(f"Accepted ToS for {ch}")
                    except subprocess.CalledProcessError as e2:
                        print(f"Failed to accept ToS for {ch}.\nCommand: {' '.join(e2.cmd)}\nStderr:\n{e2.stderr}")
                        all_accepted = False
                if all_accepted:
                    print("All ToS accepted. Retrying environment creation...")
                    try:
                        result = try_create()
                        print("data_whisper environment created successfully after ToS acceptance.")
                        return True
                    except subprocess.CalledProcessError as e3:
                        print(f"\n❌ Error creating data_whisper environment after ToS acceptance. Exit code: {e3.returncode}")
                        print(f"Command: {' '.join(e3.cmd)}")
                        if e3.stdout:
                            print(f"Stdout:\n{e3.stdout}")
                        if e3.stderr:
                            print(f"Stderr:\n{e3.stderr}")
                        print("\n💡 Suggestions:")
                        print("   1. Check if an environment with the same name already exists.")
                        print("   2. Check your internet connection.")
                        return False
                else:
                    print("Some ToS could not be accepted automatically. Please run the following commands manually:")
                    for ch in channels:
                        print(f'    "{conda_exe}" tos accept --override-channels --channel {ch}')
                    print("Then re-run the setup script.")
                    return False
            print(f"\n❌ Error creating data_whisper environment. Exit code: {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            if e.stdout:
                print(f"Stdout:\n{e.stdout}")
            if e.stderr:
                print(f"Stderr:\n{e.stderr}")
            print("\n💡 Suggestions:")
            print("   1. Check if an environment with the same name already exists.")
            print("   2. Check your internet connection.")
            return False
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during environment creation: {e}")
            return False

    def install_demucs_in_env(self) -> bool:
        """Install demucs package in the data_whisper environment with appropriate PyTorch version."""
        conda_exe = self._get_conda_exe()
        if not conda_exe:
            print("❌ Error: conda executable not found. Cannot install packages.")
            return False

        # Ask user about their preferred device for Synthalingua processing
        print("\nSynthalingua supports CPU, GPU (CUDA), and AMD GPU (ROCm) processing.")
        print("This affects both transcription and vocal isolation (demucs) performance.")
        
        if self.config.OS_TYPE == 'windows':
            print("Available options: cpu, cuda")
            while True:
                device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda): ").strip().lower()
                if device_choice in ("cuda", "gpu"):
                    use_cuda = True
                    use_rocm = False
                    print("CUDA selected - This will install GPU-accelerated PyTorch for faster processing.")
                    break
                elif device_choice in ("cpu"):
                    use_cuda = False
                    use_rocm = False
                    print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                    break
                else:
                    print("Please answer 'cpu' or 'cuda'.")
        else:
            # Linux/macOS - ROCm only supported on Linux
            if self.config.OS_TYPE == 'linux':
                print("Available options: cpu, cuda, rocm")
                while True:
                    device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda/rocm): ").strip().lower()
                    if device_choice in ("cuda", "gpu"):
                        use_cuda = True
                        use_rocm = False
                        print("CUDA selected - This will install GPU-accelerated PyTorch for faster processing.")
                        break
                    elif device_choice in ("rocm", "amd"):
                        use_cuda = False
                        use_rocm = True
                        print("ROCm selected - This will install AMD GPU-accelerated PyTorch for faster processing.")
                        break
                    elif device_choice in ("cpu"):
                        use_cuda = False
                        use_rocm = False
                        print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                        break
                    else:
                        print("Please answer 'cpu', 'cuda', or 'rocm'.")
            else:
                # macOS - no ROCm support
                print("Available options: cpu, cuda (may not work on Apple Silicon)")
                while True:
                    device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda): ").strip().lower()
                    if device_choice in ("cuda", "gpu"):
                        use_cuda = True
                        use_rocm = False
                        print("CUDA selected - This will install GPU-accelerated PyTorch (may not work on Apple Silicon).")
                        break
                    elif device_choice in ("cpu"):
                        use_cuda = False
                        use_rocm = False
                        print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                        break
                    else:
                        print("Please answer 'cpu' or 'cuda'.")

        try:
            if use_cuda:
                print("Installing CUDA-enabled PyTorch in data_whisper environment...")
                print("This may take several minutes depending on your internet connection...")
                print("You should see pip download progress below:")
                sys.stdout.flush()
                # Capture stdout and stderr for better error reporting
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'torch', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cu128'], check=True, capture_output=True, text=True)
                print("CUDA PyTorch installation completed successfully.")
            elif use_rocm:
                print("Installing ROCm-enabled PyTorch in data_whisper environment...")
                print("This may take several minutes depending on your internet connection...")
                print("You should see pip download progress below:")
                sys.stdout.flush()
                # Capture stdout and stderr for better error reporting
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'torch', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/rocm6.4'], check=True, capture_output=True, text=True)
                print("ROCm PyTorch installation completed successfully.")
            else:
                print("Installing CPU-only PyTorch in data_whisper environment...")
                print("This may take several minutes depending on your internet connection...")
                print("You should see pip download progress below:")
                sys.stdout.flush()
                # Capture stdout and stderr for better error reporting
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'torch', 'torchaudio'], check=True, capture_output=True, text=True)
                print("CPU PyTorch installation completed successfully.")

            print("Installing demucs and diffq in data_whisper environment...")
            sys.stdout.flush()
            # Capture stdout and stderr for better error reporting
            result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', '-U', 'demucs', 'diffq', 'Cython'], check=True, capture_output=True, text=True)
            print("Demucs and diffq installation completed successfully.")

            print("Installing additional audio backend support for demucs...")
            sys.stdout.flush()
            # Install conda audio packages first for better compatibility
            # Capture stdout and stderr for better error reporting
            result = subprocess.run([conda_exe, 'install', '-n', 'data_whisper', '-c', 'conda-forge', 'libsndfile', 'ffmpeg', '-y'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"\n⚠️  Warning: Could not install conda audio packages. Exit code: {result.returncode}")
                print(f"Command: {' '.join(result.args)}")
                if result.stdout:
                    print(f"Stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"Stderr:\n{result.stderr}")
            else:
                 print("Conda audio packages installed successfully.")

            # Install pip audio packages
            # Capture stdout and stderr for better error reporting
            result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'soundfile', 'librosa'], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"\n⚠️  Warning: Could not install additional audio backends. Exit code: {result.returncode}")
                print(f"Command: {' '.join(result.args)}")
                if result.stdout:
                    print(f"Stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"Stderr:\n{result.stderr}")
                print("Demucs may have audio backend issues.")
            else:
                print("Additional audio backend support installed successfully.")

            if use_cuda:
                print("Verifying CUDA availability...")
                # Capture stdout and stderr for better error reporting
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'python', '-c', 'import torch; print(f"CUDA available: {torch.cuda.is_available()}")'], check=True, capture_output=True, text=True)
                print(result.stdout.strip())
                if "CUDA available: False" in result.stdout:
                    print("⚠️  Warning: CUDA not detected. You may need to:")
                    print("   - Install NVIDIA drivers")
                    print("   - Install CUDA toolkit")
                    print("   - Use --device cpu when running Synthalingua")
                else:
                    print("✅ CUDA detected! Use --device cuda when running Synthalingua for best performance.")
            else:
                print("ℹ️  PyTorch configured for CPU processing.")
                print("   Use --device cpu when running Synthalingua (default behavior).")

            return True
        except FileNotFoundError:
            print(f"\n❌ Error: conda executable not found at {conda_exe}. Cannot install packages.")
            print("Please ensure Miniconda is installed correctly and the path is accessible.")
            return False
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error installing packages in data_whisper environment. Exit code: {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            if e.stdout:
                print(f"Stdout:\n{e.stdout}")
            if e.stderr:
                print(f"Stderr:\n{e.stderr}")
            print("Please check the error messages and your internet connection.")
            return False
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during package installation: {e}")
            return False

    def install_demucs_system_python(self) -> bool:
        """Install demucs package using system Python with appropriate PyTorch version."""
        print("\nSetting up vocal isolation with system Python...")
        
        # Ask user about their preferred device for Synthalingua processing
        print("\nSynthalingua supports CPU, GPU (CUDA), and AMD GPU (ROCm) processing.")
        print("This affects both transcription and vocal isolation (demucs) performance.")
        
        if self.config.OS_TYPE == 'windows':
            print("Available options: cpu, cuda")
            while True:
                device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda): ").strip().lower()
                if device_choice in ("cuda", "gpu"):
                    use_cuda = True
                    use_rocm = False
                    print("CUDA selected - This will install GPU-accelerated PyTorch for faster processing.")
                    break
                elif device_choice in ("cpu"):
                    use_cuda = False
                    use_rocm = False
                    print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                    break
                else:
                    print("Please answer 'cpu' or 'cuda'.")
        elif self.config.OS_TYPE == 'linux':
            print("Available options: cpu, cuda, rocm")
            while True:
                device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda/rocm): ").strip().lower()
                if device_choice in ("cuda", "gpu"):
                    use_cuda = True
                    use_rocm = False
                    print("CUDA selected - This will install GPU-accelerated PyTorch for faster processing.")
                    break
                elif device_choice in ("rocm", "amd"):
                    use_cuda = False
                    use_rocm = True
                    print("ROCm selected - This will install AMD GPU-accelerated PyTorch for faster processing.")
                    break
                elif device_choice in ("cpu"):
                    use_cuda = False
                    use_rocm = False
                    print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                    break
                else:
                    print("Please answer 'cpu', 'cuda', or 'rocm'.")
        else:
            # macOS - no ROCm support
            print("Available options: cpu, cuda (may not work on Apple Silicon)")
            while True:
                device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda): ").strip().lower()
                if device_choice in ("cuda", "gpu"):
                    use_cuda = True
                    use_rocm = False
                    print("CUDA selected - This will install GPU-accelerated PyTorch (may not work on Apple Silicon).")
                    break
                elif device_choice in ("cpu"):
                    use_cuda = False
                    use_rocm = False
                    print("CPU selected - This will install CPU-only PyTorch (slower but more compatible). Friendly reminder that vocal isolation is very slow on CPU.")
                    break
                else:
                    print("Please answer 'cpu' or 'cuda'.")

        try:
            # Install PyTorch first
            if use_cuda:
                print("Installing CUDA-enabled PyTorch...")
                print("This may take several minutes depending on your internet connection...")
                sys.stdout.flush()
                result = subprocess.run(['pip', 'install', 'torch', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cu128'], check=True, capture_output=True, text=True)
                print("CUDA PyTorch installation completed successfully.")
            elif use_rocm:
                print("Installing ROCm-enabled PyTorch...")
                print("This may take several minutes depending on your internet connection...")
                sys.stdout.flush()
                result = subprocess.run(['pip', 'install', 'torch', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/rocm6.4'], check=True, capture_output=True, text=True)
                print("ROCm PyTorch installation completed successfully.")
            else:
                print("Installing CPU-only PyTorch...")
                print("This may take several minutes depending on your internet connection...")
                sys.stdout.flush()
                result = subprocess.run(['pip', 'install', 'torch', 'torchaudio'], check=True, capture_output=True, text=True)
                print("CPU PyTorch installation completed successfully.")

            # Install demucs and dependencies
            print("Installing demucs and dependencies...")
            sys.stdout.flush()
            result = subprocess.run(['pip', 'install', '-U', 'demucs', 'diffq', 'Cython'], check=True, capture_output=True, text=True)
            print("Demucs installation completed successfully.")

            # Install additional audio libraries
            print("Installing additional audio support libraries...")
            sys.stdout.flush()
            result = subprocess.run(['pip', 'install', 'soundfile', 'librosa'], check=True, capture_output=True, text=True)
            print("Audio libraries installation completed successfully.")

            print("✅ Vocal isolation setup with system Python completed successfully!")
            return True

        except FileNotFoundError:
            print("\n❌ Error: pip not found. Please ensure pip is installed and available in your PATH.")
            print("You may need to install it with: sudo apt-get install python3-pip (Ubuntu/Debian)")
            return False
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Error installing packages. Exit code: {e.returncode}")
            print(f"Command: {' '.join(e.cmd)}")
            if e.stdout:
                print(f"Stdout:\n{e.stdout}")
            if e.stderr:
                print(f"Stderr:\n{e.stderr}")
            print("\n💡 Suggestions:")
            print("   1. Check your internet connection")
            print("   2. Make sure you have sufficient disk space")
            print("   3. Try upgrading pip: pip install --upgrade pip")
            print("   4. Consider using a virtual environment if you have package conflicts")
            return False
        except Exception as e:
            print(f"\n❌ An unexpected error occurred during package installation: {e}")
            return False

    def setup_vocal_isolation(self) -> None:
        """Set up vocal isolation feature with demucs, with improved user prompts and safety."""
        print("\nSetting up vocal isolation feature...")
        # Step 1: Ensure Miniconda is installed
        if not self.check_miniconda_installed():
            print("Miniconda not found. Downloading miniconda...")
            installer_path = self.download_miniconda()
            if not installer_path:
                print("Failed to download miniconda. Skipping.")
                return
            if not self.install_miniconda(installer_path):
                print("Failed to install miniconda. Skipping vocal isolation setup.")
                return
        else:
            print(f"Miniconda already installed at {self.config.MINICONDA_PATH}.")

        # Step 2: Check for existing data_whisper environment
        default_env_path = self.config.MINICONDA_PATH / 'envs' / 'data_whisper'
        env_path = default_env_path
        env_exists = env_path.exists()
        custom_env = False
        if env_exists:
            print(f"A data_whisper environment already exists at {env_path}.")
            while True:
                choice = input("Would you like to (k)eep, (r)ecreate, or (s)pecify a different environment? (keep/recreate/specify): ").strip().lower()
                if choice in ("keep", "k"):
                    print("Keeping existing data_whisper environment. Will update/install required packages.")
                    break
                elif choice in ("recreate", "r"):
                    confirm = input(f"Are you sure you want to delete and recreate the environment at {env_path}? (yes/no): ").strip().lower()
                    if confirm in ("yes", "y"):
                        import shutil
                        try:
                            shutil.rmtree(env_path)
                            print("Old environment removed.")
                            env_exists = False
                        except Exception as e:
                            print(f"Failed to remove environment: {e}")
                            return
                        break
                    else:
                        print("Keeping existing environment.")
                        break
                elif choice in ("specify", "s"):
                    custom_path = input("Please enter the full path to your existing data_whisper environment folder: ").strip()
                    if custom_path and os.path.isdir(custom_path):
                        env_path = Path(custom_path)
                        custom_env = True
                        print(f"Using custom data_whisper environment at {env_path}.")
                        break
                    else:
                        print("Invalid path. Please try again.")
                else:
                    print("Please answer 'keep', 'recreate', or 'specify'.")
        else:
            # No environment exists, ask if user has one elsewhere
            while True:
                choice = input("No data_whisper environment found. Do you want to (c)reate a new one or (s)pecify an existing one? (create/specify): ").strip().lower()
                if choice in ("create", "c"):
                    break
                elif choice in ("specify", "s"):
                    custom_path = input("Please enter the full path to your existing data_whisper environment folder: ").strip()
                    if custom_path and os.path.isdir(custom_path):
                        env_path = Path(custom_path)
                        custom_env = True
                        print(f"Using custom data_whisper environment at {env_path}.")
                        break
                    else:
                        print("Invalid path. Please try again.")
                else:
                    print("Please answer 'create' or 'specify'.")

        # Step 3: Create environment if needed
        if not env_path.exists():
            if not self.create_data_whisper_env():
                print("Failed to create data_whisper environment. Skipping.")
                return
            print(f"Created new data_whisper environment at {env_path}.")
        else:
            print(f"Using data_whisper environment at {env_path}.")

        # Step 4: Always run installs to ensure dependencies are present/up to date
        if self.install_demucs_in_env():
            print("\nVocal isolation setup completed successfully!")
            print(f"To manually activate the environment, run: conda activate {env_path.resolve()}")
        else:
            print("\nFailed to install demucs. Please try installing it manually.")
            print(f"1. Activate the environment: conda activate {env_path.resolve()}")
            print(f"2. Run: pip install demucs")

    def create_config_file(self, ffmpeg_path: Optional[Path], ytdlp_path: Optional[Path]) -> None:
        """Create the batch file (Windows) or shell script (Linux/macOS) for setting PATH environment variable and activating conda env."""
        path_parts = []
        if ffmpeg_path: path_parts.append(str(ffmpeg_path.resolve()))
        if ytdlp_path: path_parts.append(str(ytdlp_path.resolve()))
        
        # Check if vocal isolation is set up with conda environment
        env_path = self.config.MINICONDA_PATH / 'envs' / 'data_whisper'
        has_conda_env = env_path.exists() and not self.use_system_python
        
        if self.config.OS_TYPE == 'windows':
            # Windows batch file
            path_string = ";".join(path_parts)
            
            if has_conda_env:
                miniconda_scripts = self.config.MINICONDA_PATH / 'Scripts'
                # Add Miniconda Scripts to PATH so conda commands are available
                if path_string:
                    path_string = f"{miniconda_scripts};{path_string}"
                else:
                    path_string = str(miniconda_scripts)
                
                config_content = (
                    f'@echo off\n'
                    f'set "PATH={path_string};%PATH%"\n'
                    f'echo FFmpeg, yt-dlp, and conda are available in this session.\n'
                    f'echo Activating data_whisper conda environment...\n'
                    f'call "{miniconda_scripts / "activate.bat"}" "{env_path}"\n'
                    f'if errorlevel 1 (\n'
                    f'    echo Warning: Failed to activate data_whisper environment\n'
                    f'    echo You may need to run: conda activate data_whisper\n'
                    f') else (\n'
                    f'    echo data_whisper conda environment activated successfully!\n'
                    f'    echo demucs is now available.\n'
                    f')\n'
                )
            elif self.use_system_python:
                config_content = (
                    f'@echo off\n'
                    f'set "PATH={path_string};%PATH%"\n'
                    f'echo FFmpeg and yt-dlp are available in this session.\n'
                    f'echo Vocal isolation is set up with system Python - demucs should be available.\n'
                    f'echo To test: python -c "import demucs; print(\'demucs installed successfully\')"\n'
                )
            else:
                config_content = (
                    f'@echo off\n'
                    f'set "PATH={path_string};%PATH%"\n'
                    f'echo FFmpeg and yt-dlp are available in this session.\n'
                    f'echo Note: Vocal isolation not set up. Run with --using_vocal_isolation to enable.\n'
                )
        else:
            # Linux/macOS shell script
            path_string = ":".join(path_parts)
            
            if has_conda_env:
                miniconda_bin = self.config.MINICONDA_PATH / 'bin'
                # Add Miniconda bin to PATH so conda commands are available
                if path_string:
                    path_string = f"{miniconda_bin}:{path_string}"
                else:
                    path_string = str(miniconda_bin)
                
                config_content = (
                    f'#!/bin/bash\n'
                    f'export PATH="{path_string}:$PATH"\n'
                    f'echo "FFmpeg, yt-dlp, and conda are available in this session."\n'
                    f'echo "Activating data_whisper conda environment..."\n'
                    f'source "{miniconda_bin / "activate"}" "{env_path}"\n'
                    f'if [ $? -eq 0 ]; then\n'
                    f'    echo "data_whisper conda environment activated successfully!"\n'
                    f'    echo "demucs is now available."\n'
                    f'else\n'
                    f'    echo "Warning: Failed to activate data_whisper environment"\n'
                    f'    echo "You may need to run: conda activate data_whisper"\n'
                    f'fi\n'
                )
            elif self.use_system_python:
                config_content = (
                    f'#!/bin/bash\n'
                    f'export PATH="{path_string}:$PATH"\n'
                    f'echo "FFmpeg and yt-dlp are available in this session."\n'
                    f'echo "Vocal isolation is set up with system Python - demucs should be available."\n'
                    f'echo "To test: python -c \\"import demucs; print(\'demucs installed successfully\')\\""\n'
                )
            else:
                config_content = (
                    f'#!/bin/bash\n'
                    f'export PATH="{path_string}:$PATH"\n'
                    f'echo "FFmpeg and yt-dlp are available in this session."\n'
                    f'echo "Note: Vocal isolation not set up. Run with --using_vocal_isolation to enable."\n'
                )
        
        with open(self.config.CONFIG_FILE, 'w', encoding='utf-8') as file:
            file.write(config_content)
        
        # Make shell script executable on Unix-like systems
        if self.config.OS_TYPE in ['linux', 'darwin']:
            self.downloader.make_executable(self.config.CONFIG_FILE)
        
        print(f"\n{self.config.CONFIG_FILE} created with path settings and conda activation.")

    def run(self, using_vocal_isolation: bool = False, force_ffmpeg_download: bool = False, force_ytdlp_download: bool = False, use_system_python: bool = False) -> None:
        """Run the environment setup process."""
        # Store the system python preference
        self.use_system_python = use_system_python
        
        print("This script will download the following tools to 'downloaded_assets/' folder:")
        print("1. FFmpeg, 2. yt-dlp, 3. 7zr")
        if using_vocal_isolation:
            if use_system_python:
                print("4. PyTorch and Demucs (system Python)")
            else:
                print("4. Miniconda, 5. Demucs")
        print("\nAll installers and tools will be saved locally for reuse.")

        seven_zip_exec = self.setup_7zr()
        if not seven_zip_exec:
            print("Failed to set up 7zr.exe. Exiting...")
            return

        ffmpeg_path = self.setup_ffmpeg(seven_zip_exec, force_download=force_ffmpeg_download)
        ytdlp_path = self.setup_ytdlp(force_download=force_ytdlp_download)

        if using_vocal_isolation:
            if use_system_python:
                if not self.install_demucs_system_python():
                    print("Failed to install demucs with system Python. Please check the error messages above.")
                    return
            else:
                self.setup_vocal_isolation()

        self.create_config_file(ffmpeg_path, ytdlp_path)


def main() -> None:
    """Main entry point of the script."""
    print(f"Synthalingua Environment Setup Version {VERSION_NUMBER}")
    parser = argparse.ArgumentParser(description="Synthalingua Environment Setup")
    parser.add_argument('--reinstall', action='store_true', help='Wipe all tool folders/files and redownload fresh')
    parser.add_argument('--using_vocal_isolation', action='store_true', help='Install miniconda environment with demucs for vocal isolation features')
    args = parser.parse_args()

    # Check if this is a fresh install (no config file exists)
    config_exists = False
    if platform.system().lower() == 'windows':
        config_exists = os.path.exists("ffmpeg_path.bat")
    else:
        config_exists = os.path.exists("ffmpeg_path.sh")
    
    is_fresh_install = not config_exists

    # If fresh install and no arguments provided, enable vocal isolation by default
    if is_fresh_install and not args.reinstall and not args.using_vocal_isolation:
        print("\n🆕 Fresh installation detected!")
        print("For the best experience, we recommend setting up vocal isolation features.")
        while True:
            setup_vocal = input("Would you like to set up vocal isolation (demucs) along with the basic tools? (yes/no): ").strip().lower()
            if setup_vocal in ("yes", "y"):
                args.using_vocal_isolation = True
                print("✅ Vocal isolation will be included in the setup.")
                print("⚠️  Note: Vocal isolation setup will require approximately 8GB of disk space")
                print("   (Miniconda + PyTorch + Demucs + audio libraries)")
                break
            elif setup_vocal in ("no", "n"):
                print("ℹ️  Setting up basic tools only. You can add vocal isolation later with --using_vocal_isolation")
                break
            else:
                print("Please answer 'yes' or 'no'.")

    # Early exit if config already exists and no reinstall or extra setup requested
    if config_exists and not args.reinstall and not args.using_vocal_isolation:
        print("\nConfig file already exists. Use --reinstall to set up again, or --using_vocal_isolation to add vocal isolation.")
        return

    # Prompt for vocal isolation setup if requested
    miniconda_path: Optional[Path] = None
    use_system_python = False
    
    if args.using_vocal_isolation:
        # Platform-specific vocal isolation setup
        if platform.system().lower() == 'windows':
            # Windows: Always use Miniconda (as requested)
            default_path = 'C:\\bin\\Synthalingua\\miniconda'
            print(f"\nMiniconda is required for vocal isolation on Windows.")
            print(f"The recommended installation path is: {default_path}")
            while True:
                agree = input("Do you agree to install Miniconda to this path? (yes/no): ").strip().lower()
                if agree in ('yes', 'y'):
                    miniconda_path = Path(default_path)
                    break
                elif agree in ('no', 'n'):
                    print("\n⚠️  It is strongly recommended to use the default installation path for Miniconda.")
                    print("   Changing the location is not recommended unless absolutely necessary.")
                    print("   If you must choose a custom location, make sure the path contains NO SPACES.")
                    print("   Paths with spaces can cause installation and runtime errors with Miniconda and other tools.")
                    print("   📁 Note: A 'miniconda' folder will be created inside your chosen directory.")
                    while True:
                        custom_path = input("Please enter a custom base directory for Miniconda installation (NO SPACES): ").strip()
                        if ' ' in custom_path:
                            print("❌ Path cannot contain spaces. Please try again with a path that has NO SPACES.")
                            continue
                        if not custom_path:
                            print("Path cannot be empty. Please try again.")
                            continue
                        # Always append 'miniconda' to the user's chosen directory
                        miniconda_path = Path(custom_path) / 'miniconda'
                        print(f"Miniconda will be installed to: {miniconda_path}")
                        break
                    break
                else:
                    print("Please answer 'yes' or 'no'.")
        else:
            # Linux/macOS: Give users choice between Miniconda and system Python
            print("\n🐍 Python Environment Choice for Vocal Isolation")
            print("Linux users have two options for setting up vocal isolation (demucs):")
            print()
            print("1. 🐍 Use your existing system Python environment")
            print("   - Installs packages directly to your current Python environment")
            print("   - Requires: Python 3.8+ with pip")
            print("   - Lighter setup, uses your existing Python configuration")
            print()
            print("2. 🐧 Install Miniconda (isolated environment)")
            print("   - Creates a separate conda environment for Synthalingua")
            print("   - More isolated, won't conflict with your system packages")
            print("   - Requires ~8GB disk space")
            print()
            
            while True:
                choice = input("Which option do you prefer? (system/miniconda): ").strip().lower()
                if choice in ("system", "sys", "1"):
                    use_system_python = True
                    print("✅ Using system Python environment.")
                    print("📦 Packages will be installed to your current Python environment.")
                    print("💡 Make sure you have Python 3.8+ and pip available.")
                    print()
                    # Verify Python version
                    try:
                        import sys
                        python_version = sys.version_info
                        current_version = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
                        
                        if python_version.major == 3 and python_version.minor >= 8:
                            print(f"✅ Python {current_version} detected - compatible!")
                            
                            # Provide specific recommendations based on platform
                            if platform.system().lower() == 'windows':
                                if current_version == "3.12.10":
                                    print("   Perfect! This is the recommended Python version for Windows.")
                                elif python_version.minor == 12:
                                    print(f"   Note: Python 3.12.10 is recommended for Windows stability.")
                                    print(f"   Your version {current_version} might work but could be less stable.")
                                else:
                                    print(f"   Recommendation: Consider upgrading to Python 3.12.10 for best Windows compatibility.")
                            else:  # Linux/macOS
                                if python_version.minor == 12:
                                    if current_version == "3.12.10":
                                        print("   Perfect! This is the most stable Python 3.12.x version.")
                                    else:
                                        print(f"   Note: Python 3.12.10 is recommended for stability.")
                                        print(f"   Your version {current_version} should work but might be less stable.")
                                else:
                                    print(f"   Recommendation: Python 3.12.x is recommended for best compatibility.")
                        else:
                            print(f"⚠️  Python {current_version} detected.")
                            print("   Demucs requires Python 3.8+. Please upgrade if you encounter issues.")
                            if platform.system().lower() == 'windows':
                                print("   Recommended: Python 3.12.10 for Windows")
                            else:
                                print("   Recommended: Python 3.12.x for Linux/macOS")
                    except Exception as e:
                        print(f"⚠️  Could not verify Python version: {e}")
                    break
                elif choice in ("miniconda", "conda", "mini", "2"):
                    use_system_python = False
                    default_path = os.path.expanduser('~/bin/Synthalingua/miniconda')
                    print("✅ Using Miniconda for isolated environment.")
                    print(f"📁 Default installation path: {default_path}")
                    
                    while True:
                        agree = input("Install Miniconda to the default path? (yes/no): ").strip().lower()
                        if agree in ('yes', 'y'):
                            miniconda_path = Path(default_path)
                            break
                        elif agree in ('no', 'n'):
                            print("\n⚠️  Custom paths are not recommended unless necessary.")
                            print("   Make sure the path contains NO SPACES.")
                            print("   📁 Note: A 'miniconda' folder will be created inside your chosen directory.")
                            while True:
                                custom_path = input("Please enter a custom base directory for Miniconda installation (NO SPACES): ").strip()
                                if ' ' in custom_path:
                                    print("❌ Path cannot contain spaces. Please try again with a path that has NO SPACES.")
                                    continue
                                if not custom_path:
                                    print("Path cannot be empty. Please try again.")
                                    continue
                                # Always append 'miniconda' to the user's chosen directory
                                miniconda_path = Path(custom_path) / 'miniconda'
                                print(f"Miniconda will be installed to: {miniconda_path}")
                                break
                            break
                        else:
                            print("Please answer 'yes' or 'no'.")
                    break
                else:
                    print("Please answer 'system' or 'miniconda'.")
                break
            else:
                print("Please answer 'yes' or 'no'.")

    # Determine config path based on whether miniconda path was set
    cfg = Config(miniconda_path if miniconda_path else Path.cwd() / 'miniconda_placeholder')

    assets_to_check = [
        ('FFmpeg folder', cfg.FFMPEG_ROOT_PATH),
        ('FFmpeg archive', Path(cfg.FFMPEG_ARCHIVE)),
        ('yt-dlp folder', cfg.YTDLP_PATH),
        ('yt-dlp archive', Path(cfg.YTDLP_ARCHIVE)),
        ('7zr.exe', cfg.ASSETS_PATH / '7zr.exe'),
        ('Miniconda installer', cfg.ASSETS_PATH / 'miniconda_installer.exe'),
    ]

    assets_to_remove = []
    if args.reinstall:
        print("\n--reinstall specified: Removing all tool folders/files for a fresh setup...")
        # Add all existing assets to the removal list if --reinstall is used
        for name, path in assets_to_check:
            if path.exists():
                assets_to_remove.append(path)
        # Also add the miniconda installation path if vocal isolation is requested and it exists
        if args.using_vocal_isolation and miniconda_path and miniconda_path.exists():
             assets_to_remove.append(miniconda_path)
    else:
        print("\nChecking for existing assets...")
        for name, path in assets_to_check:
            if path.exists():
                while True:
                    reuse = input(f"Detected existing {name} at {path}. Reuse this asset? (yes/no): ").strip().lower()
                    if reuse in ("yes", "y"):
                        break
                    elif reuse in ("no", "n"):
                        assets_to_remove.append(path)
                        break
                    else:
                        print("Please answer 'yes', 'no', 'y', or 'n'.")
        # Special handling for Miniconda installation directory reuse
        if args.using_vocal_isolation and miniconda_path and miniconda_path.exists():
             while True:
                wipe_choice = input(f"Miniconda is already installed at {miniconda_path}. Do you want to (w)ipe and reinstall, or (k)eep and reuse it? (wipe/keep): ").strip().lower()
                if wipe_choice in ("wipe", "w"):
                    assets_to_remove.append(miniconda_path)
                    print("Vocal isolation flag detected - will reinstall miniconda environment.")
                    break
                elif wipe_choice in ("keep", "k"):
                    print("Keeping existing Miniconda installation. Will reuse and update environments as needed.")
                    break
                else:
                    print("Please answer 'wipe' or 'keep'.")

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
                        print(f"❌ Error removing folder {path}: {e}")
                        print("Please ensure you have the necessary permissions to delete this folder.")
                else:
                    print(f"Attempting to remove file: {path}")
                    try:
                        path.unlink()
                        print(f"Successfully removed file: {path}")
                    except OSError as e:
                        print(f"❌ Error removing file {path}: {e}")
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
            print(f"❌ Error removing config file {config_file_path}: {e}")
            print("Please ensure you have the necessary permissions to delete this file.")

    # Determine if FFmpeg and yt-dlp should be force downloaded
    force_ffmpeg = cfg.FFMPEG_ROOT_PATH in assets_to_remove
    force_ytdlp = cfg.YTDLP_PATH in assets_to_remove

    setup = EnvironmentSetup(miniconda_path if miniconda_path else Path.cwd() / 'miniconda_placeholder') # Pass placeholder if no miniconda path selected
    setup.run(using_vocal_isolation=args.using_vocal_isolation, force_ffmpeg_download=force_ffmpeg, force_ytdlp_download=force_ytdlp, use_system_python=use_system_python)

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()