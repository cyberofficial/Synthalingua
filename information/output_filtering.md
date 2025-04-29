# Output, Captions, and Filtering

These arguments control output formatting, captions, and filtering of unwanted content.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--ignorelist`          | Path to a blacklist file for filtering words/phrases.             |
| `--auto_blocklist`      | Auto-add frequently blocked phrases to the blocklist file.        |
| `--debug`               | Print debug output for blocked/suppressed messages.               |
| `--makecaptions`        | Enable captions mode (requires file input/output/name).           |
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

---
[Back to Index](./index.md)
