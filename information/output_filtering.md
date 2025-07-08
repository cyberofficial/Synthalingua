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
| `--isolate_vocals`      | Attempt to isolate vocals from the input audio before generating subtitles (sub_gen only). Requires the demucs package. |
| `--silent_detect`       | Skip processing silent audio chunks during caption generation (sub_gen only). Improves processing speed for files with long silent periods. **Note:** Only works with `--makecaptions` - not supported for HLS/streaming or microphone modes. |
| `--silent_threshold`    | dB threshold for silence detection (default: -35.0). Lower values (e.g., -45.0) detect quieter speech like whispers. Higher values (e.g., -25.0) only detect louder speech. Only used with `--silent_detect`. |
### `--isolate_vocals`
When enabled, the program will attempt to extract vocals from the input audio file before generating subtitles. This can improve subtitle accuracy for music or noisy audio, but may take additional time and requires the `demucs` package. If `demucs` is not installed, a warning will be shown.

**Note:** This flag only affects subtitle generation (sub_gen/captions mode). It has no effect in microphone or HLS/stream modes.

### `--silent_detect`
When enabled, the program will intelligently skip silent regions in audio files during caption generation. This uses advanced audio analysis to detect speech vs. silence boundaries, resulting in faster processing and better transcription quality by avoiding unnecessary processing of silent segments.

**Benefits:**
- Faster processing for files with long silent periods
- Reduced resource usage
- Better transcription quality (no processing of noise/silence)
- Natural speech boundaries (no mid-word cuts)

**Best used with:** `--isolate_vocals` for maximum efficiency and quality

**Note:** This flag only works with `--makecaptions` (caption generation mode). It is **not supported** for HLS/streaming or microphone input modes.

### `--silent_threshold`
Controls the dB threshold used for silence detection. This allows fine-tuning the sensitivity of `--silent_detect` for different types of audio content.

**Default:** -35.0dB (suitable for normal speech levels)

**Common adjustments:**
- **Quiet speech/whispers:** Use -45.0dB or lower for more sensitive detection
- **Noisy environments:** Use -30.0dB or higher to avoid false speech detection
- **Loud speech only:** Use -25.0dB or higher for less sensitive detection

**Examples:**
```
# Default threshold
--silent_detect

# More sensitive (detects quieter speech)
--silent_detect --silent_threshold -45.0

# Less sensitive (only loud speech)
--silent_detect --silent_threshold -25.0
```

**Note:** This argument only has effect when used with `--silent_detect`.

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

### Advanced Captions with Vocal Isolation and Silence Detection (RECOMMENDED)
For maximum efficiency and quality, combine vocal isolation with silence detection:
```
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```

For quiet speech or whispered content:
```
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --silent_threshold -45.0 --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```

This combination:
- Extracts clean vocals (removes background music/noise)
- Skips silent regions in the cleaned audio
- Adjustable threshold for different speech volumes
- Results in faster processing and higher accuracy

### Captions Compare Mode
Generate captions with all available RAM models for quality comparison:
```
python transcribe_audio.py --makecaptions compare --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
```

With advanced features:
```
python transcribe_audio.py --makecaptions compare --isolate_vocals --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="mycaptions"
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
