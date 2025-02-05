import threading
import queue
import time
import requests
import hashlib
import os
import m3u8
import http.client
import http.cookiejar
import whisper
from modules import parser_args
from modules.discord import send_to_discord_webhook
from modules import api_backend

# Global shutdown flag
shutdown_flag = False
args = parser_args.parse_arguments()
kill = False

# Set debug to true
# args.debug = True

# Semaphore for limiting concurrent downloads (adjust as needed)
max_concurrent_downloads = 4
download_semaphore = threading.Semaphore(max_concurrent_downloads)


def load_cookies_from_file(cookie_file_path):
    cookie_jar = http.cookiejar.MozillaCookieJar()
    cookie_jar.load(cookie_file_path, ignore_discard=True, ignore_expires=True)
    return cookie_jar


def start_stream_transcription(
    task_id,
    hls_url,
    model_name,
    temp_dir,
    segments_max,
    target_language,
    stream_language,
    tasktranslate_task,
    tasktranscribe_task,
    webhook_url,
    cookie_file_path=None,
    streamkey=None,
):

    if streamkey:
        keyid = args.remote_hls_password_id
        key = args.remote_hls_password
        params = {keyid: key}
    else:
        params = None

    global shutdown_flag
    audio_queue = queue.Queue()

    # Load cookies if a cookie file path is provided
    cookies = None
    if cookie_file_path:
        cookies = load_cookies_from_file(cookie_file_path)

    def download_segment(
        segment_url, output_path, max_retries=3, retry_delay=0.5, segment_delay=0
    ):
        """Downloads a segment with retry logic and improved error handling."""
        global kill
        with download_semaphore:
            for retry_count in range(max_retries + 1):
                try:
                    # show downloading segments if args debug is set
                    if args.debug:
                        print(f"\n\n\nDownloading segment: {segment_url}\n\n")
                    response = (
                        requests.get(
                            segment_url, stream=True, cookies=cookies, params=params
                        )
                        if cookies
                        else requests.get(segment_url, stream=True, params=params)
                    )

                    # Check for successful response
                    if response.status_code == 200:
                        with open(output_path, "wb") as file:
                            for chunk in response.iter_content(chunk_size=16000):
                                file.write(chunk)
                        # time.sleep(segment_delay)  # Optional delay
                        return True
                    elif response.status_code == 401:
                        print(
                            "Invalid credentials. Please check your cookies/streamkey and try again."
                        )
                        input("Press CTRL+C to exit...")
                        kill = True
                        raise Exception("Exiting due to invalid credentials")
                    else:
                        print(
                            f"Failed to download segment, status code: {response.status_code}. Retrying {retry_count}/{max_retries}"
                        )
                except requests.exceptions.RequestException as e:
                    print(
                        f"Network error: {e}. Retrying {retry_count}/{max_retries} in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                except Exception as e:
                    print(f"Unexpected error downloading segment: {e}")
                    break

        print(
            f"Failed to download segment {segment_url} after {max_retries} retries. Skipping."
        )
        # Clean up partial file if exists
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

    def load_m3u8_with_retry(hls_url, retry_delay=5):
        while not shutdown_flag:
            try:
                # Split and take first URL if multiple URLs are provided
                cleaned_url = hls_url.strip().split('\n')[0]
                if args.debug:
                    print(f"\n[DEBUG] Loading m3u8 from URL: {cleaned_url}")
                
                m3u8_obj = m3u8.load(cleaned_url)
                return m3u8_obj
            except (
                http.client.RemoteDisconnected,
                http.client.IncompleteRead,
                requests.exceptions.RequestException,
            ) as e:
                print(
                    f"Error loading m3u8 file: {e}. Retrying in {retry_delay} seconds..."
                )
                time.sleep(retry_delay)
            except Exception as e:
                print(f"Unexpected error loading m3u8 file: {e}")
                time.sleep(retry_delay)
        return None

    def generate_segment_filename(url, counter, task_id):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(temp_dir, f"{task_id}_{counter:05d}_{url_hash}.ts")

    def combine_audio_segments(segment_paths, output_path):
        with open(output_path, "wb") as outfile:
            for segment_path in segment_paths:
                if not os.path.exists(segment_path):
                    print(f"Warning: File {segment_path} does not exist, skipping.")
                    continue
                try:
                    with open(segment_path, "rb") as infile:
                        outfile.write(infile.read())
                    os.remove(segment_path)
                except Exception as e:
                    print(f"Error combining audio segments: {e}")

    def translate_audio(file_path, model):
        try:
            result = model.transcribe(file_path, task="translate", fp16=args.fp16, language=stream_language, condition_on_previous_text=args.condition_on_previous_text)
            return result["text"]
        except RuntimeError as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def transcribe_audio(file_path, model, language):
        try:
            result = model.transcribe(file_path, language=language, fp16=args.fp16, condition_on_previous_text=args.condition_on_previous_text)
            return result["text"]
        except RuntimeError as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def detect_language(file_path, model, device=args.device):
        try:
            audio = whisper.load_audio(file_path)
            audio = whisper.pad_or_trim(audio)
            
            # Handle "12gb-v3"
            if args.ram == "12gb-v3":
                mel = whisper.log_mel_spectrogram(audio, n_mels=128).to(device)
            else:
                mel = whisper.log_mel_spectrogram(audio, n_mels=80).to(device)

            _, language_probs = model.detect_language(mel)
            detected_language = max(language_probs, key=language_probs.get)
            return detected_language
        except RuntimeError as e:
            print(f"Error detecting language: {e}")
            detected_language = "n/a"
            return detected_language


    def process_audio(file_path, model):
        if not os.path.exists(file_path):
            print(f"Warning: File {file_path} does not exist, skipping.")
            return

        transcription = None
        translation = None
        if args.stream_original_text:
            if args.stream_language:
                detected_language = stream_language
                # print(f"Language Set By Args: {detected_language}")
            else:
                # print("Testing for Language")
                detected_language = detect_language(file_path, model)
                # print(f"Language is: {detected_language}")
            transcription = transcribe_audio(
                file_path, model, language=detected_language
            )
            print(f"{'-' * 50} {detected_language} Original {'-' * 50}")
            print(transcription)
            if args.portnumber and transcription.strip():
                new_header = f"{transcription}"
                api_backend.update_header(new_header)

        if tasktranslate_task:
            translation = translate_audio(file_path, model)
            if translation:
                print(f"{'-' * 50} Stream EN Translation {'-' * 50}")
                print(translation)
                if webhook_url:
                    send_to_discord_webhook(
                        webhook_url, f"Stream EN Translation:\n{translation}\n"
                    )
                if args.portnumber:
                    new_header = f"{translation}"
                    api_backend.update_translated_header(new_header)

        if tasktranscribe_task:
            transcription = transcribe_audio(
                file_path, model, language=target_language
            )
            if transcription:
                print(
                    f"{'-' * 50} Stream {target_language} Transcription {'-' * 50}"
                )
                print(transcription)
                if webhook_url:
                    send_to_discord_webhook(
                        webhook_url,
                        f"Stream {target_language} Transcription:\n{transcription}\n",
                    )
                if args.portnumber and transcription.strip():
                    new_header = f"{transcription}"
                    api_backend.update_transcribed_header(new_header)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing file {file_path}: {e}")

    # Thread function for processing audio
    def process_audio_thread():
        while not shutdown_flag:
            file_path = audio_queue.get()
            if file_path is None:
                break
            process_audio(file_path, model_name)

    # Start processing thread
    processing_thread = threading.Thread(target=process_audio_thread)
    processing_thread.daemon = True
    processing_thread.start()

    # Main loop for downloading and combining segments
    try:
        downloaded_segments = set()
        counter = 0
        accumulated_segments = []

        while not shutdown_flag:
            m3u8_obj = load_m3u8_with_retry(hls_url)
            if not m3u8_obj:
                print("Failed to load m3u8 after retries, stopping.")
                break

            # Get total segments and calculate starting point
            total_segments = len(m3u8_obj.segments)
            if total_segments == 0:
                if args.debug:
                    print("\n[DEBUG] Playlist is empty, waiting for segments...")
                time.sleep(1)  # Wait if playlist is empty
                continue

            # Start from the most recent segments on first run
            if len(downloaded_segments) == 0:
                start_idx = max(0, total_segments - segments_max)
                if args.debug:
                    print(f"\n[DEBUG] First run:")
                    print(f"[DEBUG] Total segments in playlist: {total_segments}")
                    print(f"[DEBUG] Starting from segment index: {start_idx}")
                    print(f"[DEBUG] Will process {total_segments - start_idx} segments")
            else:
                start_idx = 0
                if args.debug:
                    print(f"\n[DEBUG] Continuing run:")
                    print(f"[DEBUG] Total segments in playlist: {total_segments}")
                    print(f"[DEBUG] Previously downloaded segments: {len(downloaded_segments)}")
                    print(f"[DEBUG] Starting from beginning to check for new segments")

            # Process segments from the calculated starting point
            for idx in range(start_idx, total_segments):
                segment = m3u8_obj.segments[idx]
                if segment.uri in downloaded_segments:
                    continue  # Skip already downloaded segments

                segment_path = generate_segment_filename(
                    segment.uri, counter, task_id
                )
                counter += 1
                try:
                    if args.debug:
                        print(f"\n[DEBUG] Attempting to download segment {counter}:")
                        print(f"[DEBUG] Segment URI: {segment.uri}")

                    if download_segment(segment.absolute_uri, segment_path):
                        if kill:
                            break
                        downloaded_segments.add(segment.uri)
                        accumulated_segments.append(segment_path)

                        if args.debug:
                            print(f"[DEBUG] Successfully downloaded segment {counter}")
                            print(f"[DEBUG] Accumulated segments: {len(accumulated_segments)}/{segments_max}")

                        if len(accumulated_segments) >= segments_max:
                            if args.debug:
                                print(f"[DEBUG] Reached max segments ({segments_max}), processing batch...")
                            combined_path = os.path.join(
                                temp_dir, f"{task_id}_combined_{counter}.ts"
                            )
                            combine_audio_segments(
                                accumulated_segments, combined_path
                            )
                            audio_queue.put(combined_path)
                            accumulated_segments = []
                except Exception as e:  # Catch the raised exception
                    print(f"Error during download: {e}")
                    break  # Exit the loop

    except KeyboardInterrupt:
        shutdown_flag = True  # Signal to shut down

    except Exception as e:
        exit(0)

    # Cleanup
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    audio_queue.put(None)  # Signal processing thread to stop
    processing_thread.join()


def stop_transcription():
    global shutdown_flag
    shutdown_flag = True


print("Stream Transcription Module Loaded")