import os
import subprocess
import tempfile
from colorama import Fore, Style
import shutil
import hashlib
import requests
import m3u8
import time
import wave
import contextlib

def test_stream_source(hls_url, temp_dir, cookie_file_path=None, params=None, preview_seconds=10):
    """
    Downloads enough segments from the given HLS URL to cover at least `preview_seconds` of audio, combines them, and converts to WAV.
    Returns the path to the resulting WAV file.
    """
    # Prepare temp paths
    task_id = 'testsrc'
    segment_paths = []
    cookies = None
    if cookie_file_path:
        import http.cookiejar
        cookie_jar = http.cookiejar.MozillaCookieJar()
        cookie_jar.load(cookie_file_path, ignore_discard=True, ignore_expires=True)
        cookies = cookie_jar
    # Download playlist
    m3u8_obj = m3u8.load(hls_url)
    segments = m3u8_obj.segments
    if not segments:
        print(f"{Fore.RED}No segments found in playlist!{Style.RESET_ALL}")
        return None
    # Calculate how many segments to get at least preview_seconds
    total_duration = 0.0
    num_segments = 0
    for seg in segments:
        total_duration += getattr(seg, 'duration', 0)
        num_segments += 1
        if total_duration >= preview_seconds:
            break
    if num_segments == 0:
        print(f"{Fore.RED}No valid segments with duration found!{Style.RESET_ALL}")
        return None
    segments = segments[:num_segments]
    for idx, segment in enumerate(segments):
        url = segment.absolute_uri
        url_hash = hashlib.md5(url.encode()).hexdigest()
        seg_path = os.path.join(temp_dir, f"{task_id}_{idx:05d}_{url_hash}.ts")
        try:
            resp = requests.get(url, stream=True, cookies=cookies, params=params)
            if resp.status_code == 200:
                with open(seg_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=16000):
                        f.write(chunk)
                segment_paths.append(seg_path)
            else:
                print(f"{Fore.YELLOW}Failed to download segment {idx}: {resp.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error downloading segment {idx}: {e}{Style.RESET_ALL}")
    if not segment_paths:
        print(f"{Fore.RED}No segments could be downloaded!{Style.RESET_ALL}")
        return None
    # Combine segments
    combined_path = os.path.join(temp_dir, f"{task_id}_combined.ts")
    with open(combined_path, "wb") as outfile:
        for seg in segment_paths:
            with open(seg, "rb") as infile:
                outfile.write(infile.read())
    # Convert to wav using ffmpeg
    wav_path = os.path.join(temp_dir, f"{task_id}_preview.wav")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", combined_path, "-acodec", "pcm_s16le", "-ar", "16000", wav_path
    ]
    try:
        subprocess.check_call(ffmpeg_cmd)
        print(f"{Fore.GREEN}WAV preview created: {wav_path}{Style.RESET_ALL}")
        return wav_path
    except Exception as e:
        print(f"{Fore.RED}Error converting to WAV: {e}{Style.RESET_ALL}")
        return None
    finally:
        # Clean up segment files
        for seg in segment_paths:
            if os.path.exists(seg):
                os.remove(seg)
        if os.path.exists(combined_path):
            os.remove(combined_path)
