# General Usage

These arguments control the overall operation and behavior of Synthalingua.

## Arguments

| Flag                | Description                                                                                 |
|---------------------|-----------------------------------------------------------------------------------------|
| `--about`           | Show information about the app and contributors.                                          |
| `--updatebranch`    | Choose which branch to check for updates (`master`, `dev-testing`, `bleeding-under-work`, `disable`). |
| `--no_log`          | Only show the last line of the transcription (not a running log).                        |
| `--keep_temp`       | Keep temporary audio files (may use more disk space over time).                           |
| `--retry`           | Retries the transcription if it fails (may increase processing time).                    |

## Details & Examples

### `--about`
Shows information about Synthalingua, including contributors and version. Example:
```python
python transcribe_audio.py --about
```

### `--updatebranch`
Controls which branch is checked for updates. Example:
```python
python transcribe_audio.py --updatebranch dev-testing
```

### `--no_log`
Only the most recent line of output is shown, instead of a running log. Useful for a cleaner console.

### `--keep_temp`
Prevents deletion of temporary audio files. Useful for debugging or archiving.

### `--retry`
Retries transcription if it fails, which may increase processing time but improves reliability.

---
[Back to Index](./index.md)
