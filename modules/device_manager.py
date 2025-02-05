import torch
import speech_recognition as sr
import pyaudio
from prettytable import PrettyTable
from colorama import Fore, Style
import sys

def is_input_device(device_index):
    """Check if the device at given index is an input device."""
    pa = pyaudio.PyAudio()
    device_info = pa.get_device_info_by_index(device_index)
    return device_info['maxInputChannels'] > 0

def get_microphone_source(args):
    """Get microphone source based on provided arguments."""
    pa = pyaudio.PyAudio()
    available_mics = sr.Microphone.list_microphone_names()

    if args.set_microphone:
        mic_name = args.set_microphone

        if mic_name.isdigit():
            mic_index = int(mic_name)
            if mic_index in range(len(available_mics)) and is_input_device(mic_index):
                return sr.Microphone(sample_rate=16000, device_index=mic_index), available_mics[mic_index]
            else:
                print("Invalid audio source. Please choose a valid microphone.")
                sys.exit(0)
        else:
            for index, name in enumerate(available_mics):
                if mic_name == name and is_input_device(index):
                    return sr.Microphone(sample_rate=16000, device_index=index), name

    for index in range(pa.get_device_count()):
        if is_input_device(index):
            return sr.Microphone(sample_rate=16000, device_index=index), "system default"

    raise ValueError("No valid input devices found.")

def list_microphones():
    """List all available microphone devices."""
    print("Available microphone devices are: ")
    mic_table = PrettyTable()
    mic_table.field_names = ["Index", "Microphone Name"]

    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        if is_input_device(index):
            mic_table.add_row([index, name])

    print(mic_table)
    reset_text = Style.RESET_ALL
    input(f"Press {Fore.YELLOW}[enter]{reset_text} to exit.")
    sys.exit(0)

def setup_device(args):
    """Set up and configure the processing device (CPU/CUDA)."""
    if args.device:
        device = torch.device(args.device)
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if args.device == "cuda" and not torch.cuda.is_available():
            print("WARNING: CUDA was chosen but it is not available. Falling back to CPU.")
    print(f"Using device: {device}")

    if device.type == "cuda":
        cuda_device_count = torch.cuda.device_count()
        if cuda_device_count > 1 and args.cuda_device == 0:
            selected_device = select_cuda_device(cuda_device_count)
        else:
            selected_device = args.cuda_device

        torch.cuda.set_device(selected_device)
        print(f"CUDA device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
        print(f"VRAM available: {torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / 1024 / 1024} MB")

    return device

def select_cuda_device(cuda_device_count):
    """Select CUDA device when multiple devices are available."""
    while True:
        print("Multiple CUDA devices detected. Please choose a device:")
        for i in range(cuda_device_count):
            print(f"{i}: {torch.cuda.get_device_name(i)}, VRAM: {torch.cuda.get_device_properties(i).total_memory / 1024 / 1024} MB")
        try:
            selected_device = int(input("Enter the device number: "))
            if 0 <= selected_device < cuda_device_count:
                return selected_device
            else:
                print("Invalid device number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a valid device number.")