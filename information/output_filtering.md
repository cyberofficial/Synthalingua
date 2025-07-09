# Output, Captions, and Filtering

These arguments control output formatting, captions, and filtering of unwanted content.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--ignorelist`          | Path to a blacklist file for filtering words/phrases.             |
| `--auto_blocklist`      | Auto-add frequently blocked phrases to the blocklist file.        |
| `--debug`               | Print debug output for blocked/suppressed messages.               |
| `--save_transcript`     | Save the transcript to a file.                                    |
| `--save_folder`         | Folder to save the transcript to (default: `out`). Used with `--save_transcript`. |
| `--makecaptions`        | Enable captions mode. Use `--makecaptions compare` to generate captions with all RAM models (11gb-v3, 11gb-v2, 7gb, 6gb, 3gb, 2gb, 1gb). Only `compare` is a valid argument. |
| `--word_timestamps`     | Enable word-level timestamps in subtitle output (sub_gen only). May make subtitle generation slower as it requires more processing power. If you notice slowdowns, remove this flag next time. Has no effect in microphone or HLS/stream modes. |
| `--file_input`          | Path to input file for captioning. |
| `--file_output`         | Folder to save generated captions (SRT) to. Used with `--makecaptions`. |
| `--file_output_name`    | Output file name for captions (without extension, e.g. `MyCaptionsFile`). The program will add `.srt` automatically. |
| `--isolate_vocals`      | Attempt to isolate vocals from the input audio before generating subtitles (sub_gen only). Requires the demucs package. |
| `--demucs_model`        | Demucs model to use for vocal isolation (default: htdemucs). Choices: htdemucs, htdemucs_ft, htdemucs_6s, hdemucs_mmi, mdx, mdx_extra, mdx_q, mdx_extra_q, hdemucs, demucs. Only used when `--isolate_vocals` is enabled. |
| `--silent_detect`       | Skip processing silent audio chunks during caption generation (sub_gen only). Improves processing speed for files with long silent periods. **Note:** Only works with `--makecaptions` - not supported for HLS/streaming or microphone modes. |
| `--silent_threshold`    | dB threshold for silence detection (default: -35.0). Lower values (e.g., -45.0) detect quieter speech like whispers. Higher values (e.g., -25.0) only detect louder speech. Only used with `--silent_detect`. |
| `--silent_duration`     | Minimum duration in seconds for a region to be considered silence (default: 0.5). Higher values (e.g., 2.0) treat brief pauses as speech. Lower values (e.g., 0.1) detect shorter silent periods. Only used with `--silent_detect`. |
### `--isolate_vocals`
When enabled, the program will attempt to extract vocals from the input audio file before generating subtitles. This can improve subtitle accuracy for music or noisy audio, but may take additional time and requires the `demucs` package. If `demucs` is not installed, a warning will be shown.

**Model Selection:**
- By default, the program will prompt you to select which Demucs model to use
- Use `--demucs_model` to specify the model directly and skip the interactive prompt
- Available models: htdemucs (default), htdemucs_ft, htdemucs_6s, hdemucs_mmi, mdx, mdx_extra, mdx_q, mdx_extra_q, hdemucs, demucs

**Note:** This flag only affects subtitle generation (sub_gen/captions mode). It has no effect in microphone or HLS/stream modes.

### `--demucs_model`
Specifies which Demucs model to use for vocal isolation. Only used when `--isolate_vocals` is enabled. If not specified, the program will prompt you to select a model interactively.

**Available models:**
- `htdemucs` (default): Latest Hybrid Transformer model
- `htdemucs_ft`: Fine-tuned version for better quality (slower)
- `htdemucs_6s`: 6-source separation (includes piano/guitar)
- `hdemucs_mmi`: Hybrid v3 trained on expanded dataset
- `mdx`: Frequency-domain model, MDX winner
- `mdx_extra`: Enhanced MDX with extra training data
- `mdx_q`: Quantized MDX (faster, smaller)
- `mdx_extra_q`: Quantized MDX Extra (faster, smaller)
- `hdemucs`: Original Hybrid Demucs v3
- `demucs`: Original time-domain Demucs
> **Warning:** The longer your video or audio file, the more RAM will be required for processing—especially when using advanced models. For example, the `htdemucs_ft` model may require up to **24GB of RAM** (not to be confused with VRAM) to process a 1-hour video. If you encounter memory errors or segmentation faults, try using a shorter file, a less demanding model, processing your media in smaller segments, or increasing your system's page file (virtual memory) size to help prevent crashes.

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
```python
# Default threshold
--silent_detect

# More sensitive (detects quieter speech)
--silent_detect --silent_threshold -45.0

# Less sensitive (only loud speech)
--silent_detect --silent_threshold -25.0
```

### `--silent_duration`
Controls the minimum duration for a region to be considered silence versus a brief pause in speech. This helps distinguish between natural speaking pauses and actual silent periods.

**Default:** 0.5 seconds (brief pauses are treated as part of speech)

**Common adjustments:**
- **Ignore brief pauses:** Use 2.0s or higher to only consider longer gaps as silence
- **Conversational speech:** Use 1.0-1.5s for natural conversation with pauses
- **Rapid speech:** Use 0.1-0.3s to detect even brief silent moments
- **Podcast intros/outros:** Use 3.0s+ to skip only major silent sections

**Examples:**
```python
# Default duration (0.5s minimum)
--silent_detect

# Only consider 2+ second gaps as silence (ignore brief pauses)
--silent_detect --silent_duration 2.0

# Very sensitive to short gaps
--silent_detect --silent_duration 0.1

# Combined with custom threshold
--silent_detect --silent_threshold -40.0 --silent_duration 1.5
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
Save transcriptions to a file in the specified folder (always use both flags together):
```python
python transcribe_audio.py --save_transcript --save_folder "C:/transcripts"
```

### Captions Example
```python
python transcribe_audio.py --makecaptions --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

### Advanced Captions with Vocal Isolation and Silence Detection (RECOMMENDED)
For maximum efficiency and quality, combine vocal isolation with silence detection:
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

With specific Demucs model (skip interactive prompt):
```python
python transcribe_audio.py --makecaptions --isolate_vocals --demucs_model htdemucs_ft --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

For fastest processing (quantized model):
```python
python transcribe_audio.py --makecaptions --isolate_vocals --demucs_model mdx_q --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

For quiet speech or whispered content:
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --silent_threshold -45.0 --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

For content with brief speaking pauses (ignore pauses under 2 seconds):
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --silent_duration 2.0 --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

For precise control over both threshold and duration:
```python
python transcribe_audio.py --makecaptions --isolate_vocals --silent_detect --silent_threshold -40.0 --silent_duration 1.5 --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

This combination:
- Extracts clean vocals (removes background music/noise)
- Skips silent regions in the cleaned audio
- Adjustable threshold for different speech volumes
- Results in faster processing and higher accuracy

### Captions Compare Mode
Generate captions with all available RAM models for quality comparison:
```python
python transcribe_audio.py --makecaptions compare --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```

With advanced features:
```python
python transcribe_audio.py --makecaptions compare --isolate_vocals --silent_detect --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile"
```
This will create files like:
- `MyCaptionsFile.11gb-v3.srt`
- `MyCaptionsFile.11gb-v2.srt`  
- `MyCaptionsFile.7gb.srt`
- `MyCaptionsFile.6gb.srt`
- `MyCaptionsFile.3gb.srt`
- `MyCaptionsFile.2gb.srt`
- `MyCaptionsFile.1gb.srt`

---
[Back to Index](./index.md)
