from modules.imports import *
import speech_recognition as sr
import pyaudio

def is_input_device(device_index):
    pa = pyaudio.PyAudio()
    device_info = pa.get_device_info_by_index(device_index)
    return device_info['maxInputChannels'] > 0

def get_microphone_source(args):
    pa = pyaudio.PyAudio()
    available_mics = sr.Microphone.list_microphone_names()

    if args.set_microphone:
        mic_name = args.set_microphone

        if mic_name.isdigit():
            mic_index = int(mic_name)
            if mic_index in range(len(available_mics)) and is_input_device(mic_index):
                return sr.Microphone(sample_rate=16000, device_index=mic_index), available_mics[mic_index]
            else:
                raise ValueError("Invalid audio source. Please choose a valid microphone.")
        else:
            for index, name in enumerate(available_mics):
                if mic_name == name and is_input_device(index):
                    return sr.Microphone(sample_rate=16000, device_index=index), name

    for index in range(pa.get_device_count()):
        if is_input_device(index):
            return sr.Microphone(sample_rate=16000, device_index=index), "system default"

    raise ValueError("No valid input devices found.")