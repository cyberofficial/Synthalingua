# Helper for persistent data_whisper Python path config
import os
from colorama import Fore, Style

def get_demucs_python_path():
    """
    Returns the path to the python.exe for Demucs, using the following order:
    1. If a config file exists and is valid, use it.
    2. If not, try the default local path.
    3. If not, prompt the user for the path, validate, and save it for future runs.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, 'data_whisper_path.txt')
    
    # 1. Check config file
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            user_path = f.read().strip()
            if user_path and os.path.exists(user_path) and user_path.lower().endswith('python.exe'):
                return user_path
            else:
                print(f"{Fore.YELLOW}⚠️  Saved data_whisper path in config is invalid: {user_path}{Style.RESET_ALL}")
    
    # 2. Check default local path
    local_path = os.path.join(project_root, 'data_whisper', 'Scripts', 'python.exe')
    if os.path.exists(local_path):
        return local_path

    # 2b. Check known Windows miniconda path
    win_miniconda_path = r'C:\bin\Synthalingua\miniconda\envs\data_whisper\python.exe'
    if os.path.exists(win_miniconda_path):
        return win_miniconda_path

    # 3. Prompt user
    while True:
        print(f"{Fore.RED}The required Python interpreter for Demucs was not found in the default locations.{Style.RESET_ALL}")
        user_path = input(f"Please enter the full path to your data_whisper python.exe (e.g. C:\\bin\\Synthalingua\\miniconda\\envs\\data_whisper\\python.exe): ").strip()
        if os.path.exists(user_path) and user_path.lower().endswith('python.exe'):
            # Save to config for future runs
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(user_path)
            print(f"{Fore.GREEN}✅ Saved data_whisper python path for future runs: {user_path}{Style.RESET_ALL}")
            return user_path
        else:
            print(f"{Fore.RED}❌ Invalid path. Please try again. Must be a valid python.exe file.{Style.RESET_ALL}")
