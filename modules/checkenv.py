import sys
import os

def get_base_prefix_compat():
    """Get base/real prefix, or sys.prefix if there is none."""
    return (
        getattr(sys, "base_prefix", None)
        or getattr(sys, "real_prefix", None)
        or sys.prefix
    )

def in_virtualenv():
    return sys.prefix != get_base_prefix_compat()

def check_os():
    if os.name == 'nt':
        return 'windows'
    elif os.name == 'posix':
        return 'linux'
    else:
        return 'unknown'

def env_message():
    print("Not in Virtual Environment, please make sure you are in a virtual environment before running this script.")
    import os
    current_os = check_os()
    if current_os == 'windows':
        print("Since you are on windows, run livetranslation.bat")
    elif current_os == 'linux':
        print("Since you are on linux, run livetranslation.sh")
    else:
        print("Since you are on an unknown OS, activate the virtual environment and run livetranslation.py")
    import sys
    sys.exit(1)

current_os = check_os()
if current_os == 'windows':
    os.system('cls')
elif current_os == 'linux':
    os.system('clear')

print("Check ENV Module Loaded")
print("Checking if you are in a virtual environment...\n\n")