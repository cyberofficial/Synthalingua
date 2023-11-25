import os
import sys
import subprocess
import signal
import time
import whisper
import threading
import queue

# Default settings
url = "m3u8 url"
fmt = 'aac'  # the audio format extension of the stream
initial_step_s = 1  # Initial chunk size
max_step_s = 20     # Maximum chunk size
model_name = "base"

# Initialize a queue
audio_queue = queue.Queue()

# Function to transcribe audio
def transcribe_audio(file_path, model):
    try:
        result = model.transcribe(file_path)
        return result["text"]
    except RuntimeError as e:
        print(f"Error transcribing audio: {e}")
        return ""

# Thread function for processing audio files
def process_audio_queue(model):
    while True:
        file_path = audio_queue.get()
        if file_path is None:
            break  # None is used as a signal to stop the thread
        transcription = transcribe_audio(file_path, model)
        if transcription:
            print(transcription)
        os.remove(file_path)  # Clean up the processed file

# Check for Whisper model
try:
    model = whisper.load_model(model_name)
except ValueError:
    print(f"Invalid model name: {model_name}. Please choose a valid Whisper model.")
    sys.exit(1)

# Handling command line arguments
if len(sys.argv) > 1:
    url = sys.argv[1]
if len(sys.argv) > 2:
    initial_step_s = int(sys.argv[2])
if len(sys.argv) > 3:
    model_name = sys.argv[3]

# Temporary file paths
temp_dir = os.path.join(os.getcwd(), "temp")
os.makedirs(temp_dir, exist_ok=True)
temp_stream_file = os.path.join(temp_dir, f"whisper-live0.{fmt}")

# Start ffmpeg process to capture audio stream
ffmpeg_process = subprocess.Popen(
    ["ffmpeg", "-loglevel", "quiet", "-y", "-re", "-probesize", "32", "-i", url, "-c", "copy", temp_stream_file],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

print("Buffering audio. Please wait...\n")
time.sleep(initial_step_s)

running = True
def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Starting the processing thread
processing_thread = threading.Thread(target=process_audio_queue, args=(model,))
processing_thread.start()

i = 0
step_s = initial_step_s  # Current chunk size
while running:
    temp_audio_file = os.path.join(temp_dir, f"whisper-chunk-{i}.wav")
    start_time = max(0, i * step_s - 1)  # Adjust start time to avoid negative values
    subprocess.run([
        "ffmpeg", "-loglevel", "quiet", "-v", "error", "-noaccurate_seek", "-i", temp_stream_file,
        "-y", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", "-ss", str(start_time), "-t", str(step_s),
        temp_audio_file
    ])

    if os.path.exists(temp_audio_file):
        audio_queue.put(temp_audio_file)
        step_s = initial_step_s  # Reset chunk size after successful creation
    else:
        print(f"File was not created: {temp_audio_file}")
        step_s = min(step_s + 1, max_step_s)  # Increase chunk size, up to a limit

    time.sleep(step_s)
    i += 1

# Signal the processing thread to stop and wait for it to finish
audio_queue.put(None)
processing_thread.join()

# Cleanup
ffmpeg_process.terminate()
try:
    os.remove(temp_stream_file)
except OSError:
    pass
