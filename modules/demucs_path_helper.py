# Helper for persistent Python path config for Demucs/vocal isolation
import os
import sys
import platform
import subprocess
from colorama import Fore, Style

def get_demucs_python_path():
    """
    Returns the path to the Python executable for Demucs, using the following order:
    1. If a config file exists and is valid, use it.
    2. Try Python embedded path (from set_up_env.py setup) - OS-specific.
    3. Try local data_whisper path (for development builds) - OS-specific.
    4. Try legacy miniconda path (backwards compatibility) - OS-specific.
    5. Try system Python with demucs installed.
    6. Prompt the user for the path, validate, and save it for future runs.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'demucs_python_path.txt')
    
    # Detect OS
    is_windows = platform.system().lower() == 'windows'
    is_linux = platform.system().lower() == 'linux'
    is_macos = platform.system().lower() == 'darwin'
    
    # 1. Check config file
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_path = f.read().strip()
            if user_path and os.path.exists(user_path) and _is_valid_python_executable(user_path, is_windows):
                return user_path
            else:
                print(f"{Fore.YELLOW}  Saved Python path in config is invalid: {user_path}{Style.RESET_ALL}")
    
    # 2. Check Python embedded path (primary for end users) - OS-specific
    if is_windows:
        python_embedded_path = r'C:\bin\Synthalingua\python_embedded\python.exe'
        if os.path.exists(python_embedded_path) and _verify_python_version(python_embedded_path):
            return python_embedded_path
    elif is_linux or is_macos:
        # Linux/macOS embedded Python paths
        linux_embedded_paths = [
            '/usr/local/bin/Synthalingua/python_embedded/bin/python3.12',
            '/usr/local/bin/Synthalingua/python_embedded/bin/python3',
            '/opt/Synthalingua/python_embedded/bin/python3.12',
            '/opt/Synthalingua/python_embedded/bin/python3',
            os.path.expanduser('~/Synthalingua/python_embedded/bin/python3.12'),
            os.path.expanduser('~/Synthalingua/python_embedded/bin/python3'),
        ]
        for path in linux_embedded_paths:
            if os.path.exists(path) and _verify_python_version(path):
                return path

    # 3. Check default local data_whisper path (for development builds) - OS-specific
    if is_windows:
        local_path = os.path.join(project_root, 'data_whisper', 'Scripts', 'python.exe')
        if os.path.exists(local_path) and _verify_python_version(local_path):
            return local_path
    elif is_linux or is_macos:
        local_paths = [
            os.path.join(project_root, 'data_whisper', 'bin', 'python3.12'),
            os.path.join(project_root, 'data_whisper', 'bin', 'python3'),
            os.path.join(project_root, 'data_whisper', 'bin', 'python'),
        ]
        for path in local_paths:
            if os.path.exists(path) and _verify_python_version(path):
                return path

    # 4. Check legacy miniconda path (backwards compatibility) - OS-specific
    if is_windows:
        win_miniconda_path = r'C:\bin\Synthalingua\miniconda\envs\data_whisper\python.exe'
        if os.path.exists(win_miniconda_path) and _verify_python_version(win_miniconda_path):
            return win_miniconda_path
    elif is_linux or is_macos:
        linux_miniconda_paths = [
            '/usr/local/bin/Synthalingua/miniconda/envs/data_whisper/bin/python3.12',
            '/usr/local/bin/Synthalingua/miniconda/envs/data_whisper/bin/python3',
            '/opt/Synthalingua/miniconda/envs/data_whisper/bin/python3.12',
            '/opt/Synthalingua/miniconda/envs/data_whisper/bin/python3',
            os.path.expanduser('~/miniconda3/envs/data_whisper/bin/python3.12'),
            os.path.expanduser('~/miniconda3/envs/data_whisper/bin/python3'),
        ]
        for path in linux_miniconda_paths:
            if os.path.exists(path) and _verify_python_version(path):
                return path

    # 5. Try system Python with demucs installed
    system_python = _find_system_python_with_demucs()
    if system_python:
        return system_python

    # 6. Prompt user
    while True:
        print(f"{Fore.RED}The required Python interpreter for Demucs was not found in the default locations.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Expected locations:{Style.RESET_ALL}")
        
        if is_windows:
            print(f"  - Python embedded: C:\\bin\\Synthalingua\\python_embedded\\python.exe")
            print(f"  - Development: {os.path.join(project_root, 'data_whisper', 'Scripts', 'python.exe')}")
            print(f"  - Legacy miniconda: C:\\bin\\Synthalingua\\miniconda\\envs\\data_whisper\\python.exe")
            print(f"  - System Python: python.exe in PATH with demucs installed")
        elif is_linux or is_macos:
            print(f"  - Python embedded: /usr/local/bin/Synthalingua/python_embedded/bin/python3.12")
            print(f"  - Development: {os.path.join(project_root, 'data_whisper', 'bin', 'python3.12')}")
            print(f"  - Legacy miniconda: ~/miniconda3/envs/data_whisper/bin/python3.12")
            print(f"  - System Python: python3.12 in PATH with demucs installed")
        
        user_path = input(f"\nPlease enter the full path to your Python 3.12.x interpreter with demucs installed: ").strip()
        if os.path.exists(user_path) and _is_valid_python_executable(user_path, is_windows) and _verify_python_version(user_path):
            # Save to config for future runs
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(user_path)
            print(f"{Fore.GREEN} Saved Python path for future runs: {user_path}{Style.RESET_ALL}")
            return user_path
        else:
            print(f"{Fore.RED} Invalid path. Please try again. Must be a valid Python 3.12.x executable.{Style.RESET_ALL}")

def _is_valid_python_executable(path, is_windows):
    """Check if the path is a valid Python executable based on OS."""
    if is_windows:
        return path.lower().endswith(('.exe', 'python.exe', 'python3.exe'))
    else:
        # Linux/macOS - check if it's executable and named python*
        basename = os.path.basename(path).lower()
        return ('python' in basename) and os.access(path, os.X_OK)

def _verify_python_version(python_path):
    """Verify that the Python executable is version 3.12.x."""
    try:
        result = subprocess.run(
            [python_path, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_output = result.stdout.strip() if result.stdout else result.stderr.strip()
        # Parse version like "Python 3.12.10"
        if 'Python 3.12.' in version_output:
            return True
        else:
            return False
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False

def _find_system_python_with_demucs():
    """Try to find system Python 3.12.x with demucs installed."""
    is_windows = platform.system().lower() == 'windows'
    
    # Try common Python 3.12 command names
    python_commands = ['python3.12', 'python3', 'python'] if not is_windows else ['python.exe', 'python3.exe']
    
    for cmd in python_commands:
        try:
            # Check if command exists and get its path
            result = subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            version_output = result.stdout.strip() if result.stdout else result.stderr.strip()
            if 'Python 3.12.' not in version_output:
                continue
            
            # Get the actual path to the Python executable
            path_result = subprocess.run(
                [cmd, '-c', 'import sys; print(sys.executable)'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if path_result.returncode == 0:
                python_path = path_result.stdout.strip()
                
                # Check if demucs is installed
                demucs_check = subprocess.run(
                    [python_path, '-c', 'import demucs'],
                    capture_output=True,
                    timeout=5
                )
                
                if demucs_check.returncode == 0:
                    print(f"{Fore.GREEN} Found system Python 3.12.x with demucs installed: {python_path}{Style.RESET_ALL}")
                    return python_path
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            continue
    
    return None
