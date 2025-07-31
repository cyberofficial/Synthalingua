"""
Device management module for audio input and processing devices.

This module handles the configuration and management of both audio input devices
(microphones) and processing devices (CPU/CUDA/iGPU/dGPU/NPU). It provides functionality for:
- Detecting and selecting microphone devices
- Managing CUDA device selection for GPU processing
- Validating device configurations
- Listing available audio devices
"""

import torch
import re
import speech_recognition as sr
import pyaudio
import openvino as ov
from prettytable import PrettyTable
from colorama import Fore, Style
import sys

def is_input_device(device_index):
    """
    Check if the device at given index is a valid input device.

    Args:
        device_index (int): Index of the audio device to check

    Returns:
        bool: True if device is an input device, False otherwise    """
    pa = pyaudio.PyAudio()
    device_info = pa.get_device_info_by_index(device_index)
    max_input_channels = device_info['maxInputChannels']
    
    # Ensure we have a numeric value for comparison
    if isinstance(max_input_channels, (int, float)):
        return max_input_channels > 0
    else:
        # If it's not numeric, try to convert it
        try:
            return int(max_input_channels) > 0
        except (ValueError, TypeError):
            return False

def get_microphone_source(args):
    """
    Get microphone sources based on provided command line arguments.

    Attempts to find and configure two separate microphone sources based on the provided
    arguments. Falls back to system default if no specific microphone is specified.

    Args:
        args: Command line arguments containing microphone settings

    Returns:
        tuple: (sr.Microphone, sr.Microphone, str) - Two configured microphone objects and device name    Raises:
        ValueError: If no valid input devices are found
    """
    pa = pyaudio.PyAudio()
    available_mics = sr.Microphone.list_microphone_names()
    device_index = None
    mic_name = "system default"

    if args.set_microphone:
        mic_name = args.set_microphone

        if mic_name.isdigit():
            mic_index = int(mic_name)
            if mic_index in range(len(available_mics)) and is_input_device(mic_index):
                device_index = mic_index
                mic_name = available_mics[mic_index]
            else:
                print("Invalid audio source. Please choose a valid microphone.")
                sys.exit(0)
        else:
            for index, name in enumerate(available_mics):
                if mic_name == name and is_input_device(index):
                    device_index = index
                    break

    if device_index is None:
        for index in range(pa.get_device_count()):
            if is_input_device(index):
                device_index = index
                break

    if device_index is None:
        raise ValueError("No valid input devices found.")    # Create two separate microphone instances with enhanced quality settings
    # Using 48000 Hz sample rate for better audio quality (professional standard)
    # This provides better frequency response and less aliasing
    # Added chunk_size=4096 for higher quality audio capture (larger buffer = better quality)
    source_calibration = sr.Microphone(
        sample_rate=48000, 
        device_index=device_index,
        chunk_size=4096  # Larger chunk size for better audio quality
    )
    source_listening = sr.Microphone(
        sample_rate=48000, 
        device_index=device_index,
        chunk_size=4096  # Larger chunk size for better audio quality
    )
    
    return source_calibration, source_listening, mic_name

def list_microphones():
    """
    List all available microphone devices in a formatted table.

    Displays a table of available microphone devices with their indices and names.
    Only shows devices that are valid input devices.
    Exits the program after displaying the list.
    """
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
    """
    Set up and configure the processing device (CPU/CUDA/iGPU/dGPU/NPU).

    Configures the processing device based on availability and user preferences.
    Handles CUDA device selection when multiple GPUs are available.
    General flow of the device setup:
        Declare model_source with checks ->
        Declare device with checks ->
        If device is not stated, default to highest preforming supported device.

    Args:
        args: Command line arguments containing device preferences

    Returns:
        object: Configured processing device

    Note:
        Prints relevant device information including VRAM availability for CUDA devices.
        The OpenVino backend only accepts devices in full caps (ex. GPU.1, NPU.2, CPU.0)
        Full info on how OpenVINO handles devices: https://docs.openvino.ai/2025/openvino-workflow/running-inference/inference-devices-and-modes/gpu-device.html.
        Full list of supported OpenVINO devices: https://docs.openvino.ai/2025/about-openvino/release-notes-openvino/system-requirements.html
    """
    # Default device priority (NPU -> dGPU -> iGPU -> CPU)
    if args.model_source == "openvino":
        core = ov.Core()
        devices = core.available_devices

        if not devices:
            raise ValueError(f"No valid devices found for OpenVINO. Please pick another --model_source.")

        # Convert CPU.0/GPU.0/NPU.0 to more easily handled CPU/GPU/NPU
        devices = [x.removesuffix(".0") for x in devices]
        device = args.device.lower()
        dedicated = ov.properties.device.Type.DISCRETE
        integrated = ov.properties.device.Type.INTEGRATED

        if device == "cuda":
            print("OpenVINO does not support CUDA devices. Falling back to default device.")
        # Input is a specific device (ex. CPU.0, GPU.5)
        elif re.match(device.upper(), r"^(CPU|GPU|NPU)(\.\d+)$"):
            # Raise device case to match OpenVINO devices case (gpu.2 -> GPU.2)
            _device = device.upper().removesuffix(".0")
            if _device in devices:
                return _device
        elif device == "cpu":
            if "CPU" in devices:
                return "CPU"
        elif device == "intel-igpu":
            if "GPU" in devices and core.get_property("GPU", "DEVICE_TYPE") == integrated:
                return "GPU"
        elif device == "intel-dgpu":
            for _device in devices:
                if _device.startswith("GPU") and core.get_property(_device, "DEVICE_TYPE") == dedicated:
                    return _device
        elif device == "intel-npu":
            if "NPU" in devices:
                return "NPU"
        elif device != "auto":
            raise ValueError(f"\"{args.device}\" is not an valid device for OpenVINO. Please pick another --device.")

        print("Setting default device")

        priority = 0
        best_device = "CPU"
        for _device in devices:
            if _device.startswith("NPU"):
                return _device
            device_type = core.get_property(_device, "DEVICE_TYPE")
            if _device.startswith("GPU") and device_type == dedicated:
                priority = 2
                best_device = _device
            elif _device.startswith("GPU") and device_type == integrated and priority < 1:
                priority = 1
                best_device = _device
        return best_device
    # Since Whisper and FasterWhisper both have similar accepted devices, device selection can be combined
    # Default device priority (CUDA (Nvidia GPU) -> CPU)
    elif args.model_source == "whisper" or args.model_source == "fasterwhisper":
        device = args.device.lower()

        if device != "auto" and device != "cuda" and device != "cpu":
            raise ValueError(f"\"{args.device}\" is not a valid device for {args.model_source}.")

        if device == "cpu":
            return "cpu"

        if device == "cuda" and not torch.cuda.is_available():
            print("CUDA was chosen but it is not available. Reverting to cpu")
            return "cpu"

        print("Setting default device")

        if not torch.cuda.is_available():
            return "cpu"

        cuda_device_count = torch.cuda.device_count()
        if cuda_device_count > 1 and args.cuda_device == 0:
            selected_device = select_cuda_device(cuda_device_count)
        else:
            selected_device = args.cuda_device

        torch.cuda.set_device(selected_device)
        print(f"CUDA device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
        print(f"VRAM available: {torch.cuda.get_device_properties(torch.cuda.current_device()).total_memory / 1024 / 1024} MB")

        if "AMD" in torch.cuda.get_device_name(torch.cuda.current_device()):
            print("WARNING: You are using an AMD GPU with CUDA. This may not work properly. Consider using CPU instead.")

        return "cuda"
    raise ValueError(f"\"{args.model_source}\" is not a valid model source")

def select_cuda_device(cuda_device_count):
    """
    Interactive CUDA device selection when multiple devices are available.

    Presents a list of available CUDA devices with their names and VRAM,
    allowing the user to select a specific device.

    Args:
        cuda_device_count (int): Number of available CUDA devices

    Returns:
        int: Index of the selected CUDA device

    Note:
        Continues prompting until a valid device is selected.
    """
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