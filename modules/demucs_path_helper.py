# Helper for persistent Python path config for Demucs/vocal isolation
import os
import sys
import platform
import subprocess
from colorama import Fore, Style
from pathlib import Path

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
        candidate_path = Path.cwd() / 'python_embedded' / 'python.exe'
        if candidate_path.is_file() and _verify_python_version(str(candidate_path)):
            return str(candidate_path)
        # fallback to original hard‑coded path for backward compatibility
        fallback_path = r'C:\bin\Synthalingua\python_embedded\python.exe'
        if os.path.exists(fallback_path) and _verify_python_version(fallback_path):
            return fallback_path
    elif is_linux or is_macos:
        # Windows fallback now prefers a python_embedded folder in the current working directory
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
            # Show dynamic path: prefer cwd/python_embedded/python.exe if exists, else fallback path
            candidate_path = Path.cwd() / 'python_embedded' / 'python.exe'
            display_path = str(candidate_path) if candidate_path.is_file() else r'C:\bin\Synthalingua\python_embedded\python.exe'
            print(f"  - Python embedded: {display_path}")
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

def is_frozen_build() -> bool:
    """
    Return True when running from a PyInstaller build (frozen executable).

    Frozen builds ship demucs inside the executable, so no separate Python
    environment is needed and no interpreter path has to be resolved.
    """
    return bool(getattr(sys, 'frozen', False))


def get_demucs_command_prefix():
    """
    Return the leading elements of the Demucs command line.

    Frozen builds re-enter the same executable with --run-demucs-worker, which
    means vocal isolation needs no external Python environment at all. Source
    builds keep calling a Python interpreter that has demucs installed.

    Returns:
        list: Command prefix, either [<python>, '<runner script>'] for source
              builds or [<executable>, '--run-demucs-worker'] when frozen
    """
    if is_frozen_build():
        return [sys.executable, '--run-demucs-worker']
    # Source builds go through the small runner script so shipped local model
    # repos behave the same as in the frozen build (see modules/demucs_worker.py)
    runner_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demucs_worker.py')
    return [get_demucs_python_path(), runner_script]


def get_demucs_model_repo_args(model_name=None):
    """
    Return ['--repo', <path>] when the requested model ships with the app.

    Demucs resolves pretrained models from its remote repository by default,
    which needs a network connection the first time a model is used. When a
    local repo folder ships with the build (models/demucs next to the
    executable, or in the project folder), point demucs at it so vocal
    isolation works offline.

    Args are only returned when the requested model is actually present,
    otherwise demucs would fail instead of falling back to the download.

    Args:
        model_name: Demucs model name, for example 'htdemucs'

    Returns:
        list: ['--repo', <path>] or []
    """
    repo_dir = _find_local_demucs_repo(model_name)
    if repo_dir:
        return ['--repo', str(repo_dir)]
    return []


def _find_local_demucs_repo(model_name=None):
    """Locate a usable local demucs model repo folder, or return None."""
    candidates = []

    if is_frozen_build():
        # In a frozen onedir build the models folder sits next to the executable
        candidates.append(Path(sys.executable).resolve().parent / 'models' / 'demucs')
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            candidates.append(Path(meipass) / 'models' / 'demucs')

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(Path(project_root) / 'models' / 'demucs')
    candidates.append(Path.cwd() / 'models' / 'demucs')

    for candidate in candidates:
        try:
            if candidate.is_dir() and _local_repo_has_model(candidate, model_name):
                return candidate
        except OSError:
            continue

    return None


def _local_repo_has_model(repo_dir, model_name=None):
    """
    Check that a local demucs repo folder actually contains the requested model.

    Demucs model files are either named after the model itself or use the
    '<signature>-<checksum>.th' form. Bag models (htdemucs_ft, mdx and similar)
    are described by a yaml file that lists the signatures they are built from,
    and every listed signature file has to be present as well.
    """
    try:
        repo_dir = Path(repo_dir)
        if not model_name:
            return any(repo_dir.glob('*.th')) or any(repo_dir.glob('*.yaml'))

        # Single model file named after the model, optionally with a checksum
        if any(repo_dir.glob(f'{model_name}*.th')):
            return True

        bag_file = repo_dir / f'{model_name}.yaml'
        if bag_file.is_file():
            signatures = _read_bag_signatures(bag_file)
            if signatures:
                return all(any(repo_dir.glob(f'{sig}*.th')) for sig in signatures)
            # Bag could not be parsed, trust the yaml presence
            return True

        return False
    except OSError:
        return False


def _read_bag_signatures(bag_file):
    """Read the model signatures listed in a demucs bag yaml file."""
    try:
        import yaml
        bag = yaml.safe_load(bag_file.read_text(encoding='utf-8')) or {}
        return bag.get('models') or []
    except Exception:
        return []


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
