# General Usage

These arguments control the overall operation and behavior of Synthalingua.

## Arguments

| Flag                | Description                                                                                 |
|---------------------|-----------------------------------------------------------------------------------------|
| `--about`           | Show information about the app and contributors.                                          |
| `--updatebranch`    | Choose which branch to check for updates (`master`, `dev-testing`, `bleeding-under-work`, `disable`). |
| `--no_log`          | Only show the last line of the transcription (not a running log).                        |
| `--keep_temp`       | Keep temporary audio files (may use more disk space over time).                           |
| `--save_transcript` | Save the transcript to a text file.                                                      |
| `--save_folder`     | Set the folder to save the transcript to.                                                |

## Details & Examples

### `--about`
Shows information about Synthalingua, including contributors and version. Example:
```
python transcribe_audio.py --about
```

### `--updatebranch`
Controls which branch is checked for updates. Example:
```
python transcribe_audio.py --updatebranch dev-testing
```

### `--no_log`
Only the most recent line of output is shown, instead of a running log. Useful for a cleaner console.

### `--keep_temp`
Prevents deletion of temporary audio files. Useful for debugging or archiving.

### `--save_transcript` & `--save_folder`
Saves all transcriptions to a text file. You can specify the folder with `--save_folder`.

---
[Back to Index](./index.md)
