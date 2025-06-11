# Synthalingua Usage Examples

This page provides practical command-line examples for common Synthalingua workflows. Copy, modify, and experiment with these to fit your needs!

---

## 1. Streaming from Twitch/YouTube with Translation
**Translate a Japanese Twitch stream to English, using GPU and Discord integration:**
```sh
python transcribe_audio.py --ram 11gb-v3 --stream https://www.twitch.tv/somestreamerhere --stream_language Japanese --stream_translate --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890" --device cuda
```

**Stream with blocklist and repetition suppression:**
```sh
python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --stream_language Japanese --stream_translate --ignorelist "C:/path/blacklist.txt" --auto_blocklist --condition_on_previous_text
```

**Stream with web server output:**
```sh
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_language Japanese --stream_translate --portnumber 8080
```

---

## 2. Microphone Input (Live Speech)
**Transcribe and translate live microphone input to English:**
```sh
python transcribe_audio.py --ram 6gb --microphone_enabled --language ja --translate --device cuda
```

**Set a specific microphone by index or name:**
```sh
python transcribe_audio.py --microphone_enabled --set_microphone 2
python transcribe_audio.py --microphone_enabled --set_microphone "Microphone (Realtek USB2.0 Audi)"
```

**Use blocklist and auto-blocklist with microphone:**
```sh
python transcribe_audio.py --microphone_enabled --ignorelist "C:/path/blacklist.txt" --auto_blocklist --condition_on_previous_text
```

---

## 3. Making Captions/Subtitles from a File
**Generate English captions for a Japanese video file:**
```sh
python transcribe_audio.py --ram 11gb-v3 --makecaptions --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "myvideo_captions" --language Japanese --device cuda
```

**Generate captions with all models for quality comparison:**
```sh
python transcribe_audio.py --makecaptions compare --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "myvideo_captions" --language Japanese --device cuda
```

**With blocklist filtering:**
```sh
python transcribe_audio.py --makecaptions --file_input "C:/Videos/myvideo.mp4" --file_output "C:/Videos/captions" --file_output_name "myvideo_captions" --ignorelist "C:/path/blacklist.txt"
```

---

## 4. Advanced/Other Examples
**Stream with custom chunk size and cookies (cookies folder):**
```sh
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_chunks 3 --cookies twitch
```

**Stream with padded audio for better context:**
```sh
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --stream_chunks 4 --paddedaudio 1
```

**Microphone with padded audio for better context:**
```sh
python transcribe_audio.py --microphone_enabled --mic_chunk_size 3 --paddedaudio 1
```

**Stream with cookies using full path:**
```sh
python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --cookies "C:\path\to\my\twitch_cookies.txt"
```

**Stream with cookies from current directory:**
```sh
python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --cookies youtube.txt
```

**Transcribe to a non-English target language:**
```sh
python transcribe_audio.py --microphone_enabled --language en --transcribe --target_language es
```

**List microphones and set by index:**
```sh
python transcribe_audio.py --list_microphones
python transcribe_audio.py --microphone_enabled --set_microphone 3
```

---
[Back to Index](./index.md)

---

For more details on each argument, see the other docs in this folder or the [README](../README.md).
