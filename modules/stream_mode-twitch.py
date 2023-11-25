import os
import sys
import subprocess
import threading
import queue
import time
import whisper
import m3u8
import requests
import hashlib

print("Twitch Stream Loading...")
# HLS Stream URL
hls_url = "url"  # Replace with your Twitch HLS URL

# Initial Setup
model_name = "large-v3"
temp_dir = os.path.join(os.getcwd(), "temp")
os.makedirs(temp_dir, exist_ok=True)
audio_queue = queue.Queue()

# Load Whisper model
try:
    print("Loading Whisper model...")
    model = whisper.load_model(model_name)
except ValueError:
    print(f"Invalid model name: {model_name}. Please choose a valid Whisper model.")
    sys.exit(1)

# Function to transcribe audio
def transcribe_audio(file_path, model):
    try:
        result = model.transcribe(file_path)
        return result["text"]
    except RuntimeError as e:
        print(f"Error transcribing audio: {e}")
        return ""

def translate_audio(file_path, model):
    try:
        result = model.transcribe(file_path, task="translate")
        return result["text"]
    except RuntimeError as e:
        print(f"Error transcribing audio: {e}")
        return ""

# Thread function for processing audio files
def process_audio_queue(model):
    while True:
        file_path = audio_queue.get()
        if file_path is None:
            break
        #transcription = transcribe_audio(file_path, model)
        translation = translate_audio(file_path, model)
        #if transcription and translation:
        #    print(transcription + " -> " + translation)
        if translation:
            print(translation)
        os.remove(file_path)

# Start processing thread
print("Starting processing thread...")
processing_thread = threading.Thread(target=process_audio_queue, args=(model,))
processing_thread.daemon = True  # Set as daemon
processing_thread.start()

def download_segment(segment_url, output_path):
    try:
        response = requests.get(segment_url, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=16000):
                    file.write(chunk)
            return True
    except Exception as e:
        print(f"Error downloading segment: {e}")
    return False

def generate_segment_filename(url, counter):
    # Create a hash of the URL and include the counter in the filename
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(temp_dir, f"{counter:05d}_{url_hash}.ts")

# Flag for graceful shutdown
shutdown_flag = False

# Modified main loop with KeyboardInterrupt handling
try:
    downloaded_segments = set()
    counter = 0  # Initialize a counter for ordering the segments
    while not shutdown_flag:
        m3u8_obj = m3u8.load(hls_url)
        for segment in m3u8_obj.segments:
            if shutdown_flag:
                break
            if segment.uri not in downloaded_segments:
                segment_path = generate_segment_filename(segment.uri, counter)
                counter += 1  # Increment the counter for each new segment
                if download_segment(segment.absolute_uri, segment_path):
                    audio_queue.put(segment_path)
                    downloaded_segments.add(segment.uri)
                #time.sleep(1)  # Throttle downloads
except KeyboardInterrupt:
    print("Shutting down...")
    shutdown_flag = True

# Wait for the processing thread to finish
audio_queue.put(None)  # Signal the end
processing_thread.join()

# Cleanup
# Any additional cleanup if needed
