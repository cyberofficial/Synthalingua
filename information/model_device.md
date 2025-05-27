# Model & Device Options

These arguments control which AI model is used and how it runs on your hardware.

## Arguments
| Flag            | Description                                                                 |
|-----------------|-----------------------------------------------------------------------------|
| `--ram`         | Model size (choices: `1gb`, `2gb`, `4gb`, `6gb`, `11gb-v2`, `11gb-v3`).     |
| `--ramforce`    | Force the script to use the selected RAM/VRAM model.                        |
| `--fp16`        | Enable FP16 mode for faster inference (may reduce accuracy slightly).        |
| `--device`      | Select device for inference (`cpu` or `cuda`).                              |
| `--cuda_device` | Select CUDA device index (default: 0).                                      |
| `--model_dir`   | Directory to store/download models.                                          |

## Details & Examples

### `--ram` & `--ramforce`
Choose a model size that fits your hardware. For example:
```
python transcribe_audio.py --ram 6gb
```
Use `--ramforce` to override automatic checks (use with caution).

### `--fp16`
Enables half-precision mode for faster processing on supported GPUs.

### `--device` & `--cuda_device`
Selects CPU or GPU for inference. Example:
```
python transcribe_audio.py --device cuda --cuda_device 1
```

### `--model_dir`
Change where models are stored/downloaded. Example:
```
python transcribe_audio.py --model_dir "C:/models"
```

---
[Back to Index](./index.md)
