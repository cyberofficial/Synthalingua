import os
import subprocess
import urllib.request
import urllib.error
import sys
import zipfile
import shutil

def _download_reporthook(blocknum, blocksize, totalsize):
    """A simple hook for urllib to display download progress."""
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 100 / totalsize
        s = f"\r{int(percent)}% {readsofar} / {totalsize}"
        sys.stdout.write(s)
        if readsofar >= totalsize:
            sys.stdout.write("\n")
    else:
        sys.stdout.write(f"\rread {readsofar}")

def install_or_reinstall_python(assets_dir):
    """
    Handles the silent (re)installation of a specific Python version.
    Returns the path to the installation directory on success, otherwise None.
    """
    print("--- Setting up Python ---")
    python_version = "3.12.10"
    install_path = f"C:\\bin\\python\\{python_version}"
    url = f"https://www.python.org/ftp/python/{python_version}/python-{python_version}-amd64.exe"
    installer_path = os.path.join(assets_dir, f"python-{python_version}-amd64.exe")

    if os.path.isdir(install_path):
        choice = input(f"Python installation directory found at '{install_path}'.\nDo you want to reinstall or skip? (reinstall/skip): ").lower()
        if choice.startswith('s'):
            print("Skipping Python setup, using existing installation.")
            return install_path

    download_file = True
    if os.path.exists(installer_path):
        choice = input("Python installer found. Use existing or re-download? (use/redownload): ").lower()
        if choice.startswith('u'):
            print("Using existing Python installer.")
            download_file = False

    if download_file:
        print(f"Downloading Python installer to '{installer_path}'...")
        try:
            urllib.request.urlretrieve(url, installer_path, _download_reporthook)
            print("Download complete.")
        except Exception as e:
            print(f"Error downloading Python installer: {e}")
            return None

    try:
        print("\n" + "="*80)
        print("WARNING: The next step will UNINSTALL the existing Python 3.12 installation.")
        print("This is a potentially destructive action that may require Admin privileges.")
        print("If other projects depend on this installation, they may break.")
        print("="*80)
        
        confirm = input('To confirm you wish to proceed, please type "yes": ')
        if confirm.lower() != 'yes':
            print("\nPython re-installation cancelled by the user.")
            return None
        
        print(f"\nUninstalling existing Python {python_version}...")
        uninstall_command = [installer_path, "/uninstall", "/quiet"]
        subprocess.run(uninstall_command)
        print("Pre-emptive uninstall command finished.")

        print(f"Now, proceeding with fresh installation of Python {python_version}...")
        install_command = [
            installer_path, "/quiet", "InstallAllUsers=1",
            f"TargetDir={install_path}", "PrependPath=1"
        ]
        subprocess.run(install_command, check=True)
        print("Python installation successful!")

    except subprocess.CalledProcessError as e:
        print(f"\nAn error occurred during installation: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: The installer executable was not found at {installer_path}.")
        return None
    
    return install_path

def create_python_environment(base_python_exe, env_name):
    """
    Creates a Python virtual environment using the specified base interpreter.
    Returns the path to the new environment's python.exe.
    """
    print(f"\n--- Creating Python Virtual Environment: '{env_name}' ---")
    if not base_python_exe or not os.path.isfile(base_python_exe):
        print("Cannot create virtual environment: Base Python executable is invalid or not provided.")
        print(f"  Attempted to use: {base_python_exe}")
        return None
    
    print(f"Using base interpreter: {base_python_exe}")

    env_path = os.path.join(os.getcwd(), env_name)
    env_python_exe = os.path.join(env_path, 'Scripts', 'python.exe')

    if os.path.isdir(env_path):
        choice = input(f"Environment '{env_name}' already exists. Recreate or skip? (recreate/skip): ").lower()
        if choice.startswith('s'):
            print("Skipping environment creation.")
            return env_python_exe if os.path.isfile(env_python_exe) else None
        elif choice.startswith('r'):
            print(f"Deleting existing environment at '{env_path}'...")
            try:
                shutil.rmtree(env_path)
                print("Existing environment removed.")
            except OSError as e:
                print(f"Error removing directory: {e}")
                return None
        else:
            print("Invalid choice. Skipping environment creation.")
            return env_python_exe if os.path.isfile(env_python_exe) else None
    
    print(f"Creating virtual environment at '{env_path}'...")
    try:
        command = [base_python_exe, '-m', 'venv', env_path]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print("Virtual environment created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to create virtual environment: {e.stderr}")
        return None
            
    if os.path.isfile(env_python_exe):
        return env_python_exe
    else:
        print(f"Error: Could not find python.exe in the new environment's 'Scripts' folder.")
        return None

def install_packages(venv_python_exe):
    """Installs required packages into the specified virtual environment."""
    print("\n--- Installing Packages into Virtual Environment ---")
    if not venv_python_exe or not os.path.isfile(venv_python_exe):
        print("Cannot install packages: Invalid or non-existent virtual environment Python path provided.")
        print(f"  Attempted to use: {venv_python_exe}")
        return

    print(f"Using interpreter for pip: {venv_python_exe}")
    
    # Stage 1: Install PyTorch packages
    pytorch_index_url = "https://download.pytorch.org/whl/cu128"
    pytorch_packages = ["torch", "torchaudio"]
    print(f"\n--- Installing PyTorch packages from {pytorch_index_url} ---")
    try:
        command = [venv_python_exe, '-m', 'pip', 'install', *pytorch_packages, '--index-url', pytorch_index_url]
        subprocess.run(command, check=True)
        print("Successfully installed PyTorch packages.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install PyTorch packages. Aborting.")
        return

    # Stage 2: Install remaining packages
    print("\n--- Installing remaining packages from PyPI ---")
    pypi_packages = ["demucs", "diffq", "Cython", "soundfile", "librosa", "ffmpeg-python"]
    try:
        command = [venv_python_exe, '-m', 'pip', 'install', *pypi_packages]
        subprocess.run(command, check=True)
        print("Successfully installed remaining packages.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install one or more PyPI packages.")

def setup_ffmpeg(assets_dir):
    """Handles getting 7zr, extracting FFmpeg, and returns the path to the FFmpeg bin directory."""
    print("\n--- Setting up FFmpeg ---")
    
    # Ask user if they want to provide their own path first
    if input("Do you want to provide a path to an existing FFmpeg 'bin' directory? (y/n): ").lower().startswith('y'):
        user_path = input("Enter the full path to the FFmpeg 'bin' directory: ").strip('"')
        if os.path.isdir(user_path):
            print(f"Using user-provided FFmpeg path: {user_path}")
            return user_path
        else:
            print("Invalid path provided. Proceeding with script-managed setup...")

    # If they didn't provide a path, continue with the automated setup
    seven_zip_url = 'https://www.7-zip.org/a/7zr.exe'
    seven_zip_local_path = os.path.join(assets_dir, '7zr.exe')
    seven_zip_exe_path = None

    while not seven_zip_exe_path:
        action = None
        if os.path.exists(seven_zip_local_path):
            choice = input(f"7zr.exe found. [U]se it, [d]ownload new, or [p]rovide path? (u/d/p): ").lower()
            if choice.startswith('u'):
                seven_zip_exe_path = seven_zip_local_path
            elif choice.startswith('d'):
                action = 'download'
            elif choice.startswith('p'):
                action = 'provide'
        else:
            choice = input(f"7zr.exe is needed. [D]ownload or [p]rovide path? (d/p): ").lower()
            if choice.startswith('d'):
                action = 'download'
            elif choice.startswith('p'):
                action = 'provide'
        
        if not seven_zip_exe_path and not action:
            print("Invalid choice. Please try again.")
            continue

        if action == 'download':
            try:
                print(f"Downloading 7zr.exe to '{seven_zip_local_path}'...")
                urllib.request.urlretrieve(seven_zip_url, seven_zip_local_path, _download_reporthook)
                seven_zip_exe_path = seven_zip_local_path
            except Exception as e:
                print(f"Failed to download 7zr.exe: {e}")
        elif action == 'provide':
            user_path = input("Enter full path to your 7zr.exe or 7z.exe: ").strip('"')
            if os.path.isfile(user_path) and user_path.lower().endswith('.exe'):
                seven_zip_exe_path = user_path
            else:
                print("Invalid file path.")

    ffmpeg_url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z'
    ffmpeg_archive_path = os.path.join(assets_dir, 'ffmpeg-git-full.7z')
    if not os.path.exists(ffmpeg_archive_path) or input("FFmpeg archive found. Re-download? (y/n): ").lower().startswith('y'):
        print(f"Downloading FFmpeg from {ffmpeg_url}...")
        try:
            urllib.request.urlretrieve(ffmpeg_url, ffmpeg_archive_path, _download_reporthook)
            print("FFmpeg download complete.")
        except Exception as e:
            print(f"Failed to download FFmpeg: {e}")
            return None
    else:
        print("Using existing FFmpeg archive.")

    ffmpeg_extract_path = os.path.join(assets_dir, "ffmpeg")
    if not os.path.exists(ffmpeg_extract_path) or input(f"FFmpeg folder exists. Overwrite? (y/n): ").lower().startswith('y'):
        print(f"Extracting FFmpeg to '{ffmpeg_extract_path}'...")
        try:
            extract_command = [seven_zip_exe_path, 'x', ffmpeg_archive_path, f'-o{ffmpeg_extract_path}', '-y']
            subprocess.run(extract_command, check=True, capture_output=True, text=True)
            print("FFmpeg extracted successfully.")
        except subprocess.CalledProcessError as e:
            print(f"\nAn error during FFmpeg extraction: {e.stderr}")
            return None
    else:
        print("Skipping FFmpeg extraction.")

    try:
        if not os.path.isdir(ffmpeg_extract_path):
             print(f"Error: FFmpeg extraction directory '{ffmpeg_extract_path}' does not exist.")
             return None
        # BUG FIX: Be more specific when looking for the directory
        subdirectories = [d for d in os.listdir(ffmpeg_extract_path) if os.path.isdir(os.path.join(ffmpeg_extract_path, d)) and d.startswith('ffmpeg-')]
        if not subdirectories:
            print("Error: No versioned 'ffmpeg-' subdirectory found in the FFmpeg extraction folder.")
            return None
        
        versioned_folder_name = subdirectories[0]
        potential_bin_path = os.path.join(ffmpeg_extract_path, versioned_folder_name, "bin")
        
        if os.path.isdir(potential_bin_path):
            return potential_bin_path
        else:
            print(f"Error: 'bin' directory not found inside '{versioned_folder_name}'.")
            return None
    except Exception as e:
        print(f"An unexpected error occurred while locating the FFmpeg path: {e}")
        return None

def setup_yt_dlp(assets_dir):
    """Downloads and extracts yt-dlp, returning the path to its directory."""
    print("\n--- Setting up yt-dlp ---")
    
    if input("Do you want to provide a path to an existing yt-dlp directory? (y/n): ").lower().startswith('y'):
        user_path = input("Enter the full path to the directory containing yt-dlp.exe: ").strip('"')
        if os.path.isfile(os.path.join(user_path, 'yt-dlp.exe')):
            print(f"Using user-provided yt-dlp path: {user_path}")
            return user_path
        else:
            print("Invalid path (yt-dlp.exe not found). Proceeding with script-managed setup...")

    yt_dlp_url = 'https://github.com/yt-dlp/yt-dlp/releases/download/2025.06.30/yt-dlp_win.zip'
    archive_path = os.path.join(assets_dir, 'yt-dlp_win.zip')
    extract_path = os.path.join(assets_dir, 'yt-dlp')

    if not os.path.exists(archive_path) or input("yt-dlp archive found. Re-download? (y/n): ").lower().startswith('y'):
        print(f"Downloading yt-dlp from {yt_dlp_url}...")
        try:
            urllib.request.urlretrieve(yt_dlp_url, archive_path, _download_reporthook)
            print("yt-dlp download complete.")
        except Exception as e:
            print(f"Failed to download yt-dlp: {e}")
            return None
    else:
        print("Using existing yt-dlp archive.")
    
    if not os.path.exists(extract_path) or input(f"yt-dlp folder exists. Overwrite? (y/n): ").lower().startswith('y'):
        print(f"Extracting yt-dlp to '{extract_path}'...")
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            print("yt-dlp extracted successfully.")
        except Exception as e:
            print(f"An error occurred during yt-dlp extraction: {e}")
            return None
    else:
        print("Skipping yt-dlp extraction.")

    yt_dlp_exe_path = os.path.join(extract_path, 'yt-dlp.exe')
    if os.path.isfile(yt_dlp_exe_path):
        if input("Do you want to run the yt-dlp self-updater now? (y/n): ").lower().startswith('y'):
            print(f"Running yt-dlp update command: {yt_dlp_exe_path} -U")
            try:
                subprocess.run([yt_dlp_exe_path, '-U'], check=True)
            except Exception as e:
                print(f"yt-dlp update command failed with error: {e}")
    else:
        print(f"Warning: yt-dlp.exe not found at '{yt_dlp_exe_path}'.")

    return extract_path

def create_launcher_bat(file_name, ffmpeg_path, ytdlp_path, venv_name):
    """Creates a batch file to set up the environment and activate the venv."""
    print(f"\n--- Creating Launcher: {file_name} ---")
    
    if not ffmpeg_path or not ytdlp_path:
        print("Warning: Skipping launcher creation because FFmpeg or yt-dlp path is missing.")
        return

    venv_path = os.path.join(os.getcwd(), venv_name)
    activate_script = os.path.join(venv_path, "Scripts", "activate.bat")

    if not os.path.isdir(venv_path):
        print(f"Warning: Skipping launcher creation because venv '{venv_name}' does not exist.")
        return

    bat_content = f"""@echo off
setlocal

echo Setting up environment for the '{venv_name}' project...

echo Adding FFmpeg and yt-dlp to session PATH...
set "PATH={ffmpeg_path};{ytdlp_path};%PATH%"

set "VENV_ACTIVATE_SCRIPT={activate_script}"

if not exist "%VENV_ACTIVATE_SCRIPT%" (
    echo ERROR: Virtual environment activation script not found at:
    echo %VENV_ACTIVATE_SCRIPT%
    goto :eof
)

echo.
echo Activating the '{venv_name}' Python virtual environment...
cmd /k "%VENV_ACTIVATE_SCRIPT%"

:eof
"""

    try:
        with open(file_name, "w") as f:
            f.write(bat_content)
        print(f"Successfully created '{file_name}'.")
        print("You can now run this file to set up your command prompt for the project.")
    except IOError as e:
        print(f"ERROR: Could not write to file '{file_name}': {e}")


if __name__ == "__main__":
    assets_dir = os.path.join(os.getcwd(), "downloaded_assets")
    if not os.path.exists(assets_dir):
        print(f"Creating assets directory at: {assets_dir}")
        os.makedirs(assets_dir)
    
    VENV_NAME = "data_whisper"
    base_python_exe_path = None

    while True:
        has_python = input("Do you already have a Python 3.12 version installed? (y/n): ").lower()
        if has_python.startswith('y'):
            python_version = "3.12.10"
            default_install_dir = f"C:\\bin\\python\\{python_version}"
            default_python_exe = os.path.join(default_install_dir, "python.exe")
            
            use_manual_path = True
            if os.path.isfile(default_python_exe):
                print(f"Found a Python installation in the script's default location.")
                choice = input(f"Do you want to use this one? ({default_python_exe}) (y/n): ").lower()
                if choice.startswith('y'):
                    base_python_exe_path = default_python_exe
                    use_manual_path = False
            
            if use_manual_path:
                while True:
                    user_path = input("Please enter the full path to your python.exe: ").strip('"')
                    if os.path.isfile(user_path) and user_path.lower().endswith("python.exe"):
                        base_python_exe_path = user_path
                        break
                    else:
                        print("Invalid path. Please ensure it points to a valid python.exe file.")
            break 
        elif has_python.startswith('n'):
            install_dir = install_or_reinstall_python(assets_dir)
            if install_dir:
                base_python_exe_path = os.path.join(install_dir, "python.exe")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

    venv_python_exe_path = None
    if base_python_exe_path:
         venv_python_exe_path = create_python_environment(base_python_exe_path, VENV_NAME)

    if venv_python_exe_path:
        install_packages(venv_python_exe_path)

    found_ffmpeg_bin_path = setup_ffmpeg(assets_dir)
    found_yt_dlp_path = setup_yt_dlp(assets_dir)
    
    create_launcher_bat("ffmpeg_path.bat", found_ffmpeg_bin_path, found_yt_dlp_path, VENV_NAME)

    print("\n--- Setup Summary ---")
    if base_python_exe_path and os.path.isfile(base_python_exe_path):
        print(f"Base Python executable used: {base_python_exe_path}")
    else:
        print("Base Python setup was skipped or failed.")

    if venv_python_exe_path:
        print(f"Virtual environment Python: {venv_python_exe_path}")
    else:
        print(f"Virtual environment '{VENV_NAME}' was not created or found.")
    
    if found_ffmpeg_bin_path:
        print(f"FFmpeg binaries located: {found_ffmpeg_bin_path}")
    else:
        print("FFmpeg binaries were not located.")
    
    if found_yt_dlp_path:
        print(f"yt-dlp located: {found_yt_dlp_path}")
    else:
        print("yt-dlp was not located.")
    
    print("\nSetup script finished.")