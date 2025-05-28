# Output, Captions, and Filtering

These arguments control output formatting, captions, and filtering of unwanted content.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--ignorelist`          | Path to a blacklist file for filtering words/phrases.             |
| `--auto_blocklist`      | Auto-add frequently blocked phrases to the blocklist file.        |
| `--debug`               | Print debug output for blocked/suppressed messages.               |
| `--makecaptions`        | Enable captions mode. Use `--makecaptions compare` to generate captions with all RAM models (11gb-v3, 11gb-v2, 7gb, 6gb, 3gb, 2gb, 1gb). |
| `--file_input`          | Path to input file for captioning.                                |
| `--file_output`         | Output folder for captions.                                       |
| `--file_output_name`    | Output file name (without extension).                             |

## Details & Examples

### `--ignorelist`
Load a blacklist file (one word/phrase per line) to filter unwanted content from all outputs.

### `--auto_blocklist`
When enabled (with `--ignorelist`), phrases blocked 3+ times in the last 10 are auto-added to your blocklist.

### `--debug`
Prints debug info about blocked or suppressed messages.

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
