## Synthalingua 
<img src="https://github.com/cyberofficial/Synthalingua/assets/19499442/c81d2c51-bf85-4055-8243-e6a1262cce8a" width=70%>

## About

Synthalingua is an advanced, self-hosted tool that leverages the power of artificial intelligence to translate audio from various languages into English in near real time, offering the possibility of multilingual outputs. This innovative solution utilizes both GPU and CPU resources to handle the input transcription and translation, ensuring optimized performance. Although it is currently in beta and not perfect, Synthalingua is actively being developed and will receive regular updates to further enhance its capabilities.


## Developed Proudly in PyCharm IDE from JetBrains
JetBrains kindly approved me for an OSS licenses for thier software for use of this project. This will grealty improve my production rate.

Learn about it here: [https://jb.gg/OpenSourceSupport](https://jb.gg/OpenSourceSupport?from=Synthalingua)

[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="15%">](https://www.jetbrains.com/?from=Synthalingua)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm.png" width="35%">](https://www.jetbrains.com/pycharm/?from=Synthalingua)

# Changes in the Dev-Testing branch
* Added microphone calibration time. This will allow you to set how long the microphone will calibrate for. This will help with background noise and other issues. You can set it to 0 to skip user input and set it to auto 5 seconds.
* Fixed an issue where the console log did not show the translated text on update.
* If the updater fails to update, it will now show the error message rather crashing.


### Downloads
| Version (Click to DL) | Portable Included | Type | Notes |
| ------- |-------------------| ---- | ----- |
| [1.0.9986](https://github.com/cyberofficial/Synthalingua/releases/tag/1.0.9986) | Yes               | Stable | various updates and bug fixes, added noise gate supression argument. `--mic_calibration_time` check arguments below. |

### Badges
[![CodeQL](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml/badge.svg)](https://github.com/cyberofficial/Synthalingua/actions/workflows/codeql.yml)

#### Readme will update as time goes. This is a work in progress.

### Table of Contents
| Table of Contents | Description |
| ----------------- | ----------- |
| [Disclaimer](#things-to-knowdisclaimerswarningsetc) | Things to know/Disclaimers/Warnings/etc |
| [To Do List](#todo) | Things to do |
| [Contributors](#contributors) | People who helped with the project or contributed to the project. |
| [Installing/Setup](#installation) | How to install and setup the tool. |
| Misc | [Usage and File Arguments](#usage) - [Examples](#examples) - [Web Server](#web-server) |
| [Troubleshooting](#troubleshooting) | Common issues and how to fix them. |
| [Additional Info](#additional-information) | Additional information about the tool. |
| [Video Demos](#video-demonstration) | Video demonstrations of the tool. |
| [Extra Notes](#things-to-note) | Extra notes about the tool. |

## Things to know/Disclaimers/Warnings/etc
- This tool is not perfect. It's still in beta and is a work in progress. It will be updated in a reasonable amount of time.
Example: The tool might occasionally provide inaccurate translations or encounter bugs that are being actively worked on by the developers.
- Translations are more accurate when the speaker speaks clearly and slowly. If the speaker is fast or unclear, the translation will be less accurate, though it will still provide some level of translation.
Example: If the speaker speaks slowly and enunciates clearly, the tool is likely to provide more accurate translations compared to when the speaker speaks quickly or mumbles.
- The tool is not intended for professional use. It's meant for fun, language learning, and enjoying content at a reasonable pace. You may need to try to understand the content on your own before using this tool.
Example: This tool can be used for casual conversations, language practice with friends, or enjoying audio content in different languages.
- You agree not to use the tool to produce or spread misinformation or hate speech. If there is a discrepancy between the tool's output and the speaker's words, you must conduct your own research to determine the truth.
Example: If the tool translates a statement into something false or misleading, it is your responsibility to verify the accuracy of the information before sharing it. Avoid using the tool to spread false information or engage in hate speech.
- You assume your own risk and liability. The repository owner will not be held responsible for any damages caused by the tool. You are responsible for your own actions and cannot hold the repository owner accountable if you encounter issues or face consequences due to your usage of the tool.
Example: If the tool encounters technical issues, fails to provide accurate translations, or if you face any negative consequences resulting from its usage, the repository owner cannot be held liable.
- The tool is not meant to replace human translators. It is designed for fun, language learning, and enjoying content at a reasonable pace. You may need to make an effort to understand the content on your own before using this tool.
Example: When dealing with complex or highly specialized content, it is advisable to consult professional human translators for accurate translations.
- Your hardware can affect the tool's performance. A weak CPU or GPU may hinder its functionality. However, a weak internet connection or microphone will not significantly impact the tool.
Example: If you have a powerful computer with a fast processor, the tool is likely to perform better and provide translations more efficiently compared to using it on a slower or older system.
- This is a tool, not a service. You are responsible for your own actions and cannot hold the repository owner accountable if the tool violates terms of service or end-user license agreements, or if you encounter any issues while using the tool.
Example: If you use the tool in a way that violates the terms of service or policies of the platform you're using it with, the repository owner cannot be held responsible for any resulting consequences.


## TODO
| Todo  | Sub-Task | Status |
|-------|----------|--------|
| Add support for AMD GPUs. | ROCm support - Linux Only | ✅ |
|       | OpenCL support - Linux Only | ✅ |
| Add support API access. |          | ❌ |
| Custom localhost web server. |      | ✅ |
| Add reverse translation. |        | ✅ |
|       | Localize script to other languages. (Will take place after reverse translations.) | ❌ |
| Custom dictionary support. |       | ❌ |
| GUI.  |          | ❌ |
| Linux support. |          | ✅ |
| Improve performance. |         | ❌ |
|       | Compressed Model Format for lower ram users | ✅ |
|       | Better large model loading speed | ❌ |
|          | Split model up into multiple chunks based on usage | ❌ |
| Increase model swapping accuracy. | | ❌ |


# Contributors 
#### [@DaniruKun](https://github.com/DaniruKun) - https://watsonindustries.live
#### [@Expletive](https://github.com/Expletive) - https://evitelpxe.neocities.org 
#### [@Adenser](https://github.com/Adenser)

# System Requirements
| Supported GPUs | Description |
| -------------- | ----------- |
| Nvidia Dedicated Graphics | Supported |
| Nvidia Integrated Graphics | Tested - Not Supported |
| AMD/ATI | * Linux Verified |
| Intel Arc | Not Supported |
| Intel HD | Not Supported |
| Intel iGPU | Not Supported |

You can find full list of supported Nvida GPUs here:
* [Official Nvidia List](https://developer.nvidia.com/cuda-gpus)
* [Simple List](https://gist.github.com/standaloneSA/99788f30466516dbcc00338b36ad5acf)

| Requirement | Minimum | Moderate | Recommended | Best Performance |
| ----------- | ------- | -------- | ----------- | ---------------- |
| CPU Cores | 2 | 6 | 8 | 16 |
| CPU Clock Speed (GHz) | 2.5 or higher | 3.0 or higher | 3.5 or higher | 4.0 or higher |
| RAM (GB) | 4 or higher | 8 or higher | 16 or higher | 16 or higher |
| GPU VRAM (GB) | 2 or higher | 6 or higher | 8 or higher | 12 or higher |
| Free Disk Space (GB) | 10 or higher | 10 or higher | 10 or higher | 10 or higher |
| GPU (suggested) As long as the gpu you have is within vram spec, it should work fine. | Nvidia GTX 1050 or higher | Nvidia GTX 1660 or higher | Nvidia RTX 3070 or higher | Nvidia RTX 3090 or higher |

Note:
- Nvidia GPU support on Linux and Windows
- Nvidia GPU is suggested but not required.
- AMD GPUs are supported on linux, not Windows, but will *try* to be supported soon.

The tool will work on any system that meets the minimum requirements. The tool will work better on systems that meet the recommended requirements. The tool will work best on systems that meet the best performance requirements. You can mix and match the requirements to get the best performance. For example, you can have a CPU that meets the best performance requirements and a GPU that meets the moderate requirements. The tool will work best on systems that meet the best performance requirements.

## Installation
1. Download and install [Python 3.10.9](https://www.python.org/downloads/release/python-3109/).
     * Make sure to check the box that says "Add Python to PATH" when installing. If you don't check the box, you will have to manually add Python to your PATH. You can check this guide: [How to add Python to PATH](https://datatofish.com/add-python-to-windows-path/).
     * You can choose any python version that is 3.10.9 up to the latest version. The tool will *not* work on any python version that is 3.11 or higher. Must be 3.10.9+ not 3.11.x.
2. Download and install [Git](https://git-scm.com/downloads).
     * Using default settings is fine.
3. Download and install FFMPEG
     * Instructions: https://github.com/cyberofficial/Synthalingua/issues/2#issuecomment-1491098222
4. Download and install CUDA [Optional, but needs to be installed if using GPU]
     * https://developer.nvidia.com/cuda-downloads
5. Run setup script
     * **On Windows**: `setup.bat`
     * **On Linux**: `setup.bash`
     * If you get an error saying "Setup.bat is not recognized as an internal or external command, operable program or batch file.", houston we have a problem. This will require you to fix your operating system.
6. Run the newly created batch file/bash script. You can edit that file to change the settings.
     * If you get an error saying it is "not recognized as an internal or external command, operable program or batch file.", make sure you have  installed and added to your PATH, and make sure you have git installed. If you have python and git installed and added to your PATH, then create a new issue on the repo and I will try to help you fix the issue.

## Usage 

This script uses argparse to accept command line arguments. The following options are available:
| Flag | Description |
| ---- | ----------- |
| `--ram` | Change the amount of RAM to use. Default is 4GB. Choices are "1GB", "2GB", "4GB", "6GB", "12GB". |
| `--ramforce` | Use this flag to force the script to use desired VRAM. May cause the script to crash if there is not enough VRAM available. |
| `--non_english` | Use non-English models for transcription. Enables the use of non-English models. |
| `--energy_threshold` | Set the energy level for microphone to detect. Default is 100. Choose from 1 to 1000; anything higher will be harder to trigger the audio detection. |
| `--mic_calibration_time` | How long to calibrate the mic for in seconds. To skip user input type 0 and time will be set to 5 seconds. |
| `--record_timeout` | Set the time in seconds for real-time recording. Default is 2 seconds. |
| `--phrase_timeout` | Set the time in seconds for empty space between recordings before considering it a new line in the transcription. Default is 1 second. |
| `--translate` | Translate the transcriptions to English. Enables translation. |
| `--transcribe` | Transcribe the audio to a set target language. Target Language flag is required. |
| `--target_language` | Select the language to translate to. Available choices are a list of languages in ISO 639-1 format, as well as their English names. |
| `--language` | Select the language to translate from. Available choices are a list of languages in ISO 639-1 format, as well as their English names. |
| `--auto_model_swap` | Automatically swap the model based on the detected language. Enables automatic model swapping. |
| `--device` | Select the device to use for the model. Default is "cuda" if available. Available options are "cpu" and "cuda". When setting to CPU you can choose any RAM size as long as you have enough RAM. The CPU option is optimized for multi-threading, so if you have like 16 cores, 32 threads, you can see good results. |
| `--cuda_device` | Select the CUDA device to use for the model. Default is 0. |
| `--discord_webhook` | Set the Discord webhook to send the transcription to. |
| `--list_microphones` | List available microphones and exit. |
| `--set_microphone` | Set the default microphone to use. You can set the name or its ID number from the list. |
| `--auto_language_lock` | Automatically lock the language based on the detected language after 5 detections. Enables automatic language locking. Will help reduce latency. Use this flag if you are using non-English and if you do not know the current spoken language. |
| `--use_finetune` | Use fine-tuned model. This will increase accuracy, but will also increase latency. Additional VRAM/RAM usage is required. |
| `--no_log` | Makes it so only the last thing translated/transcribed is shown rather log style list. |
| `--updatebranch` | Check which branch from the repo to check for updates. Default is **master**, choices are **master** and **dev-testing** and **bleeding-under-work**. To turn off update checks use **disable**. **bleeding-under-work** is basically latest changes and can break at any time. |
| `--keep_temp` | Keeps audio files in the **out** folder. This will take up space over time though. |
| `--portnumber` | Set the port number for the web server. If no number is set then the web server will not start. |
| `--retry` | Retries translations and transcription if they fail. |
| `--about` | Shows about the app. |

# Things to note!
- When crafting your command line arguments, you need to make sure you adjust the energy threshold to your liking. The default is 100, but you can adjust it to your liking. The higher the number, the harder it is to trigger the audio detection. The lower the number, the easier it is to trigger the audio detection. I recommend you start with 100 and adjust it from there. I seen best results with 250-500.
- When using the discord webhook make sure the url is in quotes. Example: `--discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890"`
- An active internet connection is required for initial usage. Over time you'll no longer need an internet connection. Changing RAM size will download certain models, once downloaded you'll no longer need internet.
- The fine tuned model will automatically be downloaded from OneDrive via Direct Public link. In the event of failure

## Web Server
With the command flag `--port 4000`, you can use query parameters like `?showoriginal`, `?showtranslation`, and `?showtranscription` to show specific elements. If any other query parameter is used or no query parameters are specified, all elements will be shown by default. You can choose another number other than `4000` if you want. You can mix the query parameters to show specific elements, leave blank to show all elements.

For example:
- `http://localhost:4000?showoriginal` will show the `original` detected text.
- `http://localhost:4000?showtranslation` will show the `translated` text.
- `http://localhost:4000?showtranscription` will show the `transcribed` text.
- `http://localhost:4000/?showoriginal&showtranscription` will show the `original` and `transcribed` text.
- `http://localhost:4000` or `http://localhost:4000?otherparam=value` will show all elements by default.

## Examples
#### Please note, make sure you edit the livetranslation.bat/livetranslation.bash file to change the settings. If you do not, it will use the default settings.


You have a GPU with 6GB of memory and you want to use the Japanese model. You also want to translate the transcription to English. You also want to send the transcription to a Discord channel. You also want to set the energy threshold to 300. You can run the following command:
`python transcribe_audio.py --ram 6gb --non_english --translate --language ja --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890" --energy_threshold 300`

When choosing ram, you can only choose 1gb, 2gb, 4gb, 6gb, 12gb. There are no in-betweens.

You have a 12gb GPU and you want to translate to Spanish from English, you can run the following command:
`python transcribe_audio.py --ram 12gb --transcribe --target_language Spanish --non_english --language en`

Lets say you have multiple audio devices and you want to use the one that is not the default. You can run the following command:
`python transcribe_audio.py --list_microphones`
This command will list all audio devices and their index. You can then use the index to set the default audio device. For example, if you want to use the second audio device, you can run the following command:
`python transcribe_audio.py --set_microphone "Realtek Audio (2- High Definiti"` to set the device to listen to. *Please note the quotes around the device name. This is required to prevent errors. Some names may be cut off, copy exactly what is in the quotes of the listed devices.

Example lets say I have these devices:
```
Microphone with name "Microsoft Sound Mapper - Input" found, the device index is 1
Microphone with name "VoiceMeeter VAIO3 Output (VB-Au" found, the device index is 2
Microphone with name "Headset (B01)" found, the device index is 3
Microphone with name "Microphone (Realtek USB2.0 Audi" found, the device index is 4
Microphone with name "Microphone (NVIDIA Broadcast)" found, the device index is 5
```

I would put `python transcribe_audio.py --set_microphone "Microphone (Realtek USB2.0 Audi"` to set the device to listen to.
-or-
I would put `python transcribe_audio.py --set_microphone 4` to set the device to listen to.

## Troubleshooting

If you encounter any issues with the tool, here are some common problems and their solutions:

* Python is not recognized as an internal or external command, operable program or batch file.
    * Make sure you have Python installed and added to your PATH.
    * If you recently installed Python, try restarting your computer to refresh the PATH environment variable.
    * Check that you installed the correct version of Python required by the application. Some applications may require a specific version of Python.
    * If you are still having issues, try running the command prompt as an administrator and running the installation again. However, only do this as a last resort and with caution, as running scripts as an administrator can potentially cause issues with the system.
* I get an error saying "No module named 'transformers'".
    * Re-run the setup.bat file.
        * If issues persist, make sure you have Python installed and added to your PATH.
        * Make sure you have the `transformers` module installed by running `pip install transformers`.
        * If you have multiple versions of Python installed, make sure you are installing the module for the correct version by specifying the Python version when running the command, e.g. `python -m pip install transformers`.
        * If you are still having issues, create a new issue on the repository and the developer may be able to help you fix the issue.
* Git is not recognized as an internal or external command, operable program or batch file.
    * Make sure you have Git installed and added to your PATH.
    * If you recently installed Git, try restarting your computer to refresh the PATH environment variable.
    * If you are still having issues, try running the command prompt as an administrator and running the installation again. However, only do this as a last resort and with caution, as running scripts as an administrator can potentially cause issues with the system.
* CUDA is not recognized or available.
    * Make sure you have CUDA installed. You can get it from [here](https://developer.nvidia.com/cuda-downloads).
    * CUDA is only for NVIDIA GPUs. If you have an AMD GPU, you have to use the CPU model. ROCm is not supported at this time.
* [WinError 2] The system cannot find the file specified
    Try this fix: https://github.com/cyberofficial/Real-Time-Translation/issues/2#issuecomment-1491098222
* Translator can't pickup stream sound
    * Check out this discussion thread for a possible fix: [#12 Discussion](https://github.com/cyberofficial/Synthalingua/discussions/12)

# Additional Information
* Models used are from OpenAI Whisper - [Whisper](https://github.com/openai/whisper)
    * Models were fine tuned using this [Documentation](https://huggingface.co/blog/fine-tune-whisper#load-whisperfeatureextractor)

# Video Demonstration
Command line arguments used. `--ram 6gb --record_timeout 2 --language ja --energy_threshold 500`
[<img src="https://i.imgur.com/sXTWr76.jpg" width="50%">](https://streamable.com/m9mhfr)

Command line arguments used. `--ram 12gb --record_timeout 5 --language id --energy_threshold 500`
[<img src="https://i.imgur.com/2WbWpH4.jpg" width="50%">](https://streamable.com/skuhoh)
