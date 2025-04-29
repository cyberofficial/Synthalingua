# Input & Microphone

These arguments control microphone input and related settings.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--microphone_enabled`  | Enable microphone input.                                         |
| `--list_microphones`    | List available microphones and exit.                             |
| `--set_microphone`      | Set the default microphone by name or index.                    |
| `--energy_threshold`    | Set the energy threshold for audio detection (default: 100).     |
| `--mic_calibration_time`| Duration (seconds) for microphone calibration.                  |
| `--record_timeout`      | Real-time recording chunk length (seconds).                      |
| `--phrase_timeout`      | Silence duration (seconds) before starting a new transcription.  |

## Details & Examples

### `--microphone_enabled`
Enable microphone input for real-time transcription.

### `--list_microphones`
Lists all available microphones and their indices. Example:
```
python transcribe_audio.py --list_microphones
```

### `--set_microphone`
Set the microphone by name or index. Examples:
```
python transcribe_audio.py --set_microphone "Microphone (Realtek USB2.0 Audi)"
python transcribe_audio.py --set_microphone 4
```

### `--energy_threshold`
Adjusts how sensitive the microphone is to sound. Higher values = less sensitive.

### `--mic_calibration_time`
How long to calibrate the mic for background noise. Example:
```
python transcribe_audio.py --mic_calibration_time 5
```

### `--record_timeout` & `--phrase_timeout`
Control how often the mic records and when a new line is started.

---
[Back to Index](./index.md)
