# Output, Captions, and Filtering

These arguments control output formatting, captions, and filtering of unwanted content.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--ignorelist`          | Path to a blacklist file for filtering words/phrases.             |
| `--auto_blocklist`      | Auto-add frequently blocked phrases to the blocklist file.        |
| `--debug`               | Print debug output for blocked/suppressed messages.               |
| `--save_transcript`     | Save the transcript to a file.                                    |
| `--save_folder`         | Folder to save the transcript to (default: `out`).               |
| `--makecaptions`        | Enable captions mode. Use `--makecaptions compare` to generate captions with all RAM models (11gb-v3, 11gb-v2, 7gb, 6gb, 3gb, 2gb, 1gb). |
| `--word_timestamps`     | Enable word-level timestamps in subtitle output (sub_gen only). May make subtitle generation slower as it requires more processing power. If you notice slowdowns, remove this flag next time. Has no effect in microphone or HLS/stream modes. |
| `--file_input`          | Path to input file for captioning.                                |
| `--file_output`         | Output folder for captions.                                       |
| `--file_output_name`    | Output file name (without extension).                             |
| `--isolate_vocals`      | Attempt to isolate vocals from the input audio before generating subtitles (sub_gen only). Requires the spleeter package. |
### `--isolate_vocals`
When enabled, the program will attempt to extract vocals from the input audio file before generating subtitles. This can improve subtitle accuracy for music or noisy audio, but may take additional time and requires the `spleeter` package. If `spleeter` is not installed, a warning will be shown.

**Note:** This flag only affects subtitle generation (sub_gen/captions mode). It has no effect in microphone or HLS/stream modes.

### `--word_timestamps`
When enabled, subtitles will include word-level timestamps for more precise alignment. This may make subtitle generation a bit slower as it requires more processing power. If you notice any unusual slowdowns, try removing the `--word_timestamps` flag next time you run this command.

**Note:** This flag only affects subtitle generation (sub_gen/captions mode). It has no effect in microphone or HLS/stream modes, and will show a warning if used there.

## Details & Examples

### `--ignorelist`
Load a blacklist file (one word/phrase per line) to filter unwanted content from all outputs.

### `--auto_blocklist`
When enabled (with `--ignorelist`), phrases blocked 3+ times in the last 10 are auto-added to your blocklist.

### `--debug`
Prints debug info about blocked or suppressed messages.

### `--save_transcript` & `--save_folder`
Save transcriptions to a file in the specified folder:
```
python transcribe_audio.py --save_transcript --save_folder "C:/transcripts"
```

### Captions Example
```
python transcribe_audio.py --makecaptions --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```

### Captions Compare Mode
Generate captions with all available RAM models for quality comparison:
```
python transcribe_audio.py --makecaptions compare --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```
This will create files like:
- `mycaptions.11gb-v3.srt`
- `mycaptions.11gb-v2.srt`  
- `mycaptions.7gb.srt`
- `mycaptions.6gb.srt`
- `mycaptions.3gb.srt`
- `mycaptions.2gb.srt`
- `mycaptions.1gb.srt`

---
[Back to Index](./index.md)
