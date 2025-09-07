# Synthalingua
> **Note:** The Synthalingua Wrapper code has been moved to a new repo here: https://github.com/cyberofficial/Synthalingua_Wrapper
> By using Synthalingua, you agree to use it responsibly and accept full responsibility for your actions. Let's keep it fun, safe, and positive for everyone!

- **Real-time translation & transcription** (stream, mic, file)
- **Multilingual**: Translate between dozens of languages
- **Streaming & captions**: HLS, YouTube, Twitch, and more
- **Blocklist & repetition suppression**: Auto-filter repeated or unwanted phrases
- **Discord & web integration**: Send results to Discord or view in browser
- **Portable GUI version available**

---

## Don't have the hardware for Synthalingua? Use Recall.ai - Meeting Transcription API
If you’re looking for a transcription API for meetings, consider checking out [Recall.ai](https://www.recall.ai/?utm_source=github&utm_medium=sponsorship&utm_campaign=cyb3rofficial-synthalingua), an API that works with Zoom, Google Meet, Microsoft Teams, and more. Recall.ai diarizes by pulling the speaker data and separate audio streams from the meeting platforms, which means 100% accurate speaker diarization with actual speaker names.

[<img src="https://i.imgur.com/dyZz6u5.png" width=60%>](https://cyberofficial.itch.io/synthalingua)

<img src="https://github.com/cyberofficial/Synthalingua/assets/19499442/c81d2c51-bf85-4055-8243-e6a1262cce8a" width=70%>

<a href="https://www.producthunt.com/posts/synthalingua?embed=true&utm_source=badge-featured&utm_medium=badge&utm_souce=badge-synthalingua" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=963036&theme=dark&t=1746865849346" alt="Synthalingua - Synthalingua&#0032;&#0045;&#0032;Real&#0032;Time&#0032;Translation | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>

---

[![CodeQL](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml/badge.svg)](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml)

## Table of Contents
- [About](#about-synthalingua)
- [Documentation Wiki](#documentation-wiki)
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
- [Support Synthalingua](#support-synthalingua) 

---

## Documentation Wiki

**For comprehensive guides and detailed documentation, visit the official Synthalingua Wiki:**

[https://github.com/cyberofficial/Synthalingua/wiki](https://github.com/cyberofficial/Synthalingua/wiki)

The GitHub Wiki contains detailed guides for every feature, including setup, usage, troubleshooting, and advanced options. Always check the wiki for the latest documentation and tips!

---

## About Synthalingua
Synthalingua is an advanced, self-hosted tool that leverages the power of artificial intelligence to translate audio from various languages into English in near real time, offering the possibility of multilingual outputs. This innovative solution utilizes both GPU and CPU resources to handle input transcription and translation, ensuring optimized performance.

While currently in beta and not perfect, Synthalingua is actively being developed and will receive regular updates to further enhance its capabilities.

Synthalingua started as a very personal project for me. I was inspired by my love for VTubers, many of whom I could only understand through translated clips on YouTube. I wanted to experience their streams live, in real time, with the same depth and connection that native speakers enjoyed. While I could already watch live, it just wasn’t the same without fully understanding what was being said in the moment. That frustration turned into motivation, and I began working on a tool that could break through improve the experience.

What started as a small, personal endeavor quickly grew into something much larger than I could have imagined. The idea that language should never be a barrier to connection, whether in the VTuber community or beyond, really resonated with me. I wanted to create something that would allow anyone, anywhere, to fully experience the rich conversations, emotions, and stories that come from people speaking in their own native tongue - and that’s how Synthalingua was born.

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

---

## Quick Start
1. **Install Python 3.12** from [here](https://www.python.org/downloads/release/python-31210/) and [Git](https://git-scm.com/downloads)
2. **Install FFMPEG** ([guide](https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222))
3. *(Optional)* Install [CUDA 12.8](https://developer.nvidia.com/cuda-12-8-0-download-archive) for GPU acceleration if you plan to use GPU features
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
| Requirement | Minimum | Moderate | Recommended | Best Performance | 
|-----|-----|-----|-----|-----|
| CPU | 2 cores, 2.0 GHz+ | 4 cores, 3.0 GHz+ | 8 cores, 3.5 GHz+ | 16+ cores, 4.0 GHz+ | 
| RAM | 4 GB | 8 GB | 16 GB | 32+ GB | 
| GPU (Nvidia) | 2GB VRAM (Kepler/Maxwell, e.g. GTX 750 Ti) | 4GB VRAM (Pascal, e.g. GTX 1050 Ti) | 8GB VRAM (Turing/Ampere, e.g. RTX 2070/3070) | 12GB+ VRAM (RTX 3080/3090, A6000, etc.) |
| GPU (AMD/Linux) | 4GB VRAM (experimental) | 8GB VRAM | 12GB+ VRAM | 16GB+ VRAM |
| OS | Windows 10+, Linux | Windows 10+, Linux | Windows 10+, Linux | Windows 10+, Linux |
| Storage | 2 GB free | 10 GB free | 20 GB+ free | SSD/NVMe recommended | 

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
1. Install [Python 3.12](https://www.python.org/downloads/release/python-31210/)
2. Install [Git](https://git-scm.com/downloads)
3. Install FFMPEG ([guide](https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222))
4. *(Optional)* Install [CUDA 12.8](https://developer.nvidia.com/cuda-12-8-0-download-archive) for GPU if you plan to use GPU features
5. Run `setup.bat` (Windows) or `setup.bash` (Linux)
6. Edit and run the generated batch/bash file, or use the GUI

---

## Command-Line Arguments

### General
| Flag | Description |
|-----|-----|
| `--about` | Show app info |
| `--updatebranch` | Update branch (master/dev-testing/bleeding-under-work/disable) |
| `--no_log` | Only show last line of output |
| `--keep_temp` | Keep temp audio files |
| `--save_transcript` | Save transcript to file |
| `--save_folder` | Set transcript save folder |

### Model & Device
| Flag | Description |
|-----|------|
| `--ram` | Model size (1gb, 2gb, 3gb, 6gb, 11gb-v2, 11gb-v3) |
| `--ramforce` | Force RAM/VRAM model |
| `--fp16` | Enable FP16 mode |
| `--device` | Device: (auto/cpu/cuda/intel-igpu/intel-dgpu/intel-npu) |
| `--cuda_device` | CUDA device index |
| `--model_dir` | Model directory |
| `--model_source` | Source of the model (Whisper, FasterWhisper, OpenVINO)  |
| `--compute_type` | Quantization of the model |

### Input & Microphone
| Flag | Description |
|-----|-----|
| `--microphone_enabled` | Enable microphone input |
| `--list_microphones` | List microphones |
| `--set_microphone` | Set mic by name or index |
| `--energy_threshold` | Mic energy threshold |
| `--mic_calibration_time` | Mic calibration time |
| `--record_timeout` | Recording chunk length |
| `--phrase_timeout` | Silence before new line |

### Streaming & File
| Flag | Description |
|-----|-----|
| `--selectsource` | Select the stream audio source (interactive.) |
| `--stream` | HLS stream input |
| `--stream_language` | Stream language |
| `--stream_translate` | Enable stream translation |
| `--stream_transcribe [language]` | Enable stream transcription with optional target language (e.g., --stream_transcribe English) |
| `--stream_original_text` | Show original stream text |
| `--stream_chunks` | Stream chunk size |
| `--paddedaudio` | Number of chunks to overlap from previous batch for better context (works with both --stream and microphone input) |
| `--auto_hls` | Auto HLS chunk tuning |
| `--cookies` | Cookies file (supports absolute paths, current dir, or cookies/ folder) |
| `--remote_hls_password_id` | Webserver password ID |
| `--remote_hls_password` | Webserver password for|

### Language & Translation
| Flag | Description |
|-----|-----|
| `--language` | Source language |
| `--target_language` | Target language |
| `--translate` | Enable translation |
| `--transcribe` | Transcribe to target language |
| `--auto_language_lock` | Auto language lock |
| `--condition_on_previous_text` | Suppress repeated/similar messages |

### Output, Captions, and Filtering
| Flag | Description |
|-----|-----|
| `--makecaptions` | Captions mode. Use `--makecaptions compare` to generate captions with all RAM models |
| `--subtype` | Process video with subtitles after generation. 'burn' overlays subtitles permanently onto video. 'embed' adds subtitle track to video container. Only works with `--makecaptions` and video files. |
| `--substyle` | Customize burned subtitle appearance (only with `--subtype burn`). Format: 'font,size,color' in any order. Font files go in `fonts/` folder. Use `--substyle help` for examples. |
| `--word_timestamps` | Enable word-level timestamps in subtitle output (sub_gen only). May make subtitle generation slower as it requires more processing power. If you notice slowdowns, remove this flag next time. Has no effect in microphone or HLS/stream modes. |
| `--isolate_vocals` | Attempt to isolate vocals from the input audio before generating subtitles (sub_gen only). Requires the demucs package. |
| `--demucs_model` | Demucs model to use for vocal isolation. Choices: `htdemucs` (default), `htdemucs_ft`, `htdemucs_6s`, `hdemucs_mmi`, `mdx`, `mdx_extra`, `mdx_q`, `mdx_extra_q`, `hdemucs`, `demucs`. Only used when `--isolate_vocals` is enabled. |
| `--silent_detect` | Skip processing silent audio chunks during caption generation (sub_gen only). Improves processing speed for files with long silent periods. Highly recommended with `--isolate_vocals` for maximum efficiency. **Note:** Only works with `--makecaptions` - not supported for HLS/streaming or microphone modes. |
| `--silent_threshold` | dB threshold for silence detection (default: -35.0). Lower values (e.g., -45.0) detect quieter speech like whispers. Higher values (e.g., -25.0) only detect louder speech. Only used with `--silent_detect`. |
| `--silent_duration` | Minimum duration in seconds for a region to be considered silence (default: 0.5). Higher values (e.g., 2.0) treat brief pauses as speech. Lower values (e.g., 0.1) detect shorter silent periods. Only used with `--silent_detect`. |
| `--print_srt_to_console` | Print the final generated SRT subtitles to the console after file creation (captions mode only). |
| `--file_input` | Input file for captions |
| `--file_output` | Output folder for captions |
| `--file_output_name` | Output file name |
| `--ignorelist` | Blocklist file (words/phrases) |
| `--auto_blocklist` | Auto-add frequently blocked phrases to blocklist |
| `--debug` | Print debug info for blocked/suppressed messages |
### Print SRT to Console
The `--print_srt_to_console` flag prints the final, fully combined SRT subtitles to the console after the SRT file is created (captions mode only). This is useful for quickly viewing the generated subtitles without opening the SRT file manually. It only prints the final combined SRT (not per-segment SRTs) and works with `--makecaptions`.

**Example:**
```sh
python synthalingua.py --makecaptions --file_input="C:/path/video.mp4" --file_output="C:/output" --file_output_name="MyCaptionsFile" --print_srt_to_console
```
This will save the SRT file as usual and also print its contents to the console at the end of processing.

### Web & Discord
| Flag | Description |
|-----|-----|
| `--portnumber` | Web server port |
| `--discord_webhook` | Discord webhook URL |

---

## Usage Examples
- **Stream translation:**
  ```sh
  python synthalingua.py --ram 11gb-v3 --stream_translate --stream_language Japanese --stream https://www.twitch.tv/somestreamerhere
  ```
- **Microphone translation:**
  ```sh
  python synthalingua.py --ram 6gb --translate --language ja --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890" --energy_threshold 300
  ```
- **Captions mode:**
  ```sh
  python synthalingua.py --ram 11gb-v3 --makecaptions --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With word-level timestamps (may be slower):
  python synthalingua.py --ram 11gb-v3 --makecaptions --word_timestamps --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With vocal isolation (requires demucs):
  python synthalingua.py --ram 11gb-v3 --makecaptions --isolate_vocals --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With vocal isolation using specific model (skip interactive prompt):
  python synthalingua.py --ram 11gb-v3 --makecaptions --isolate_vocals --demucs_model htdemucs_ft --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With silence detection (faster processing for long silent periods):
  python synthalingua.py --ram 11gb-v3 --makecaptions --silent_detect --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With custom silence threshold for quiet speech (e.g., whispers):
  python synthalingua.py --ram 11gb-v3 --makecaptions --silent_detect --silent_threshold -45.0 --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With custom duration to ignore brief pauses (e.g., 2s minimum):
  python synthalingua.py --ram 11gb-v3 --makecaptions --silent_detect --silent_duration 2.0 --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # RECOMMENDED: Vocal isolation + silence detection (maximum efficiency and quality):
  python synthalingua.py --ram 11gb-v3 --makecaptions --isolate_vocals --silent_detect --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Captions compare mode (all models):**
  ```sh
  python synthalingua.py --makecaptions compare --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With word-level timestamps (may be slower):
  python synthalingua.py --makecaptions compare --word_timestamps --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # With vocal isolation (requires demucs):
  python synthalingua.py --makecaptions compare --isolate_vocals --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # RECOMMENDED: Vocal isolation + silence detection (maximum efficiency and quality):
  python synthalingua.py --makecaptions compare --isolate_vocals --silent_detect --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Video subtitle processing (burn subtitles permanently):**
  ```sh
  python synthalingua.py --makecaptions --subtype burn --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Video subtitle processing (embed toggleable subtitles):**
  ```sh
  python synthalingua.py --makecaptions --subtype embed --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  ```
- **Custom styled burned subtitles:**
  ```sh
  # Large yellow text with custom font
  python synthalingua.py --makecaptions --subtype burn --substyle "FiraSans-Bold.otf,28,yellow" --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # System font with size and color
  python synthalingua.py --makecaptions --subtype burn --substyle "22,cyan" --file_input="C:\Users\username\Downloads\file.mp4" --file_output="C:\Users\username\Downloads" --file_output_name="outputname" --language Japanese --device cuda
  # Get help and see available fonts
  python synthalingua.py --substyle help
  ```
- **Set microphone by name or index:**
  ```sh
  python synthalingua.py --set_microphone "Microphone (Realtek USB2.0 Audi)"
  python synthalingua.py --set_microphone 4
  ```

---

## Caption Generation Optimization

### Advanced Caption Features
For the best caption generation experience, Synthalingua offers several advanced features that can be combined:

#### **Silent Detection (`--silent_detect`)**
- **What it does:** Intelligently skips silent regions in audio files
- **Benefits:** Faster processing, reduced resource usage, better transcription quality
- **Best for:** Podcasts, lectures, videos with long pauses or intro/outro music
- **Usage:** Only works with `--makecaptions` (caption generation mode)
- **Not supported:** HLS/streaming modes or microphone input
- **Customizable settings:**
  - **Threshold (`--silent_threshold`):** Controls volume sensitivity
    - **Default:** -35.0dB (good for normal speech)
    - **Quiet speech/whispers:** -45.0dB or lower (more sensitive)
    - **Loud speech only:** -25.0dB or higher (less sensitive)
  - **Duration (`--silent_duration`):** Controls minimum silence length
    - **Default:** 0.5s (brief pauses treated as speech)
    - **Ignore short pauses:** 2.0s+ (only long silences count)
    - **Detect quick breaks:** 0.1s (very sensitive to gaps)

#### **Vocal Isolation (`--isolate_vocals`)**
- **What it does:** Separates vocals from background music/noise using AI (requires demucs)
- **Benefits:** Cleaner transcription, better accuracy in noisy environments
- **Best for:** Music videos, podcasts with background music, noisy recordings
- **Requires:** `pip install demucs` or included in some distributions

#### ** Maximum Efficiency Combo (RECOMMENDED)**
Combine both features for optimal results:
```sh
python synthalingua.py --makecaptions --isolate_vocals --silent_detect --file_input="your_file.mp4"
```

**Why this combination works so well:**
1. **Vocal isolation** removes background noise/music, creating cleaner audio
2. **Silent detection** analyzes the cleaned audio for more accurate silence detection
3. **Result:** Only speech regions from isolated vocals are processed
4. **Benefits:** 
   - **Fastest processing** (skips silence and noise)
   - **Highest accuracy** (clean vocal-only audio)
   - **Resource efficient** (processes less audio overall)
   - **Natural boundaries** (respects speech patterns, no mid-word cuts)

#### **Processing Workflow**
1. **Input:** Original audio/video file
2. **Vocal Isolation:** Extracts clean vocals (if `--isolate_vocals`)
3. **Silence Detection:** Finds speech regions in vocal track (if `--silent_detect`)
4. **Transcription:** Processes only speech regions with natural boundaries
5. **Output:** High-quality SRT captions with perfect timestamps

#### ** Pro Tips**
- Use `--makecaptions compare` with both flags to test all models efficiently
- Silent detection works on any audio, but is most effective with vocal isolation
- Both features maintain perfect timestamp accuracy in final SRT files
- Vocal isolation creates temporary files in `temp/audio/` directory

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
python synthalingua.py --ram 6gb --translate --language ja --portnumber 8080

# For remote HLS password protection
python synthalingua.py --ram 6gb --translate --portnumber 8080 --remote_hls_password_id "user" --remote_hls_password "yourpassword"
```

---

## Troubleshooting
- **Python not recognized:** Add Python to PATH, restart, check version (should be 3.12)
- **No module named 'transformers':** Run `pip install transformers` in the correct Python environment
- **Git not recognized:** Add Git to PATH, restart
- **CUDA not available:** Install [CUDA 12.8](https://developer.nvidia.com/cuda-12-8-0-download-archive) (Nvidia only), or use CPU mode
- **Audio source errors:** Make sure a microphone or stream is set up
- **For detailed troubleshooting:** See the [Troubleshooting Guide](./information/troubleshooting.md) in the information folder
- **Other issues:** See [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues)

---

## Contributors
- [@DaniruKun](https://github.com/DaniruKun) - https://watsonindustries.live
- [@Expletive](https://github.com/Expletive) - https://evitelpxe.neocities.org
- [@Adenser](https://github.com/Adenser)
- [@YuumiPie](https://github.com/YuumiPie)

---

## Video Demonstration
Command line arguments used: `--ram 6gb --record_timeout 2 --language ja --energy_threshold 500`
[<img src="https://i.imgur.com/sXTWr76.jpg" width="50%">](https://streamable.com/m9mhfr)

Command line arguments used: `--ram 11gb-v2 --record_timeout 5 --language id --energy_threshold 500`
[<img src="https://i.imgur.com/2WbWpH4.jpg" width="50%">](https://streamable.com/skuhoh)

---

## Support Synthalingua
If Synthalingua has made a difference in your life and you find yourself using it regularly, I would be truly grateful if you considered supporting its continued development. 😁 Running a GPU at full power day in and day out requires a lot of resources, and the cost of electricity and maintenance adds up over time. Any contribution, no matter how small, would help tremendously in keeping this project going strong and ensuring that I can continue to improve and expand it for everyone.

Your support would not just help cover the costs of running and maintaining Synthalingua, it would also be a vote of confidence in this vision — a world where language doesn’t stand in the way of connection and understanding. I believe that no one should feel left out of a new experience just because it’s in a different language. Every conversation, every voice, deserves to be understood and appreciated. If you can not support through monetary means, just sharing the application would also be a great benefit to those who want the same experience I wanted but don't know where to begin.

Synthalingua will always remain free, because I want this tool to be available to anyone who needs it, regardless of their financial situation. But if it has enriched your experience, opened up new possibilities for you, or simply made your world a little bigger, your support would mean the world to me. It helps keep this project alive and ensures that others can also benefit from this tool and the vision behind it.

Thank you for being part of this journey. Your belief in Synthalingua and its mission is what drives me to keep going, and I’m incredibly grateful for every one of you who uses and believes in this project. Together, we can help build a future where communication knows no boundaries, and language is a bridge rather than a barrier.


**Support via:**

[<img src="https://i.imgur.com/dyZz6u5.png" width=60%>](https://cyberofficial.itch.io/synthalingua)

[<img src="https://i.imgur.com/ghRdIqe.png" alt="Support me on Ko-fi" width="200">](https://ko-fi.com/cyberofficial)

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

### Word-level Timestamps
The `--word_timestamps` flag enables word-level timestamps in subtitle output (sub_gen/captions mode only). This provides more precise alignment but may make subtitle generation a bit slower as it requires more processing power. If you notice any unusual slowdowns, try removing the flag next time you run this command.

**Note:** This flag has no effect in microphone or HLS/stream modes, and will show a warning if used there.

### Vocal Isolation
The `--isolate_vocals` flag attempts to isolate vocals from the input audio before generating subtitles (sub_gen/captions mode only). This can improve subtitle accuracy for music or noisy audio, but may take additional time and requires the `demucs` package. If `demucs` is not installed, a warning will be shown.

**Demucs Model Selection:**
- By default, the program will prompt you to select which Demucs model to use for vocal isolation
- You can skip the prompt by using `--demucs_model` to specify the model directly
- Available models:
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

**Examples:**
```sh
# Interactive model selection (default behavior)
python synthalingua.py --makecaptions --isolate_vocals --file_input="video.mp4"

# Specify model directly (no prompt)
python synthalingua.py --makecaptions --isolate_vocals --demucs_model htdemucs_ft --file_input="video.mp4"

# For best quality (slower)
python synthalingua.py --makecaptions --isolate_vocals --demucs_model htdemucs_ft --file_input="video.mp4"

# For fastest processing
python synthalingua.py --makecaptions --isolate_vocals --demucs_model mdx_q --file_input="video.mp4"
```

**Note:** This flag has no effect in microphone or HLS/stream modes.

