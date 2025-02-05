import speech_recognition as sr
from queue import Queue
from colorama import Fore, Style

def record_callback(_, audio: sr.AudioData, data_queue: Queue) -> None:
    """Callback function for audio recording."""
    data = audio.get_raw_data()
    data_queue.put(data)

def mic_calibration(recorder: sr.Recognizer, source: sr.Microphone, calibration_time: int):
    """Calibrate microphone for ambient noise."""
    print("Starting mic calibration...")
    recorder.adjust_for_ambient_noise(source, duration=calibration_time)
    reset_text = Style.RESET_ALL
    print(f"Calibration complete. The microphone is set to: {Fore.YELLOW}" + str(recorder.energy_threshold) + f"{reset_text}")

def handle_mic_calibration(recorder: sr.Recognizer, source: sr.Microphone, args):
    """Handle microphone calibration process with user interaction."""
    reset_text = Style.RESET_ALL
    if args.mic_calibration_time:
        print("Mic calibration flag detected.\n")
        print(f"Press {Fore.YELLOW}[enter]{reset_text} when ready to start mic calibration.\nMake sure there is no one speaking during this time.")
        if args.mic_calibration_time == 0:
            args.mic_calibration_time = 5
            mic_calibration(recorder, source, args.mic_calibration_time)
        else:
            print("Waiting for user input...")
            input()
            mic_calibration(recorder, source, args.mic_calibration_time)
            print(f"If you are happy with this setting press {Fore.YELLOW}[enter]{reset_text} or type {Fore.YELLOW}[r]{reset_text} then {Fore.YELLOW}[enter]{reset_text} to recalibrate.\n")
            while True:
                user_input = input("r/enter: ")
                if user_input == "r":
                    mic_calibration(recorder, source, args.mic_calibration_time)
                    print(f"If you are happy with this setting press {Fore.YELLOW}[enter]{reset_text} or type {Fore.YELLOW}[r]{reset_text} then {Fore.YELLOW}[enter]{reset_text} to recalibrate.\n")
                else:
                    break