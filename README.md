# Synthalingua
> **Note:** The Synthalingua Wrapper code has been moved to a new repository: [Synthalingua_Wrapper](https://github.com/cyberofficial/Synthalingua_Wrapper)

<img src="https://github.com/cyberofficial/Synthalingua/assets/19499442/c81d2c51-bf85-4055-8243-e6a1262cce8a" width=70%>

<a href="https://www.producthunt.com/posts/synthalingua?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-synthalingua" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=963036&theme=dark&t=1746865849346" alt="Synthalingua - Synthalingua&#0032;&#0045;&#0032;Real&#0032;Time&#0032;Translation | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

---

[![CodeQL](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml/badge.svg)](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml)

## Table of Contents
- [About](#about)
- [Quick Start](#quick-start)
- [Feature Highlights](#feature-highlights)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Command-Line Arguments](#command-line-arguments)
- [Usage Examples](#usage-examples)
- [Blocklist & Filtering](#blocklist--filtering)
- [Web & Discord Integration](#web--discord-integration)
- [Troubleshooting](#troubleshooting)
- [Contributors](#contributors)
- [Video Demonstration](#video-demonstration)

---


## About
Synthalingua is a self-hosted AI tool for real-time audio translation and transcription. It supports multilingual input and output, streaming, microphone, and file modes, and is optimized for both GPU and CPU. The project is in active development and open source.

## Legal & Friendly Disclaimer
Hey there! Synthalingua is a fun and powerful tool for exploring languages, learning, and enjoying live translations. But just like any tool, it comes with a few important guidelines to keep things safe, legal, and friendly for everyone.

- **Synthalingua is a tool, not a service.** You run it on your own computer, and you are in control. It’s not a replacement for professional translators or interpreters.
- **For fun, learning, and curiosity!** Use Synthalingua to practice languages, understand foreign content, or experiment with AI audio. It’s great for hobbyists, students, and anyone curious about language tech.
- **Not for official or critical use.** Please don’t rely on Synthalingua for legal, medical, business, or other important communications. For anything serious, always consult a qualified human expert.
- **Be kind and ethical.** Don’t use Synthalingua to spread misinformation, harass others, or break the law. Respect the rules of any platform you use it with.
- **Respect privacy and copyright.** Only process audio or video you have the right to use. Don’t share or transcribe private conversations without permission.
- **No warranty or liability.** I built Synthalingua for the community, but I can’t take responsibility for how it’s used. You use it at your own risk.

### 👍 Examples of Good Use
- Translating a livestream for your own understanding
- Practicing a new language by listening to foreign media
- Making fun subtitles for a YouTube video you have rights to
- Learning how AI models handle different accents or languages

### 🚫 Please Don’t
- Use Synthalingua to translate confidential work meetings or private calls without consent
- Rely on it for medical, legal, or business decisions
- Use it to bypass paywalls, copyright, or platform rules
- Share or publish AI-generated translations as if they are 100% accurate or official

By using Synthalingua, you agree to use it responsibly and accept full responsibility for your actions. Let’s keep it fun, safe, and positive for everyone!

- **Real-time translation & transcription** (stream, mic, file)
- **Multilingual**: Translate between dozens of languages
- **Streaming & captions**: HLS, YouTube, Twitch, and more
- **Blocklist & repetition suppression**: Auto-filter repeated or unwanted phrases
- **Discord & web integration**: Send results to Discord or view in browser
- **Portable GUI version available**

---

## Quick Start
1. **Install Python 3.10.9+ (not 3.11+)** and [Git](https://git-scm.com/downloads)
2. **Install FFMPEG** ([guide](https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222))
3. *(Optional)* Install CUDA for GPU acceleration
4. Run `setup.bat` (Windows) or `setup.bash` (Linux)
5. Edit and run the generated batch/bash file, or use the GUI portable version:

[<img src="https://i.imgur.com/dyZz6u5.png" width=60%>](https://cyberofficial.itch.io/synthalingua)

---

## Feature Highlights
- **Suppress repeated/similar messages**: Prevents spam from repeated or hallucinated phrases in all modes
- **Auto blocklist**: Frequently blocked phrases are auto-added to your blocklist file
- **Flexible input**: Microphone, HLS stream, or file
- **Captions mode**: Generate subtitles for any audio/video file
- **Web server**: View live subtitles in your browser
- **Discord integration**: Send results to a Discord channel
- **Customizable**: Blocklist, language, device, RAM, and more

---

## System Requirements
| Requirement      | Minimum                | Moderate                | Recommended           | Best Performance      |
|------------------|------------------------|-------------------------|-----------------------|----------------------|
| CPU              | 2 cores, 2.0 GHz+      | 4 cores, 3.0 GHz+       | 8 cores, 3.5 GHz+     | 16+ cores, 4.0 GHz+  |
| RAM              | 4 GB                   | 8 GB                    | 16 GB                 | 32+ GB               |
| GPU (Nvidia)     | 2GB VRAM (Kepler/Maxwell, e.g. GTX 750 Ti) | 4GB VRAM (Pascal, e.g. GTX 1050 Ti) | 8GB VRAM (Turing/Ampere, e.g. RTX 2070/3070) | 12GB+ VRAM (RTX 3080/3090, A6000, etc.) |
| GPU (AMD/Linux)  | 4GB VRAM (experimental) | 8GB VRAM                | 12GB+ VRAM            | 16GB+ VRAM           |
| OS               | Windows 10+, Linux     | Windows 10+, Linux      | Windows 10+, Linux    | Windows 10+, Linux   |
| Storage          | 2 GB free              | 10 GB free              | 20 GB+ free           | SSD/NVMe recommended |

**Supported GPUs:**
- Nvidia: Most CUDA-capable cards (Kepler, Maxwell, Pascal, Turing, Ampere, Ada; e.g. GTX 750 Ti, 1050 Ti, 1660, RTX 2060/2070/2080/3060/3070/3080/3090/40xx, A6000, etc.)
- AMD: ROCm-compatible cards (Linux only, experimental)
- CPU: Supported (slower, but works for small models)

**Notes:**
- Nvidia GPU with CUDA is strongly recommended for best performance.
- AMD GPU support is experimental and Linux-only (see [ROCm docs](https://rocmdocs.amd.com/en/latest/)).
- CPU-only mode is available for testing or low-resource systems.
- Microphone is optional (use `--stream` for HLS input).
- For a full list of supported Nvidia GPUs, see the [Official Nvidia List](https://developer.nvidia.com/cuda-gpus) or [Simple Nvidia List](https://gist.github.com/standaloneSA/99788f30466516dbcc00338b36ad5acf).

---

## Installation
1. Install [Python 3.10.9+](https://www.python.org/downloads/release/python-3109/) (not 3.11+)
2. Install [Git](https://git-scm.com/downloads)
3. Install FFMPEG ([guide](https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222))
4. *(Optional)* Install CUDA for GPU
5. Run `setup.bat` (Windows) or `setup.bash` (Linux)
6. Edit and run the generated batch/bash file, or use the GUI

---

## Command-Line Arguments

### General
| Flag | Description |
|------|-------------|
| `--about` | Show app info |
| `--updatebranch` | Update branch (master/dev-testing/bleeding-under-work/disable) |
| `--no_log` | Only show last line of output |
| `--keep_temp` | Keep temp audio files |
| `--save_transcript` | Save transcript to file |
| `--save_folder` | Set transcript save folder |

### Model & Device
| Flag | Description |
|------|-------------|
| `--ram` | Model size (1gb, 2gb, 3gb, 6gb, 11gb-v2, 11gb-v3) |
| `--ramforce` | Force RAM/VRAM model |
| `--fp16` | Enable FP16 mode |
| `--device` | Device: cpu/cuda |
| `--cuda_device` | CUDA device index |
| `--model_dir` | Model directory |

### Input & Microphone
| Flag | Description |
|------|-------------|
| `--microphone_enabled` | Enable microphone input |
| `--list_microphones` | List microphones |
| `--set_microphone` | Set mic by name or index |
| `--energy_threshold` | Mic energy threshold |
| `--mic_calibration_time` | Mic calibration time |
| `--record_timeout` | Recording chunk length |
| `--phrase_timeout` | Silence before new line |

### Streaming & File
| Flag | Description |
|------|-------------|
| `--selectsource` | Select the stream audi source (interactive.) |
| `--stream` | HLS stream input |
| `--stream_language` | Stream language |
| `--stream_target_language` | [DEPRECATED - WILL BE REMOVED SOON] Stream translation target (use --stream_transcribe <language> instead) |
| `--stream_translate` | Enable stream translation |
| `--stream_transcribe [language]` | Enable stream transcription with optional target language (e.g., --stream_transcribe English) |
| `--stream_original_text` | Show original stream text |
| `--stream_chunks` | Stream chunk size |
| `--auto_hls` | Auto HLS chunk tuning |
| `--cookies` | Cookies file (supports absolute paths, current dir, or cookies/ folder) |
| `--remote_hls_password_id` | Webserver password ID |
| `--remote_hls_password` | Webserver password |

### Language & Translation
| Flag | Description |
|------|-------------|
| `--language` | Source language |
| `--target_language` | Target language |
| `--translate` | Enable translation |
| `--transcribe` | Transcribe to target language |
| `--auto_language_lock` | Auto language lock |
| `--condition_on_previous_text` | Suppress repeated/similar messages |

### Output, Captions, and Filtering
| Flag | Description |
|------|-------------|
| `--makecaptions` | Captions mode. Use `--makecaptions compare` to generate captions with all RAM models |
| `--file_input` | Input file for captions |
| `--file_output` | Output folder for captions |
| `--file_output_name` | Output file name |
| `--ignorelist` | Blocklist file (words/phrases) |
| `--auto_blocklist` | Auto-add frequently blocked phrases to blocklist |
| `--debug` | Print debug info for blocked/suppressed messages |

### Web & Discord
| Flag | Description |
|------|-------------|
| `--portnumber` | Web server port |
| `--discord_webhook` | Discord webhook URL |

---

## Usage Examples
- **Stream translation:**
  ```sh
  python transcribe_audio.py --ram 11gb-v3 --stream_translate --stream_language Japanese --stream https://www.twitch.tv/somestreamerhere
  ```
- **Microphone translation:**
  ```sh
  python transcribe_audio.py --ram 6gb --translate --language ja --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890" --energy_threshold 300
  ```
- **Captions mode:**
  ```sh
  python transcribe_audio.py --ram 11gb-v3 --makecaptions --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Captions compare mode (all models):**
  ```sh
  python transcribe_audio.py --makecaptions compare --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Set microphone by name or index:**
  ```sh
  python transcribe_audio.py --set_microphone "Microphone (Realtek USB2.0 Audi)"
  python transcribe_audio.py --set_microphone 4
  ```

---

## Blocklist & Filtering
- Use `--ignorelist` to load a blocklist file (one word/phrase per line)
- **Suppression:** With `--condition_on_previous_text`, repeated or highly similar messages are automatically suppressed in all modes
- **Auto blocklist:** With `--auto_blocklist` and `--ignorelist`, phrases blocked 3+ times in the last 10 are auto-added to your blocklist
- **Debug:** Use `--debug` to print info about blocked/suppressed messages
- Blocklist and suppression logic applies to all output (console, Discord, web)

---

## Web & Discord Integration
- **Discord:** Use `--discord_webhook` to send results to Discord (long messages are split, rate limits handled)
- **Web server:** Use `--portnumber` to launch a local Flask server and view subtitles in your browser

### Accessing the Web Server
Once you've launched Synthalingua with the `--portnumber` parameter:

1. Open your web browser and navigate to `http://localhost:[PORT]` (replace `[PORT]` with the port number you specified)
2. Example: `http://localhost:8080` if you used `--portnumber 8080`
3. For accessing from other devices on your network, use your computer's IP address: `http://[YOUR_IP]:[PORT]`

**Example usage:**
```sh
# Start Synthalingua with a web server on port 8080
python transcribe_audio.py --ram 6gb --translate --language ja --portnumber 8080

# For remote HLS password protection
python transcribe_audio.py --ram 6gb --translate --portnumber 8080 --remote_hls_password_id "user" --remote_hls_password "yourpassword"
```

---

## Troubleshooting
- **Python not recognized:** Add Python to PATH, restart, check version (must be 3.10.x, not 3.11+)
- **No module named 'transformers':** Run `pip install transformers` in the correct Python environment
- **Git not recognized:** Add Git to PATH, restart
- **CUDA not available:** Install CUDA (Nvidia only), or use CPU mode
- **Audio source errors:** Make sure a microphone or stream is set up
- **Other issues:** See [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues)

---

## Contributors
- [@DaniruKun](https://github.com/DaniruKun) - https://watsonindustries.live
- [@Expletive](https://github.com/Expletive) - https://evitelpxe.neocities.org
- [@Adenser](https://github.com/Adenser)

---

## Video Demonstration
Command line arguments used: `--ram 6gb --record_timeout 2 --language ja --energy_threshold 500`
[<img src="https://i.imgur.com/sXTWr76.jpg" width="50%">](https://streamable.com/m9mhfr)

Command line arguments used: `--ram 11gb-v2 --record_timeout 5 --language id --energy_threshold 500`
[<img src="https://i.imgur.com/2WbWpH4.jpg" width="50%">](https://streamable.com/skuhoh)

---

## Credits
Developed proudly in PyCharm IDE from JetBrains
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="15%">](https://www.jetbrains.com/?from=Synthalingua)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm.png" width="35%">](https://www.jetbrains.com/pycharm/?from=Synthalingua)

JetBrains kindly provided an OSS license for this project, greatly improving development productivity. [Learn more](https://jb.gg/OpenSourceSupport?from=Synthalingua)

---

## More
- [Wiki](https://github.com/cyberofficial/Synthalingua/wiki)
- [Official Nvidia List](https://developer.nvidia.com/cuda-gpus)
- [Simple Nvidia List](https://gist.github.com/standaloneSA/99788f30466516dbcc00338b36ad5acf)
- [FFMPEG Install Guide](https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222)

