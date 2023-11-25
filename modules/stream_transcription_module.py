# stream_transcription_module.py

import os
import hashlib
import queue
import shutil
import threading
import whisper
import m3u8
import requests

# Global shutdown flag
shutdown_flag = False

def start_stream_transcription(hls_url, model_name, temp_dir, segments_max):
    global shutdown_flag
    audio_queue = queue.Queue()

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
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(temp_dir, f"{counter:05d}_{url_hash}.ts")

    def combine_audio_segments(segment_paths, output_path):
        with open(output_path, 'wb') as outfile:
            for segment_path in segment_paths:
                with open(segment_path, 'rb') as infile:
                    outfile.write(infile.read())
                os.remove(segment_path)

    def translate_audio(file_path, model):
        try:
            result = model.transcribe(file_path, task="translate")
            return result["text"]
        except RuntimeError as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def transcribe_audio(file_path, model):
        try:
            result = model.transcribe(file_path)
            return result["text"]
        except RuntimeError as e:
            print(f"Error transcribing audio: {e}")
            return ""

    def process_audio_queue(model):
        while True:
            file_path = audio_queue.get()
            if file_path is None:
                break
            translation = translate_audio(file_path, model)
            if translation:
                print(
                    f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)} EN Translation {'-' * int((shutil.get_terminal_size().columns - 15) / 2)}")
                print(translation)

            os.remove(file_path)

    # Start processing thread
    processing_thread = threading.Thread(target=process_audio_queue, args=(model_name,))
    processing_thread.daemon = True
    processing_thread.start()

    # Main loop for downloading and combining segments
    try:
        downloaded_segments = set()
        counter = 0
        accumulated_segments = []

        while not shutdown_flag:
            m3u8_obj = m3u8.load(hls_url)
            for segment in m3u8_obj.segments:
                if segment.uri not in downloaded_segments:
                    segment_path = generate_segment_filename(segment.uri, counter)
                    counter += 1
                    if download_segment(segment.absolute_uri, segment_path):
                        downloaded_segments.add(segment.uri)
                        accumulated_segments.append(segment_path)

                        if len(accumulated_segments) >= segments_max:
                            combined_path = os.path.join(temp_dir, f"combined_{counter}.ts")
                            combine_audio_segments(accumulated_segments, combined_path)
                            audio_queue.put(combined_path)
                            accumulated_segments = []

    except KeyboardInterrupt:
        shutdown_flag = True  # Signal to shut down

    # Cleanup
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    audio_queue.put(None)
    processing_thread.join()

def stop_transcription():
    global shutdown_flag
    shutdown_flag = True
