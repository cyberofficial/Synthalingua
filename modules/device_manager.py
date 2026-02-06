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
import math
import audioop
import time

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
    List all available microphone devices in a formatted table with detailed information.

    Displays a comprehensive table of available microphone devices with their indices,
    names, sample rates, and channel information. Only shows devices that are valid 
    input devices. Provides clear instructions for device selection.
    Exits the program after displaying the list.
    """
    pa = pyaudio.PyAudio()
    
    # Print header with styling
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{Style.RESET_ALL}           {Fore.YELLOW}AVAILABLE AUDIO INPUT DEVICES (MICROPHONES){Style.RESET_ALL}                  {Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    print("=" * 80 + "\n")
    
    # Create enhanced table
    mic_table = PrettyTable()
    mic_table.field_names = [
        f"{Fore.GREEN}Device ID{Style.RESET_ALL}", 
        f"{Fore.GREEN}Device Name{Style.RESET_ALL}",
        f"{Fore.GREEN}Channels{Style.RESET_ALL}",
        f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}"
    ]
    mic_table.align[f"{Fore.GREEN}Device ID{Style.RESET_ALL}"] = "c"
    mic_table.align[f"{Fore.GREEN}Device Name{Style.RESET_ALL}"] = "l"
    mic_table.align[f"{Fore.GREEN}Channels{Style.RESET_ALL}"] = "c"
    mic_table.align[f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}"] = "c"
    
    device_count = 0
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        if is_input_device(index):
            try:
                device_info = pa.get_device_info_by_index(index)
                channels = int(device_info.get('maxInputChannels', 0))
                sample_rate = int(device_info.get('defaultSampleRate', 0))
                
                mic_table.add_row([
                    f"{Fore.YELLOW}{index}{Style.RESET_ALL}",
                    name[:60] + "..." if len(name) > 60 else name,
                    f"{channels} ch",
                    f"{sample_rate} Hz"
                ])
                device_count += 1
            except Exception as e:
                # If we can't get device info, still show basic info
                mic_table.add_row([
                    f"{Fore.YELLOW}{index}{Style.RESET_ALL}",
                    name[:60] + "..." if len(name) > 60 else name,
                    "N/A",
                    "N/A"
                ])
                device_count += 1
    
    print(mic_table)
    
    # Print usage instructions
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}USAGE INSTRUCTIONS:{Style.RESET_ALL}")
    print(f"  • To select a microphone, use the {Fore.YELLOW}Device ID{Style.RESET_ALL} (the number in the first column)")
    print(f"  • Example: {Fore.GREEN}--set_microphone 0{Style.RESET_ALL}")
    print(f"  • {Fore.RED}Do NOT use the device name{Style.RESET_ALL}, only use the {Fore.YELLOW}Device ID number{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}DEVICE INFORMATION:{Style.RESET_ALL}")
    print(f"  • {Fore.YELLOW}Channels:{Style.RESET_ALL} Number of input channels (1=Mono, 2=Stereo, etc.)")
    print(f"  • {Fore.YELLOW}Sample Rate:{Style.RESET_ALL} Audio sampling frequency (higher = better quality)")
    print(f"  • {Fore.YELLOW}Device ID:{Style.RESET_ALL} Lower IDs typically have faster response times and lower latency")
    print(f"  • Total devices found: {Fore.GREEN}{device_count}{Style.RESET_ALL}")
    print("=" * 80 + "\n")
    
    pa.terminate()
    
    reset_text = Style.RESET_ALL
    input(f"Press {Fore.YELLOW}[Enter]{reset_text} to exit...")
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

def detect_sound():
    """
    Monitor all available audio input devices for sound detection and display dB levels.

    Continuously monitors all input devices simultaneously, calculating RMS levels and
    converting to dB. Shows which devices are detecting sound above threshold with their
    dB levels. Displays device list first like --list_microphones, then monitors continuously
    until interrupted with Ctrl+C.

    Runs continuously until interrupted.
    """
    pa = pyaudio.PyAudio()

    # Get list of input devices
    input_devices = []
    device_names = sr.Microphone.list_microphone_names()
    for index in range(pa.get_device_count()):
        if is_input_device(index):
            input_devices.append(index)

    if not input_devices:
        print("No input devices found.")
        pa.terminate()
        sys.exit(1)

    # Print header and device table (similar to list_microphones)
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{Style.RESET_ALL}           {Fore.YELLOW}AVAILABLE AUDIO INPUT DEVICES (MICROPHONES){Style.RESET_ALL}                  {Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
    print("=" * 80 + "\n")

    # Create table
    mic_table = PrettyTable()
    mic_table.field_names = [
        f"{Fore.GREEN}Device ID{Style.RESET_ALL}",
        f"{Fore.GREEN}Device Name{Style.RESET_ALL}",
        f"{Fore.GREEN}Channels{Style.RESET_ALL}",
        f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}"
    ]
    mic_table.align[f"{Fore.GREEN}Device ID{Style.RESET_ALL}"] = "c"
    mic_table.align[f"{Fore.GREEN}Device Name{Style.RESET_ALL}"] = "l"
    mic_table.align[f"{Fore.GREEN}Channels{Style.RESET_ALL}"] = "c"
    mic_table.align[f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}"] = "c"

    for index in input_devices:
        try:
            device_info = pa.get_device_info_by_index(index)
            channels = int(device_info.get('maxInputChannels', 0))
            sample_rate = int(device_info.get('defaultSampleRate', 0))
            name = device_names[index] if index < len(device_names) else f"Device {index}"

            mic_table.add_row([
                f"{Fore.YELLOW}{index}{Style.RESET_ALL}",
                name[:60] + "..." if len(name) > 60 else name,
                f"{channels} ch",
                f"{sample_rate} Hz"
            ])
        except Exception as e:
            name = device_names[index] if index < len(device_names) else f"Device {index}"
            mic_table.add_row([
                f"{Fore.YELLOW}{index}{Style.RESET_ALL}",
                name[:60] + "..." if len(name) > 60 else name,
                "N/A",
                "N/A"
            ])

    print(mic_table)
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}SOUND DETECTION:{Style.RESET_ALL}")
    print(f"  • Monitoring all devices for sound detection")
    print(f"  • Shows Device ID and dB level when sound is detected")
    print(f"  • Press {Fore.YELLOW}Ctrl+C{Style.RESET_ALL} to stop monitoring")
    print("=" * 80 + "\n")

    # Open streams for each device
    streams = []
    for device_index in input_devices:
        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,  # mono
                rate=44100,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            streams.append((device_index, stream))
        except Exception as e:
            print(f"Warning: Could not open stream for device {device_index}: {e}")
            continue

    if not streams:
        print("No devices could be opened for monitoring.")
        pa.terminate()
        sys.exit(1)

    print(">>> Listening to devices...")

    # Track devices that have been detected as active during the session (device_id -> hit_count)
    active_device_hits = {}

    try:
        while True:
            active_devices = {}

            # Read from each stream
            for device_index, stream in streams:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    if len(data) > 0:
                        # Calculate RMS
                        rms = audioop.rms(data, 2)  # 2 bytes per sample (16-bit)

                        # Convert to dB (reference level for 16-bit is 32767)
                        if rms > 0:
                            db = 20 * math.log10(rms / 32767.0)
                            # Only report if above threshold (around -50 dB is quiet)
                            if db > -50:
                                active_devices[device_index] = int(db)
                                # Track hit count for this device
                                active_device_hits[device_index] = active_device_hits.get(device_index, 0) + 1
                except Exception as e:
                    # Skip problematic devices
                    continue

            # Display active devices
            if active_devices:
                active_list = " - ".join(f"{id}({db}dB)" for id, db in sorted(active_devices.items()))
                print(f"There is sound being detected on: {active_list}")
            else:
                print("No sound detected on any device.")

            time.sleep(1)  # Update every second

    except KeyboardInterrupt:
        print("\nStopping sound detection...")

    finally:
        # Clean up streams
        for _, stream in streams:
            try:
                stream.stop_stream()
                stream.close()
            except:
                pass
        pa.terminate()

    # Display summary of active devices
    if active_device_hits:
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}         {Fore.GREEN}ACTIVE AUDIO INPUT DEVICES DETECTED{Style.RESET_ALL}                    {Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
        print("=" * 80 + "\n")

        # Create summary table for active devices only, sorted by hit count (most active first)
        active_table = PrettyTable()
        active_table.field_names = [
            f"{Fore.GREEN}Device ID{Style.RESET_ALL}",
            f"{Fore.GREEN}Device Name{Style.RESET_ALL}",
            f"{Fore.GREEN}Channels{Style.RESET_ALL}",
            f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}",
            f"{Fore.GREEN}Hit Count{Style.RESET_ALL}"
        ]
        active_table.align[f"{Fore.GREEN}Device ID{Style.RESET_ALL}"] = "c"
        active_table.align[f"{Fore.GREEN}Device Name{Style.RESET_ALL}"] = "l"
        active_table.align[f"{Fore.GREEN}Channels{Style.RESET_ALL}"] = "c"
        active_table.align[f"{Fore.GREEN}Sample Rate{Style.RESET_ALL}"] = "c"
        active_table.align[f"{Fore.GREEN}Hit Count{Style.RESET_ALL}"] = "c"

        # Sort by hit count (descending) to show most active devices first
        for device_index in sorted(active_device_hits.keys(), key=lambda x: active_device_hits[x], reverse=True):
            try:
                device_info = pa.get_device_info_by_index(device_index)
                channels = int(device_info.get('maxInputChannels', 0))
                sample_rate = int(device_info.get('defaultSampleRate', 0))
                name = device_names[device_index] if device_index < len(device_names) else f"Device {device_index}"
                hit_count = active_device_hits[device_index]

                active_table.add_row([
                    f"{Fore.YELLOW}{device_index}{Style.RESET_ALL}",
                    name[:50] + "..." if len(name) > 50 else name,  # Shortened for hit count column
                    f"{channels} ch",
                    f"{sample_rate} Hz",
                    f"{Fore.RED}{hit_count}{Style.RESET_ALL}"
                ])
            except Exception as e:
                name = device_names[device_index] if device_index < len(device_names) else f"Device {device_index}"
                hit_count = active_device_hits[device_index]
                active_table.add_row([
                    f"{Fore.YELLOW}{device_index}{Style.RESET_ALL}",
                    name[:50] + "..." if len(name) > 50 else name,
                    "N/A",
                    "N/A",
                    f"{Fore.RED}{hit_count}{Style.RESET_ALL}"
                ])

        print(active_table)
        print(f"\n{Fore.CYAN}SUMMARY:{Style.RESET_ALL}")
        print(f"  • {Fore.GREEN}{len(active_device_hits)}{Style.RESET_ALL} device(s) detected sound during monitoring")
        print(f"  • Devices are sorted by activity level (most active first)")
        print(f"  • These devices can be used with {Fore.GREEN}--set_microphone <ID>{Style.RESET_ALL}")
        print("=" * 80)
    else:
        print(f"\n{Fore.YELLOW}No devices detected sound during the monitoring session.{Style.RESET_ALL}")

    print("Sound detection stopped.")
    reset_text = Style.RESET_ALL
    input(f"Press {Fore.YELLOW}[Enter]{reset_text} to exit...")
    sys.exit(0)
