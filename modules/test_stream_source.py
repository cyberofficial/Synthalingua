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

def test_stream_source(hls_url, temp_dir=None, cookie_file_path=None, params=None, num_segments=10):
    """
    Downloads the first `num_segments` from the given HLS URL, combines them, and converts to WAV.
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
    if temp_dir is None:
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    # Download playlist
    m3u8_obj = m3u8.load(hls_url)
    segments = m3u8_obj.segments[:num_segments]
    if not segments:
        print(f"{Fore.RED}No segments found in playlist!{Style.RESET_ALL}")
        return None
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
