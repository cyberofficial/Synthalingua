import pyaudio
import subprocess
import os
import threading
import time
import argparse
import json
import signal
from http.server import SimpleHTTPRequestHandler, HTTPServer
import sys
import urllib.parse
import secrets
from functools import partial
from socketserver import ThreadingMixIn
import numpy as np

# Enhanced audio quality settings for better microphone input
CHUNK = 4096          # Buffer size for audio capture
FORMAT = pyaudio.paInt16    # Fixed: Use 16-bit format to match FFmpeg input
CHANNELS = 1          # Mono audio (standard for speech)
RATE = 48000          # Professional audio standard
OUTPUT_DIR = "hls_segments"
PLAYLIST_NAME = "index.m3u8"
SERVER_PORT = 8888  # Default
CONFIG_FILE = "remote_mic_config.json"

# Audio level monitoring
NOISE_THRESHOLD = 500  # Minimum audio level to detect speech
level_monitor_enabled = True

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Synchronization mechanism
playlist_ready = threading.Event()
shutdown_event = threading.Event()


def load_config():
    """Load configuration from file if it exists."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
    return {}

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save config file: {e}")

def get_audio_level(data):
    """Calculate RMS audio level from audio data."""
    try:
        # Convert bytes to numpy array
        audio_array = np.frombuffer(data, dtype=np.int16)
        
        # Check if array is empty or contains only zeros
        if len(audio_array) == 0:
            return 0
            
        # Calculate mean of squared values
        mean_squared = np.mean(audio_array.astype(np.float64)**2)
        
        # Handle edge cases
        if np.isnan(mean_squared) or np.isinf(mean_squared) or mean_squared < 0:
            return 0
            
        # Calculate RMS level
        rms = np.sqrt(mean_squared)
        
        # Ensure result is valid
        if np.isnan(rms) or np.isinf(rms):
            return 0
            
        return int(rms)
    except Exception:
        return 0

def list_audio_devices():
    """List all available audio input devices with enhanced information."""
    p = pyaudio.PyAudio()
    print("\n" + "="*60)
    print("AVAILABLE AUDIO INPUT DEVICES")
    print("="*60)
    
    input_devices = []
    for i in range(p.get_device_count()):
        try:
            device_info = p.get_device_info_by_index(i)
            max_input_channels = int(device_info.get('maxInputChannels', 0))
            if max_input_channels > 0:  # Only show input devices
                input_devices.append((i, device_info))
                print(f"Device {i:2d}: {device_info['name']}")
                print(f"           Channels: {max_input_channels}")
                print(f"           Sample Rate: {int(float(device_info.get('defaultSampleRate', 0)))} Hz")
                host_api_index = int(device_info.get('hostApi', 0))
                host_api_name = p.get_host_api_info_by_index(host_api_index)['name']
                print(f"           Host API: {host_api_name}")
                print()
        except Exception as e:
            print(f"Device {i}: Error reading device info - {e}")
    
    p.terminate()
    
    if not input_devices:
        print(" No input devices found!")
        return []
    
    return input_devices


def test_audio_device(device_index):
    """Test if the audio device works properly."""
    print(f" Testing device {device_index}...")
    try:
        p = pyaudio.PyAudio()
        
        # Try to open the device
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=device_index,
        )
        
        # Read a small amount of data to test
        try:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_level = get_audio_level(data)
            print(f" Device test successful! Current audio level: {audio_level}")
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            return True
            
        except Exception as e:
            print(f" Device test failed - could not read audio data: {e}")
            stream.stop_stream()
            stream.close()
            p.terminate()
            return False
            
    except Exception as e:
        print(f" Device test failed - could not open device: {e}")
        try:
            p.terminate()
        except:
            pass
        return False

def get_input_device_index(input_devices, config):
    """Get input device index with better UX and config persistence."""
    if not input_devices:
        print(" No input devices available!")
        return None
    
    # Try to use previously saved device
    saved_device = config.get('device_index')
    if saved_device is not None:
        # Verify the saved device still exists
        device_exists = any(device[0] == saved_device for device in input_devices)
        if device_exists:
            while True:
                use_saved = input(f"\nUse previously saved device {saved_device}? (y/n): ").strip().lower()
                if use_saved in ('y', 'yes'):
                    return saved_device
                elif use_saved in ('n', 'no'):
                    break
                else:
                    print("Please enter 'y' or 'n'")
    
    # Get new device selection
    print("\n" + "="*60)
    print("DEVICE SELECTION")
    print("="*60)
    print(" Tips for better audio quality:")
    print("   • Choose devices with 'WASAPI' or 'DirectSound' host API")
    print("   • Avoid 'MME' host API when possible")
    print("   • Built-in microphones often work better than USB devices")
    print("   • Lower device numbers often indicate higher priority devices")
    print()
    
    while True:
        try:
            choice = input("Enter the device number: ").strip()
            if choice.lower() in ('q', 'quit', 'exit'):
                return None
            
            device_index = int(choice)
            # Verify device exists in our input devices list
            if any(device[0] == device_index for device in input_devices):
                # Test the device
                if test_audio_device(device_index):
                    # Save to config
                    config['device_index'] = device_index
                    save_config(config)
                    return device_index
                else:
                    print(" Device test failed. Please try another device.")
            else:
                print(" Invalid device number. Please choose from the list above.")
        except ValueError:
            print(" Please enter a valid device number.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            return None


def capture_audio(device_index, enable_level_monitoring=True):
    """Enhanced audio capture with level monitoring and better error handling."""
    p = pyaudio.PyAudio()

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=device_index,
        )
    except Exception as e:
        print(f" Failed to open audio device {device_index}: {e}")
        p.terminate()
        return

    print(" Recording started...")
    if enable_level_monitoring:
        print(" Audio level monitoring enabled (Ctrl+C to stop)")

    # Simplified FFmpeg command for better reliability
    ffmpeg_command = [
        "ffmpeg",
        "-y",  # Overwrite output files
        "-f", "s16le",  # Input format: signed 16-bit little-endian
        "-ac", str(CHANNELS),  # Audio channels
        "-ar", str(RATE),  # Audio sample rate
        "-i", "pipe:0",  # Input from stdin
        "-f", "hls",  # Output format: HLS
        "-hls_time", "3",  # Segment duration: 3 seconds
        "-hls_list_size", "5",  # Keep last 5 segments (15 seconds of audio)
        "-hls_flags", "append_list",  # Just append to list, no auto-deletion
        "-hls_segment_filename", os.path.join(OUTPUT_DIR, "segment_%03d.ts"),
        "-c:a", "aac",  # Output audio codec
        "-b:a", "96k",  # Lower bitrate for stability
        "-avoid_negative_ts", "make_zero",
        "-loglevel", "warning",  # Reduce log verbosity
        os.path.join(OUTPUT_DIR, PLAYLIST_NAME),
    ]

    print(f" Starting FFmpeg with command: {' '.join(ffmpeg_command)}")

    try:
        ffmpeg_process = subprocess.Popen(
            ffmpeg_command, 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
    except Exception as e:
        print(f" Failed to start FFmpeg: {e}")
        stream.stop_stream()
        stream.close()
        p.terminate()
        return

    # Check if stdin is properly initialized
    if ffmpeg_process.stdin is None:
        print(" Failed to create FFmpeg process with stdin pipe")
        stream.stop_stream()
        stream.close()
        p.terminate()
        return

    last_level_display = time.time()
    silent_duration = 0
    server_startup_delay = 0
    ffmpeg_error_check_time = time.time()
    segments_created = 0
    last_segment_check = time.time()
    
    try:
        while not shutdown_event.is_set():
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                
                # Check if FFmpeg process is still alive
                if ffmpeg_process.poll() is not None:
                    # FFmpeg has exited, get error information
                    try:
                        stdout, stderr = ffmpeg_process.communicate(timeout=1)
                        print(f"\n FFmpeg process died unexpectedly!")
                        print(f"Exit code: {ffmpeg_process.returncode}")
                        if stderr:
                            stderr_text = stderr.decode('utf-8', errors='ignore')
                            print(f"FFmpeg stderr: {stderr_text}")
                        if stdout:
                            stdout_text = stdout.decode('utf-8', errors='ignore')
                            print(f"FFmpeg stdout: {stdout_text}")
                    except subprocess.TimeoutExpired:
                        print(f"\n FFmpeg process died and couldn't get error info")
                    break
                
                try:
                    ffmpeg_process.stdin.write(data)
                    ffmpeg_process.stdin.flush()
                except BrokenPipeError:
                    print(f"\n FFmpeg pipe broken - process may have crashed")
                    break
                except Exception as e:
                    print(f"\n Error writing to FFmpeg: {e}")
                    break
                
                # Set the event when the first HLS chunk is ready
                if not playlist_ready.is_set():
                    playlist_ready.set()
                
                # Give server a brief moment to start up and print messages
                if playlist_ready.is_set() and server_startup_delay < 5:
                    server_startup_delay += 1
                    if server_startup_delay == 5 and enable_level_monitoring:
                        print()  # Add a blank line before starting level monitoring
                
                current_time = time.time()
                
                # Check for new segments every 2 seconds
                if current_time - last_segment_check >= 2:
                    try:
                        segment_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('segment_') and f.endswith('.ts')]
                        if len(segment_files) > segments_created:
                            segments_created = len(segment_files)
                            if enable_level_monitoring and server_startup_delay >= 5:
                                print(f"\n Created segment {segments_created}: {max(segment_files) if segment_files else 'unknown'}")
                    except Exception as e:
                        print(f"\n  Error checking segments: {e}")
                    last_segment_check = current_time
                
                # Clean up old segments manually (keep last 5)
                if segments_created > 5:
                    try:
                        segment_files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.startswith('segment_') and f.endswith('.ts')])
                        while len(segment_files) > 5:
                            old_segment = segment_files.pop(0)
                            old_path = os.path.join(OUTPUT_DIR, old_segment)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                                if enable_level_monitoring and server_startup_delay >= 5:
                                    print(f"\n  Removed old segment: {old_segment}")
                    except Exception as e:
                        print(f"\n  Error cleaning old segments: {e}")
                
                # Audio level monitoring
                if enable_level_monitoring and server_startup_delay >= 5:
                    if current_time - last_level_display >= 0.5:  # Update every 0.5 seconds
                        audio_level = get_audio_level(data)
                        
                        # Create visual level meter
                        bars = min(20, audio_level // 100)
                        meter = "█" * bars + "░" * (20 - bars)
                        
                        if audio_level < NOISE_THRESHOLD:
                            silent_duration += 0.5
                            status = f"🔇 SILENT ({silent_duration:.1f}s)"
                        else:
                            silent_duration = 0
                            status = " ACTIVE"
                        
                        print(f"\r{status} Level: {audio_level:4d} [{meter}] Segments: {segments_created}", end="", flush=True)
                        last_level_display = current_time
                        
            except Exception as e:
                if not shutdown_event.is_set():
                    print(f"\n Audio capture error: {e}")
                break
                
    except KeyboardInterrupt:
        print("\n Recording stopped by user...")
    
    finally:
        # Cleanup
        try:
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            if ffmpeg_process.stdin:
                ffmpeg_process.stdin.close()
            ffmpeg_process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ffmpeg_process.kill()
                
        except Exception as e:
            print(f"  Cleanup warning: {e}")
        
        print(" Audio capture stopped.")


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


def start_server(stream_key, server_ip="127.0.0.1"):
    """Start the HLS streaming server with improved error handling."""
    # Wait for the HLS playlist to be ready
    print("Waiting for HLS playlist to be ready...")
    playlist_ready.wait()

    try:
        # Pass the key to the HTTP handler
        handler_class = partial(MyHTTPRequestHandler, stream_key=stream_key)
        httpd = ThreadingSimpleServer((server_ip, globals()['SERVER_PORT']), handler_class)
        httpd.timeout = 1  # Set timeout for serve_request
        
        print(f"Server started at http://{server_ip}:{globals()['SERVER_PORT']}")
        print("HLS streaming is now active!")
        
        # Serve until shutdown
        while not shutdown_event.is_set():
            try:
                httpd.handle_request()
            except Exception as e:
                if not shutdown_event.is_set():
                    print(f"  Server request error: {e}")
                
    except Exception as e:
        print(f" Server error: {e}")
    finally:
        try:
            httpd.server_close()
        except:
            pass
        print(" Server stopped.")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n Received signal {signum}, shutting down...")
    shutdown_event.set()

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Remote Microphone HLS Streamer: Stream your microphone as an HLS audio source for live transcription.",
        epilog="""
Examples:
  python remote_microphone.py --list-devices
  python remote_microphone.py --device 2 --port 9000
  python remote_microphone.py --no-level-monitor
  python remote_microphone.py --chunk-size 2048 --sample-rate 44100
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--port", type=int, default=SERVER_PORT,
        help=f"Server port for HLS stream (default: {SERVER_PORT})"
    )
    parser.add_argument(
        "--device", type=int,
        help="Audio device index to use (see --list-devices; will prompt if not provided)"
    )
    parser.add_argument(
        "--no-level-monitor", action="store_true",
        help="Disable real-time audio level monitoring in the console"
    )
    parser.add_argument(
        "--list-devices", action="store_true",
        help="List available audio input devices and exit"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=CHUNK,
        help=f"Audio buffer size in samples (default: {CHUNK})"
    )
    parser.add_argument(
        "--sample-rate", type=int, default=RATE,
        help=f"Audio sample rate in Hz (default: {RATE})"
    )
    parser.add_argument(
        "--serverip", default="127.0.0.1", type=str,
        help="IP address for the HLS server to bind to. Use 127.0.0.1 for localhost only (default), 0.0.0.0 to listen on all interfaces, or a specific IP available on your machine."
    )
    return parser.parse_args()

if __name__ == "__main__":
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Update settings from arguments
    if args.chunk_size != CHUNK:
        globals()['CHUNK'] = args.chunk_size
    if args.sample_rate != RATE:
        globals()['RATE'] = args.sample_rate
    if args.port != SERVER_PORT:
        globals()['SERVER_PORT'] = args.port
    
    print("Remote Microphone HLS Streamer")
    print("="*50)
    
    # Load configuration
    config = load_config()
    
    # List available devices
    input_devices = list_audio_devices()
    
    if args.list_devices:
        print("Device list complete. Exiting...")
        sys.exit(0)
    
    if not input_devices:
        print(" No audio input devices available!")
        sys.exit(1)
    
    # Get device index
    if args.device is not None:
        device_index = args.device
        # Verify device exists
        if not any(device[0] == device_index for device in input_devices):
            print(f" Device {device_index} not found!")
            sys.exit(1)
        # Test the device
        if not test_audio_device(device_index):
            print(f" Device {device_index} failed test!")
            sys.exit(1)
    else:
        device_index = get_input_device_index(input_devices, config)
        if device_index is None:
            print("No device selected. Exiting...")
            sys.exit(0)

    print(f"\n Selected microphone device: {device_index}")

    # Get server port
    current_port = globals()['SERVER_PORT']
    if args.port == SERVER_PORT and 'port' in config:
        while True:
            use_saved_port = input(f"Use previously saved port {config['port']}? (y/n): ").strip().lower()
            if use_saved_port in ('y', 'yes'):
                globals()['SERVER_PORT'] = config['port']
                current_port = config['port']
                break
            elif use_saved_port in ('n', 'no'):
                break
            else:
                print("Please enter 'y' or 'n'")
    
    if current_port == args.port and 'port' not in config:
        print(f"\nServer will run on port {current_port}")
        custom_port = input(f"Press Enter to use default port {current_port}, or enter a new port: ").strip()
        if custom_port:
            try:
                new_port = int(custom_port)
                globals()['SERVER_PORT'] = new_port
                current_port = new_port
                config['port'] = new_port
                save_config(config)
            except ValueError:
                print("  Invalid port number, using default.")

    print(f"Server port: {current_port}")

    # Generate stream key
    stream_key = secrets.token_urlsafe(16)
    print(f" Stream Key: {stream_key}")
    
    print(f"\nHLS Stream URL:")
    print(f"   http://localhost:{current_port}/{PLAYLIST_NAME}?key={stream_key}")
    print(f"\n Tips:")
    print(f"   • Use this URL in your transcription software")
    print(f"   • Keep this window open while streaming")
    print(f"   • Press Ctrl+C to stop streaming")
    
    if not args.no_level_monitor:
        print(f"   • Audio level monitoring is enabled")
    
    # Clean up old segments
    try:
        for filename in os.listdir(OUTPUT_DIR):
            file_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("Cleaned up old HLS segments")
    except Exception as e:
        print(f"  Could not clean old segments: {e}")

    print(f"\n Press Enter to start streaming...")
    input()

    # Start capture and server threads
    capture_thread = threading.Thread(
        target=capture_audio, 
        args=(device_index, not args.no_level_monitor),
        daemon=True
    )
    server_thread = threading.Thread(
        target=start_server, 
        args=(stream_key, args.serverip),
        daemon=True
    )

    try:
        capture_thread.start()
        server_thread.start()
        
        # Wait for shutdown signal
        while not shutdown_event.is_set():
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n Interrupted by user...")
    finally:
        shutdown_event.set()
        print("Goodbye!")