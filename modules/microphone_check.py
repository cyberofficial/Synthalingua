from speech_recognition.__main__ import r

from modules.imports import *

print("Microphone Check Module Loaded")
def microphone_check():
    # Check if the user has a microphone
    print("Checking for microphone...")
    mic = sr.Microphone()
    with mic as source:
        r.adjust_for_ambient_noise(source)
    print("Microphone check complete.")
    print("\n\n")
    return True

