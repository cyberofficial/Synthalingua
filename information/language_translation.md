# Language & Translation

These arguments control language selection and translation features.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--language`            | Source language (ISO 639-1 code or English name).                |
| `--target_language`     | Target language for translation.                                 |
| `--translate`           | Enable translation to English.                                   |
| `--transcribe`          | Transcribe audio to a set target language.                       |
| `--auto_language_lock`  | Automatically lock language after several detections.            |
| `--condition_on_previous_text` | Use previous output as prompt for next window (reduces repetition). |

## Details & Examples

### `--language` & `--target_language`
Set the source and target languages. Example:
```
python transcribe_audio.py --language ja --target_language en
```

### `--translate` & `--transcribe`
Enable translation or transcription to a target language. Example:
```
python transcribe_audio.py --translate --language ja
python transcribe_audio.py --transcribe --target_language es
```

### `--auto_language_lock`
Locks the detected language after several detections to reduce latency.

### `--condition_on_previous_text`
Helps prevent repeated or similar outputs by conditioning on previous text.

---
[Back to Index](./index.md)
