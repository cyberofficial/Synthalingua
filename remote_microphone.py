import pyaudio
import subprocess
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import sys

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
OUTPUT_DIR = "hls_segments"
PLAYLIST_NAME = "index.m3u8"
SERVER_PORT = 8888  # Default

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Synchronization mechanism
playlist_ready = threading.Event()


def list_audio_devices():
    p = pyaudio.PyAudio()
    print("Available audio devices:")
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        print(f"{i}: {device_info['name']}")


def get_input_device_index():
    while True:
        try:
            print("\n\n\n\nEnter the index of the microphone input device.\n"
                  "Remember this script may not work for all devices.\n"
                  "The lower the index, the better the quality of the audio.\n")
            index = int(input("Enter the index of the microphone input device: "))
            return index
        except ValueError:
            print("Invalid input. Please enter a valid index.")


def capture_audio(device_index):
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=device_index)

    print("* recording")

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        "-ac", str(CHANNELS),
        "-ar", str(RATE),
        "-i", "pipe:0",
        "-f", "hls",
        "-hls_time", "3",
        "-hls_list_size", "6",
        os.path.join(OUTPUT_DIR, PLAYLIST_NAME),
    ]

    ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)

    try:
        while True:
            data = stream.read(CHUNK)
            ffmpeg_process.stdin.write(data)
            # Set the event when the first HLS chunk is ready
            if not playlist_ready.is_set():
                playlist_ready.set()
    except KeyboardInterrupt:
        print("Interrupted, stopping recording and exiting...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        ffmpeg_process.kill()  # Forcefully kill the ffmpeg process
        sys.exit(0)


class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)


def start_server():
    # Wait for the HLS playlist to be ready
    playlist_ready.wait()

    httpd = HTTPServer(("0.0.0.0", SERVER_PORT), MyHTTPRequestHandler)
    print(f"Server started at http://localhost:{SERVER_PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    # Empty the hls_segments directory
    for filename in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, filename))

    list_audio_devices()
    device_index = get_input_device_index()

    print(f"Selected microphone input device: {device_index}")

    print(f"Choose a server port {SERVER_PORT} is default, if you don't want to change it then press enter,"
          f"If you want to change it then enter the port number.")
    port = input()
    if port:
        SERVER_PORT = int(port)
    print(f"Selected server port: {SERVER_PORT}")
    print(f"Access the HLS playlist at http://localhost:{SERVER_PORT}/{PLAYLIST_NAME}")
    print("Press Ctrl+C to stop recording and exit. Press enter to continue.")
    input()

    capture_thread = threading.Thread(target=capture_audio, args=(device_index,))
    server_thread = threading.Thread(target=start_server)

    capture_thread.start()
    server_thread.start()

    capture_thread.join()
    server_thread.join()
