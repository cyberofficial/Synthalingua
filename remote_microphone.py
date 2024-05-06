import pyaudio
import subprocess
import os
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import sys
import urllib.parse
import secrets
from functools import partial
from socketserver import ThreadingMixIn

CHUNK = 2048
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
            print(
                "\n\n\n\nEnter the index of the microphone input device.\n"
                "Remember this script may not work for all devices.\n"
                "The lower the index, the better the quality of the audio.\n"
            )
            index = int(input("Enter the index of the microphone input device: "))
            return index
        except ValueError:
            print("Invalid input. Please enter a valid index.")


def capture_audio(device_index):
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
        input_device_index=device_index,
    )

    print("* recording")

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f",
        "s16le",
        "-acodec",
        "pcm_s16le",
        "-ac",
        str(CHANNELS),
        "-ar",
        str(RATE),
        "-i",
        "pipe:0",
        "-f",
        "hls",
        "-hls_time",
        "1",
        "-hls_list_size",
        "30",
        "-hls_flags",  # Add this line
        "delete_segments+append_list",  # Add this line
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
    def __init__(self, *args, stream_key, **kwargs):
        self.stream_key = stream_key
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)

    def do_GET(self):
        # Get the provided key from the URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        provided_key = params.get("key", [""])[0]  # Get the first 'key' value or ''

        if provided_key != self.stream_key:
            self.send_error(401, "Unauthorized")
            return

        super().do_GET()


# Define a custom HTTP server class to limit concurrent connections
class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    pass


def start_server(stream_key):
    # Wait for the HLS playlist to be ready
    playlist_ready.wait()

    try:
        # Pass the key to the HTTP handler
        handler_class = partial(MyHTTPRequestHandler, stream_key=stream_key)
        httpd = ThreadingSimpleServer(("0.0.0.0", SERVER_PORT), handler_class)
        print(f"Server started at http://0.0.0.0:{SERVER_PORT}")
        # start the server with debug mode disabled
        httpd.serve_forever(poll_interval=5)
    except Exception as e:
        print(f"Error starting server: {e}")


if __name__ == "__main__":
    # Empty the hls_segments directory
    for filename in os.listdir(OUTPUT_DIR):
        os.remove(os.path.join(OUTPUT_DIR, filename))

    list_audio_devices()
    device_index = get_input_device_index()

    print(f"Selected microphone input device: {device_index}")

    print(
        f"Choose a server port {SERVER_PORT} is default, if you don't want to change it then press enter,"
        f"If you want to change it then enter the port number."
    )
    port = input()
    if port:
        SERVER_PORT = int(port)
    print(f"Selected server port: {SERVER_PORT}")

    # Generate stream key
    stream_key = secrets.token_urlsafe(16)
    print(f"Stream Key: {stream_key}")

    print(
        f"Access the HLS playlist at http://localhost:{SERVER_PORT}/{PLAYLIST_NAME}?key={stream_key}"
    )
    print("Press Ctrl+C to stop recording and exit. Press enter to continue.")
    input()

    capture_thread = threading.Thread(target=capture_audio, args=(device_index,))
    server_thread = threading.Thread(target=start_server, args=(stream_key,))

    capture_thread.start()
    server_thread.start()

    capture_thread.join()
    server_thread.join()