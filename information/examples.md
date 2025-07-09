
# Synthalingua Command-Line Examples

A practical, easy-to-read guide for common Synthalingua workflows. Copy, adapt, and experiment!

---

## 1. Streaming (Twitch/YouTube/Other)


**Basic: Translate a Japanese Twitch stream to English (GPU):**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_language Japanese --stream_translate --device cuda
```


**With Discord notifications:**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_language Japanese --stream_translate --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890"
```


**With blocklist and auto-blocklist:**
```python
python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --stream_language Japanese --stream_translate --ignorelist "C:/path/blacklist.txt" --auto_blocklist
```


**With web server output (view in browser):**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_language Japanese --stream_translate --portnumber 8080
```


**With cookies (for private/region-locked streams):**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --cookies twitch
```


**Custom chunk size and padded audio (for better context):**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_chunks 4 --paddedaudio 1
```


**Select audio stream quality (YouTube):**
```python
python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --selectsource bestaudio
```

---

## 2. Microphone Input (Live Speech)


**Transcribe and translate live microphone input to English:**
```python
python transcribe_audio.py --microphone_enabled --language ja --translate --device cuda
```


**Set a specific microphone by index or name:**
```python
python transcribe_audio.py --microphone_enabled --set_microphone 2
python transcribe_audio.py --microphone_enabled --set_microphone "Microphone (Realtek USB2.0 Audi)"
```


**With blocklist and auto-blocklist:**
```python
python transcribe_audio.py --microphone_enabled --ignorelist "C:/path/blacklist.txt" --auto_blocklist
```


**With padded audio for better context:**
```python
python transcribe_audio.py --microphone_enabled --mic_chunk_size 3 --paddedaudio 1
```


**Transcribe to a non-English target language:**
```python
python transcribe_audio.py --microphone_enabled --language en --transcribe --target_language es
```


**List microphones and set by index:**
```python
python transcribe_audio.py --list_microphones
python transcribe_audio.py --microphone_enabled --set_microphone 3
```

---

## 3. File Captioning (Subtitles)


**Basic: Generate English captions for a Japanese video file:**
```python
python transcribe_audio.py --makecaptions --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile" --language Japanese --device cuda
```


**Compare all models for quality:**
```python
python transcribe_audio.py --makecaptions compare --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile" --language Japanese
```


**With vocal isolation (removes music/noise, requires demucs):**
```python
python transcribe_audio.py --makecaptions --isolate_vocals --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**With silence detection (faster for files with silent periods):**
```python
python transcribe_audio.py --makecaptions --silent_detect --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**With custom silence threshold (for quiet speech):**
```python
python transcribe_audio.py --makecaptions --silent_detect --silent_threshold -45.0 --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**With custom silence duration (ignore pauses under 2s):**
```python
python transcribe_audio.py --makecaptions --silent_detect --silent_duration 2.0 --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**RECOMMENDED: Vocal isolation + silence detection:**
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**RECOMMENDED: With custom settings for natural speech with pauses:**
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --silent_threshold -40.0 --silent_duration 1.5 --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile"
```


**With blocklist filtering:**
```python
python transcribe_audio.py --makecaptions --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "MyCaptionsFile" --ignorelist "C:/path/blacklist.txt"
```

---

## 4. Saving Transcripts (Text Output)


**Save transcript to a folder (always use both flags):**
```python
python transcribe_audio.py --save_transcript --save_folder "C:/transcripts"
```

---

## 5. Advanced & Troubleshooting


**Stream with cookies using full path:**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --cookies "C:/path/to/my/twitch_cookies.txt"
```


**Stream with cookies from current directory:**
```python
python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --cookies youtube.txt
```


**Show detected language of the stream:**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_original_text
```


**Legacy: Translate stream using deprecated argument (still supported):**
```python
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_target_language English
```

---

For more details on each argument, see the other docs in this folder or the [README](../README.md).
