import sys
import ctypes

def set_window_title(detected_language, confidence, model):
    title = f"Model: {model} - {detected_language} [{confidence:.2f}%]"

    if sys.platform == "win32":
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    else:
        sys.stdout.write(f"]2;{title}")
        sys.stdout.flush()

print("Console Settings Module Loaded")