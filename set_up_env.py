import argparse
"""Environment setup script for Synthalingua.

This script handles the installation and configuration of required tools:
- FFmpeg: A multimedia framework for processing audio and video files
- yt-dlp: A video downloader for YouTube and other sites
- 7zr: A tool for extracting .7z files
- Miniconda: Python environment manager for creating isolated environments (optional with --using_vocal_isolation)
- Demucs: Audio source separation library for vocal isolation (optional with --using_vocal_isolation)

The script will create a batch file that sets up the necessary PATH environment
variables for these tools to work with Synthalingua. For vocal isolation features,
use the --using_vocal_isolation flag to download and install Miniconda, create a 
data_whisper environment with Python 3.12, and install the demucs package.

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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List
from tqdm import tqdm


# Version number for the setup script
VERSION_NUMBER = "0.0.41"

@dataclass
class Config:
    """Configuration settings for the environment setup."""
    FFMPEG_URL: str = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
    YTDLP_URL: str = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.30/yt-dlp_win.zip'
    SEVEN_ZIP_URL: str = 'https://www.7-zip.org/a/7zr.exe'
    MINICONDA_WINDOWS_URL: str = 'https://repo.anaconda.com/miniconda/Miniconda3-py312_25.5.1-0-Windows-x86_64.exe'
    def __init__(self, miniconda_path: Path):
        self.ASSETS_PATH: Path = Path.cwd() / 'downloaded_assets'
        self.FFMPEG_ROOT_PATH: Path = self.ASSETS_PATH / 'ffmpeg'
        self.YTDLP_PATH: Path = self.ASSETS_PATH / 'yt-dlp_win'
        self.MINICONDA_PATH: Path = miniconda_path
        self.FFMPEG_ARCHIVE: str = str(self.ASSETS_PATH / 'ffmpeg.7z')
        self.YTDLP_ARCHIVE: str = str(self.ASSETS_PATH / 'yt-dlp_win.zip')
        self.SEVEN_ZIP_EXEC: str = '7zr.exe'
        self.CONFIG_FILE: str = 'ffmpeg_path.bat'
        self.MINICONDA_INSTALLER: str = 'miniconda_installer'


class DownloadManager:
    """Handles file downloads and extractions."""

    @staticmethod
    def download_file(url: str, filename: str) -> None:
        """Download a file from a URL with progress display."""
        print(f"Downloading {Path(filename).name} from {url}...")
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

    @staticmethod
    def extract_7z(file_path: str, extract_to: str, seven_zip_exec: str) -> None:
        """Extract a .7z file using 7zr.exe."""
        print(f"Extracting {file_path} with 7zr...")
        subprocess.run([seven_zip_exec, 'x', file_path, f'-o{extract_to}'], check=True, capture_output=True)
        print(f"{Path(file_path).name} extracted successfully.")

    @staticmethod
    def extract_zip(file_path: str, extract_to: str) -> None:
        """Extract a .zip file to a specified directory."""
        print(f"Extracting {file_path}...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"{Path(file_path).name} extracted successfully.")


class EnvironmentSetup:
    """Handles the setup of required tools and environment."""

    def __init__(self, miniconda_path: Path):
        self.config = Config(miniconda_path)
        self.downloader = DownloadManager()

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
        """Set up 7zr.exe either from user input or download."""
        # Create assets directory if it doesn't exist
        self.config.ASSETS_PATH.mkdir(exist_ok=True)
        seven_zip_path = self.config.ASSETS_PATH / '7zr.exe'
        
        # Check if 7zr.exe exists in downloaded_assets and ask user
        if seven_zip_path.exists():
            while True:
                reuse = input(f"Found existing 7zr.exe. Use it or download fresh? (use/download): ").strip().lower()
                if reuse in ("use", "u"):
                    print(f"Using existing 7zr.exe: {seven_zip_path}")
                    return str(seven_zip_path)
                elif reuse in ("download", "d"):
                    print("Downloading fresh 7zr.exe...")
                    seven_zip_path.unlink()  # Remove old file first
                    break
                else:
                    print("Please answer 'use' or 'download'.")
        else:
            # Only ask about providing own version if no downloaded version exists
            use_own_7zr = input("Do you want to provide your own version of 7zr.exe? (yes/no): ").strip().lower()
            if use_own_7zr == 'yes':
                sevens_zip_path = input("Please enter the path to your 7zr.exe file: ").strip()
                if os.path.isfile(sevens_zip_path):
                    print(f"Using provided 7zr.exe at {sevens_zip_path}.")
                    return sevens_zip_path
                print("The specified 7zr.exe file does not exist.")
                return None
        
        try:
            self.downloader.download_file(self.config.SEVEN_ZIP_URL, str(seven_zip_path))
            return str(seven_zip_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download 7zr.exe: {e}")
            return None

    def setup_ffmpeg(self, seven_zip_exec: str) -> Optional[Path]:
        """Set up FFmpeg either from user input or download."""
        use_own_ffmpeg = input("Do you already have FFmpeg? (yes/no): ").strip().lower()
        if use_own_ffmpeg == 'yes':
            use_system_ffmpeg = input("Do you want to use the system default FFmpeg? (yes/no): ").strip().lower()
            if use_system_ffmpeg == 'yes':
                return None
            ffmpeg_path = input("Please enter the path to your FFmpeg bin folder: ").strip()
            if os.path.isdir(ffmpeg_path):
                return self.find_ffmpeg_bin_path(Path(ffmpeg_path))
            print("The specified FFmpeg folder does not exist.")
            return None
        if not self.config.FFMPEG_ROOT_PATH.is_dir():
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)
                
                # Check if archive exists and ask user
                ffmpeg_archive_path = Path(self.config.FFMPEG_ARCHIVE)
                if ffmpeg_archive_path.exists():
                    while True:
                        reuse = input(f"Found existing FFmpeg archive. Use it or download fresh? (use/download): ").strip().lower()
                        if reuse in ("use", "u"):
                            print(f"Using existing FFmpeg archive: {self.config.FFMPEG_ARCHIVE}")
                            break
                        elif reuse in ("download", "d"):
                            print("Downloading fresh FFmpeg archive...")
                            ffmpeg_archive_path.unlink()  # Remove old archive first
                            self.downloader.download_file(self.config.FFMPEG_URL, self.config.FFMPEG_ARCHIVE)
                            break
                        else:
                            print("Please answer 'use' or 'download'.")
                else:
                    self.downloader.download_file(self.config.FFMPEG_URL, self.config.FFMPEG_ARCHIVE)
                
                temp_extract_path = self.config.ASSETS_PATH / "_temp_ffmpeg"
                temp_extract_path.mkdir(exist_ok=True)
                self.downloader.extract_7z(self.config.FFMPEG_ARCHIVE, str(temp_extract_path), seven_zip_exec)
                
                extracted_folders = [d for d in temp_extract_path.iterdir() if d.is_dir()]
                if not extracted_folders:
                    raise FileNotFoundError("Could not find the main folder inside the FFmpeg archive.")
                
                extracted_folders[0].rename(self.config.FFMPEG_ROOT_PATH)
                
                import shutil
                shutil.rmtree(temp_extract_path)
                # Keep the archive for reuse: os.remove(self.config.FFMPEG_ARCHIVE)
                
                return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)
            except (requests.exceptions.RequestException, subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"Failed to set up FFmpeg: {e}")
                return None
        else:
            print("FFmpeg folder already exists, skipping download.")
            return self.find_ffmpeg_bin_path(self.config.FFMPEG_ROOT_PATH)

    def setup_ytdlp(self) -> Optional[Path]:
        """Set up yt-dlp either from user input or download."""
        use_own_ytdlp = input("Do you already have yt-dlp? (yes/no): ").strip().lower()
        if use_own_ytdlp == 'yes':
            use_system_ytdlp = input("Do you want to use the system default yt-dlp? (yes/no): ").strip().lower()
            if use_system_ytdlp == 'yes':
                return None
            ytdlp_path = input("Please enter the path to your yt-dlp folder: ").strip()
            if os.path.isdir(ytdlp_path):
                return Path(ytdlp_path)
            print("The specified yt-dlp folder does not exist.")
            return None
        if not self.config.YTDLP_PATH.is_dir():
            try:
                self.config.ASSETS_PATH.mkdir(exist_ok=True)
                
                # Check if archive exists and ask user
                ytdlp_archive_path = Path(self.config.YTDLP_ARCHIVE)
                if ytdlp_archive_path.exists():
                    while True:
                        reuse = input(f"Found existing yt-dlp archive. Use it or download fresh? (use/download): ").strip().lower()
                        if reuse in ("use", "u"):
                            print(f"Using existing yt-dlp archive: {self.config.YTDLP_ARCHIVE}")
                            break
                        elif reuse in ("download", "d"):
                            print("Downloading fresh yt-dlp archive...")
                            ytdlp_archive_path.unlink()  # Remove old archive first
                            self.downloader.download_file(self.config.YTDLP_URL, self.config.YTDLP_ARCHIVE)
                            break
                        else:
                            print("Please answer 'use' or 'download'.")
                else:
                    self.downloader.download_file(self.config.YTDLP_URL, self.config.YTDLP_ARCHIVE)
                
                self.config.YTDLP_PATH.mkdir(exist_ok=True)
                self.downloader.extract_zip(self.config.YTDLP_ARCHIVE, str(self.config.YTDLP_PATH))
                # Keep the archive for reuse: os.remove(self.config.YTDLP_ARCHIVE)
                ytdlp_exe = self.config.YTDLP_PATH / 'yt-dlp.exe'
                if ytdlp_exe.exists():
                    while True:
                        update_choice = input("Would you like to check for yt-dlp updates now? (yes/no): ").strip().lower()
                        if update_choice in ("yes", "y"):
                            print("Updating yt-dlp to the latest version...")
                            try:
                                subprocess.run([str(ytdlp_exe), '-U'], check=True, capture_output=True)
                                print("yt-dlp updated to the latest version.")
                            except Exception as e:
                                print(f"Warning: Failed to auto-update yt-dlp: {e}")
                            break
                        elif update_choice in ("no", "n"):
                            print("Skipping yt-dlp update check.")
                            break
                        else:
                            print("Please answer 'yes' or 'no'.")
                return self.config.YTDLP_PATH
            except (requests.exceptions.RequestException, zipfile.BadZipFile) as e:
                print(f"Failed to set up yt-dlp: {e}")
                return None
        else:
            print("yt-dlp folder already exists, skipping download.")
            return self.config.YTDLP_PATH

    def check_miniconda_installed(self) -> bool:
        """Check if miniconda is installed in the local directory."""
        return self.config.MINICONDA_PATH.exists() and self.config.MINICONDA_PATH.is_dir()

    def download_miniconda(self) -> Optional[str]:
        """Download miniconda installer for Windows."""
        self.config.ASSETS_PATH.mkdir(exist_ok=True)
        installer_path = self.config.ASSETS_PATH / "miniconda_installer.exe"
        
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
        
        url = self.config.MINICONDA_WINDOWS_URL
        print(f"Using miniconda installer: {url.split('/')[-1]}")
        try:
            self.downloader.download_file(url, str(installer_path))
            return str(installer_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download miniconda: {e}")
            return None

    def install_miniconda(self, installer_path: str) -> bool:
        """Install miniconda using the downloaded installer."""
        miniconda_install_path = r"C:\bin\Synthalingua\miniconda"
        
        print("Installing miniconda for Windows...")
        print(f"Installation path: {miniconda_install_path}")
        # Ensure parent directories exist
        Path(miniconda_install_path).parent.mkdir(parents=True, exist_ok=True)
        command = [
            installer_path,
            '/InstallationType=JustMe',
            '/RegisterPython=0',
            '/AddToPath=0',
            '/S',
            f'/D={miniconda_install_path}'
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing miniconda. Exit code: {e.returncode}")
            if e.stdout: print(f"Installer stdout:\n{e.stdout}")
            if e.stderr: print(f"Installer stderr:\n{e.stderr}")
            print("\n💡 Suggestions:")
            print("   1. Check for leftover Miniconda/Anaconda installations or registry keys.")
            print("   2. Make sure you have write permissions to C:\\bin\\Synthalingua.")
            return False

        print("Miniconda installation completed.")
        if Path(miniconda_install_path).exists():
            print(f"✅ Miniconda successfully installed to: {Path(miniconda_install_path).resolve()}")
            return True
        else:
            print(f"❌ ERROR: Miniconda installation directory not found at: {Path(miniconda_install_path).resolve()}")
            return False

    def _get_conda_exe(self) -> Optional[str]:
        """Find the conda executable for Windows."""
        if not self.check_miniconda_installed(): return None
        possible_paths = [
            self.config.MINICONDA_PATH / 'Scripts' / 'conda.exe', 
            self.config.MINICONDA_PATH / 'condabin' / 'conda.bat'
        ]
        for path in possible_paths:
            if path.exists():
                return str(path)
        print(f"Error: conda executable not found in {self.config.MINICONDA_PATH}")
        return None

    def create_data_whisper_env(self) -> bool:
        """Create the data_whisper environment using miniconda (in the default envs folder)."""
        conda_exe = self._get_conda_exe()
        if not conda_exe: return False
        try:
            print("Creating data_whisper environment with Python 3.12...")
            subprocess.run([conda_exe, 'create', '-n', 'data_whisper', 'python=3.12', '-y'], check=True, text=True)
            print("data_whisper environment created successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error creating environment: {e}")
            return False

    def install_demucs_in_env(self) -> bool:
        """Install demucs package in the data_whisper environment with appropriate PyTorch version."""
        conda_exe = self._get_conda_exe()
        if not conda_exe: return False
        
        # Ask user about their preferred device for Synthalingua processing
        print("\nSynthalingua supports both CPU and GPU (CUDA) processing.")
        print("This affects both transcription and vocal isolation (demucs) performance.")
        while True:
            device_choice = input("Which device do you typically want to use with Synthalingua? (cpu/cuda): ").strip().lower()
            if device_choice in ("cuda", "gpu"):
                use_cuda = True
                print("CUDA selected - This will install GPU-accelerated PyTorch for faster processing.")
                break
            elif device_choice in ("cpu"):
                use_cuda = False
                print("CPU selected - This will install CPU-only PyTorch (slower but more compatible).")
                break
            else:
                print("Please answer 'cpu' or 'cuda'.")
        
        try:
            if use_cuda:
                print("Installing CUDA-enabled PyTorch in data_whisper environment...")
                print("This may take several minutes depending on your internet connection...")
                print("You should see pip download progress below:")
                sys.stdout.flush()
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'torch', 'torchaudio', '--index-url', 'https://download.pytorch.org/whl/cu128'], text=True)
                if result.returncode != 0:
                    print(f"Error installing CUDA PyTorch. Exit code: {result.returncode}")
                    return False
                print("CUDA PyTorch installation completed successfully.")
            else:
                print("Installing CPU-only PyTorch in data_whisper environment...")
                print("This may take several minutes depending on your internet connection...")
                print("You should see pip download progress below:")
                sys.stdout.flush()
                result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'torch', 'torchaudio'], text=True)
                if result.returncode != 0:
                    print(f"Error installing CPU PyTorch. Exit code: {result.returncode}")
                    return False
                print("CPU PyTorch installation completed successfully.")
            
            print("Installing demucs and diffq in data_whisper environment...")
            sys.stdout.flush()
            result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', '-U', 'demucs', 'diffq'], text=True)
            if result.returncode != 0:
                print(f"Error installing demucs and diffq. Exit code: {result.returncode}")
                return False
            
            print("Installing additional audio backend support for demucs...")
            sys.stdout.flush()
            # Install conda audio packages first for better compatibility
            result = subprocess.run([conda_exe, 'install', '-n', 'data_whisper', '-c', 'conda-forge', 'libsndfile', 'ffmpeg', '-y'], text=True)
            if result.returncode != 0:
                print(f"Warning: Could not install conda audio packages. Exit code: {result.returncode}")
            
            # Install pip audio packages
            result = subprocess.run([conda_exe, 'run', '-n', 'data_whisper', 'pip', 'install', 'soundfile', 'librosa'], text=True)
            if result.returncode != 0:
                print(f"Warning: Could not install additional audio backends. Exit code: {result.returncode}")
                print("Demucs may have audio backend issues.")
            else:
                print("Additional audio backend support installed successfully.")
            
            print("Demucs installation completed successfully.")
            
            if use_cuda:
                print("Verifying CUDA availability...")
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
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
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
        """Create the batch file for setting PATH environment variable and activating conda env."""
        path_parts = []
        if ffmpeg_path: path_parts.append(str(ffmpeg_path.resolve()))
        if ytdlp_path: path_parts.append(str(ytdlp_path.resolve()))
        path_string = ";".join(path_parts)
        
        # Check if vocal isolation is set up
        env_path = self.config.MINICONDA_PATH / 'envs' / 'data_whisper'
        if env_path.exists():
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
        else:
            config_content = (
                f'@echo off\n'
                f'set "PATH={path_string};%PATH%"\n'
                f'echo FFmpeg and yt-dlp are available in this session.\n'
                f'echo Note: Vocal isolation not set up. Run with --using_vocal_isolation to enable.\n'
            )
        
        with open(self.config.CONFIG_FILE, 'w', encoding='utf-8') as file:
            file.write(config_content)
        print(f"\n{self.config.CONFIG_FILE} created with path settings and conda activation.")

    def run(self, using_vocal_isolation: bool = False) -> None:
        """Run the environment setup process."""
        print("This script will download the following tools to 'downloaded_assets/' folder:")
        print("1. FFmpeg, 2. yt-dlp, 3. 7zr")
        if using_vocal_isolation:
            print("4. Miniconda, 5. Demucs")
        print("\nAll installers and tools will be saved locally for reuse.")

        seven_zip_exec = self.setup_7zr()
        if not seven_zip_exec:
            print("Failed to set up 7zr.exe. Exiting...")
            return

        ffmpeg_path = self.setup_ffmpeg(seven_zip_exec)
        ytdlp_path = self.setup_ytdlp()
        
        if using_vocal_isolation:
            self.setup_vocal_isolation()
        
        self.create_config_file(ffmpeg_path, ytdlp_path)


def main() -> None:
    """Main entry point of the script."""
    print(f"Version {VERSION_NUMBER}")
    parser = argparse.ArgumentParser(description="Synthalingua Environment Setup")
    parser.add_argument('--reinstall', action='store_true', help='Wipe all tool folders/files and redownload fresh')
    parser.add_argument('--using_vocal_isolation', action='store_true', help='Install miniconda environment with demucs for vocal isolation features')
    args = parser.parse_args()

    # Check if this is a fresh install (no config file exists)
    config_exists = os.path.exists("ffmpeg_path.bat")
    is_fresh_install = not config_exists
    
    # If fresh install and no arguments provided, enable vocal isolation by default
    if is_fresh_install and not args.reinstall and not args.using_vocal_isolation:
        print("🆕 Fresh installation detected!")
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
        print("Config file already exists. Use --reinstall to set up again, or --using_vocal_isolation to add vocal isolation.")
        return

    # Prompt for Miniconda path ONCE
    default_path = 'C:\\bin\\Synthalingua\\miniconda'
    miniconda_path: Path
    print(f"Miniconda will be installed to: {default_path}")
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
            while True:
                custom_path = input("Please enter a custom path for Miniconda installation (NO SPACES, recommended to keep the default): ").strip()
                if ' ' in custom_path:
                    print("❌ Path cannot contain spaces. Please try again with a path that has NO SPACES.")
                    continue
                if not custom_path:
                    print("Path cannot be empty. Please try again.")
                    continue
                miniconda_path = Path(custom_path)
                break
            break
        else:
            print("Please answer 'yes', 'no', 'y', or 'n'.")

    # Individual asset reuse logic
    assets_to_check = []
    cfg = Config(miniconda_path)
    # FFmpeg
    if cfg.FFMPEG_ROOT_PATH.exists():
        assets_to_check.append(('FFmpeg', cfg.FFMPEG_ROOT_PATH))
    # FFmpeg archive
    ffmpeg_archive_path = Path(cfg.FFMPEG_ARCHIVE)
    if ffmpeg_archive_path.exists():
        assets_to_check.append(('FFmpeg archive', ffmpeg_archive_path))
    # yt-dlp
    if cfg.YTDLP_PATH.exists():
        assets_to_check.append(('yt-dlp', cfg.YTDLP_PATH))
    # yt-dlp archive
    ytdlp_archive_path = Path(cfg.YTDLP_ARCHIVE)
    if ytdlp_archive_path.exists():
        assets_to_check.append(('yt-dlp archive', ytdlp_archive_path))
    # 7zr.exe
    seven_zip_path = cfg.ASSETS_PATH / '7zr.exe'
    if seven_zip_path.exists():
        assets_to_check.append(('7zr.exe', seven_zip_path))
    # Miniconda installer
    miniconda_installer_path = cfg.ASSETS_PATH / 'miniconda_installer.exe'
    if miniconda_installer_path.exists():
        assets_to_check.append(('Miniconda installer', miniconda_installer_path))

    assets_to_remove = []
    if not args.reinstall:
        for name, path in assets_to_check:
            while True:
                reuse = input(f"Detected existing {name} at {path}. Reuse this asset? (yes/no): ").strip().lower()
                if reuse in ("yes", "y"):
                    break
                elif reuse in ("no", "n"):
                    assets_to_remove.append(path)
                    break
                else:
                    print("Please answer 'yes', 'no', 'y', or 'n'.")

    if args.reinstall or assets_to_remove:
        print("--reinstall specified or selected assets for removal: Removing tool folders/files for a fresh setup...")
        import shutil
        folders_to_remove = []
        files_to_remove = []
        # Remove folders for FFmpeg and yt-dlp if selected
        if args.reinstall or (cfg.FFMPEG_ROOT_PATH in assets_to_remove):
            folders_to_remove.append(cfg.FFMPEG_ROOT_PATH)
        if args.reinstall or (cfg.YTDLP_PATH in assets_to_remove):
            folders_to_remove.append(cfg.YTDLP_PATH)
        # Miniconda: prompt before removing, even with --reinstall
        minconda_should_remove = False
        if args.using_vocal_isolation and (args.reinstall or (cfg.MINICONDA_PATH in assets_to_remove)):
            if cfg.MINICONDA_PATH.exists():
                print(f"Miniconda is already installed at {cfg.MINICONDA_PATH}.")
                while True:
                    wipe_choice = input(f"Do you want to (w)ipe and reinstall Miniconda, or (k)eep and reuse it? (wipe/keep): ").strip().lower()
                    if wipe_choice in ("wipe", "w"):
                        minconda_should_remove = True
                        print("Vocal isolation flag detected - will reinstall miniconda environment.")
                        break
                    elif wipe_choice in ("keep", "k"):
                        print("Keeping existing Miniconda installation. Will reuse and update environments as needed.")
                        minconda_should_remove = False
                        break
                    else:
                        print("Please answer 'wipe' or 'keep'.")
            else:
                minconda_should_remove = False
        # Only add Miniconda to folders_to_remove if user confirmed wipe
        if minconda_should_remove:
            folders_to_remove.append(cfg.MINICONDA_PATH)
        # Remove files for 7zr.exe and ffmpeg_path.bat if selected
        if args.reinstall or (seven_zip_path in assets_to_remove):
            files_to_remove.append(seven_zip_path)
        files_to_remove.append(Path.cwd() / 'ffmpeg_path.bat')
        # Remove archives if selected
        ffmpeg_archive_path = Path(cfg.FFMPEG_ARCHIVE)
        if ffmpeg_archive_path in assets_to_remove:
            files_to_remove.append(ffmpeg_archive_path)
        ytdlp_archive_path = Path(cfg.YTDLP_ARCHIVE)
        if ytdlp_archive_path in assets_to_remove:
            files_to_remove.append(ytdlp_archive_path)
        # Remove Miniconda installer ONLY if user said no to reuse
        if (miniconda_installer_path in assets_to_remove):
            files_to_remove.append(miniconda_installer_path)
        for path in folders_to_remove:
            if path.exists() and path.is_dir():
                print(f"Removing folder: {path}")
                shutil.rmtree(path, ignore_errors=True)
        for path in files_to_remove:
            if path.exists():
                try: path.unlink()
                except Exception as e: print(f"Warning: Could not remove {path}: {e}")
        print("Selected tool folders/files have been removed for a fresh setup. Installers in downloaded_assets/ are preserved unless you chose not to reuse them.")

    setup = EnvironmentSetup(miniconda_path)
    setup.run(using_vocal_isolation=args.using_vocal_isolation)

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    main()