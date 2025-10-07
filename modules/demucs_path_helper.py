# Helper for persistent Python path config for Demucs/vocal isolation
import os
from colorama import Fore, Style

def get_demucs_python_path():
    """
    Returns the path to the python.exe for Demucs, using the following order:
    1. If a config file exists and is valid, use it.
    2. Try Python embedded path (from set_up_env.py setup).
    3. Try local data_whisper path (for development builds).
    4. Try legacy miniconda path.
    5. Prompt the user for the path, validate, and save it for future runs.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'demucs_python_path.txt')
    
    # 1. Check config file
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_path = f.read().strip()
            if user_path and os.path.exists(user_path) and user_path.lower().endswith('python.exe'):
                return user_path
            else:
                print(f"{Fore.YELLOW}  Saved Python path in config is invalid: {user_path}{Style.RESET_ALL}")
    
    # 2. Check Python embedded path (primary for end users)
    python_embedded_path = r'C:\bin\Synthalingua\python_embedded\python.exe'
    if os.path.exists(python_embedded_path):
        return python_embedded_path

    # 3. Check default local data_whisper path (for development builds)
    local_path = os.path.join(project_root, 'data_whisper', 'Scripts', 'python.exe')
    if os.path.exists(local_path):
        return local_path

    # 4. Check legacy miniconda path (backwards compatibility)
    win_miniconda_path = r'C:\bin\Synthalingua\miniconda\envs\data_whisper\python.exe'
    if os.path.exists(win_miniconda_path):
        return win_miniconda_path

    # 5. Prompt user
    while True:
        print(f"{Fore.RED}The required Python interpreter for Demucs was not found in the default locations.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Expected locations:{Style.RESET_ALL}")
        print(f"  - Python embedded: C:\\bin\\Synthalingua\\python_embedded\\python.exe")
        print(f"  - Development: {local_path}")
        print(f"  - Legacy miniconda: C:\\bin\\Synthalingua\\miniconda\\envs\\data_whisper\\python.exe")
        user_path = input(f"\nPlease enter the full path to your Python interpreter with demucs installed: ").strip()
        if os.path.exists(user_path) and user_path.lower().endswith('python.exe'):
            # Save to config for future runs
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(user_path)
            print(f"{Fore.GREEN} Saved Python path for future runs: {user_path}{Style.RESET_ALL}")
            return user_path
        else:
            print(f"{Fore.RED} Invalid path. Please try again. Must be a valid python.exe file.{Style.RESET_ALL}")
