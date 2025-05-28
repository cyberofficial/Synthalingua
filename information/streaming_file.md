# Streaming & File Input

These arguments control streaming (HLS, YouTube, Twitch) and file input.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--stream`              | Stream audio from an HLS source (e.g., Twitch, YouTube).         |
| `--stream_language`     | Language of the stream (default: English).                       |
| `--stream_target_language` | [DEPRECATED - WILL BE REMOVED SOON] Language to translate the stream to. Use --stream_transcribe <language> instead. |
| `--stream_translate`    | Enable translation for the stream.                               |
| `--stream_transcribe [language]` | Enable transcription for the stream with optional target language (e.g., --stream_transcribe English). |
| `--stream_original_text`| Show detected original text from the stream.                     |
| `--stream_chunks`       | Number of chunks to split the stream into (default: 5).          |
| `--auto_hls`            | Auto-adjust HLS chunk batching for optimal performance.           |
| `--cookies`             | Name of the cookies file (without `.txt`).                       |
| `--makecaptions`        | Enable captions mode (requires file input/output/name).           |
| `--file_input`          | Path to input file for captioning.                               |
| `--file_output`         | Output folder for captions.                                      |
| `--file_output_name`    | Output file name (without extension).                            |

## Details & Examples

### Streaming Example
```
python transcribe_audio.py --ram 11gb-v3 --stream_translate --stream_language Japanese --stream https://www.twitch.tv/somestreamerhere
```

### Captions Example
```
python transcribe_audio.py --ram 11gb-v3 --makecaptions --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```

### `--auto_hls`
Automatically tunes chunk size for best latency and performance.

---
[Back to Index](./index.md)
