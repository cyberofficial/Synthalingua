## Real-Time-Translation
Real Time Translation is a tool that translates audio from one language to English. It's a self hosted tool that can be used to translate audio from any language to English. It uses uses the power of A.I. to handle the input transcription and translation. Even though it's really powerful, it's still in beta and is not perfect. It's still a work in progress and will be updated in a reasonable amount of time.

#### Readme will update as time goes. This is a work in progress.

## Things to know/Disclaimers/Warnings/etc
- This tool is not perfect. It's still in beta and is not perfect. It's still a work in progress and will be updated in a reasonable amount of time.
- The tool will prioritize the language you select over the language it detects. For example if you select Japanese and the speaker is speaking in Spanish it will try and translate it to Japanese. If you want it to translate it to Spanish, you can select Spanish as the language or set the language to auto detect.
- Translations will be more accurate if the speaker is speaking clearly and slowly. If the speaker is speaking fast or unclear, the translation will be less accurate. Though it will still be able to translate it to some degree.
- The tool is not to be used in a professional setting. It's not perfect and is not meant to be used in a professional setting. It's meant to be used for fun and to learn languages and enjoy content at a reasonable pace. You may be required to try and understand the content on your own before using this tool.
- You agree to not use the tool to produce misinformation; Example: If the tool says one thing and the speaker says another, you must do your own research to find out what is true. You may not use the tool to spread misinformation at all.
- You agree to not use the tool to produce hate speech; Example: If the tool says one thing and the speaker says another, you must do your own research to find out what is true. You may not use the tool to spread hate speech at all.
- Since this tool allows connecting to Discord, you must also adhere to Discord's Terms of Service. You may not use the tool to break Discord's Terms of Service or bypass any restrictions Discord has in place, if you use the Discord feature.
- You run your own risk and liability, I (the repo owner), will not be held liable for any damages caused by the tool. You are responsible for your own actions and can not blame me if the tool breaks tos or eulas, or if you get banned from Discord or any other service you use the tool with.
- The tool's model was tuned for conversational speech. It may not work well with other types of speech. For example, it may not work well with news broadcasts, or with a speaker that is speaking in traditional speech. It will work best with conversational speech and prioritizes names over alternate terms of names. For example in Japanese; "Okayu" will always be "Okayu" and not porridge. The A.I. will only translate "porridge" if it's in the context of a sentence is detected with enough confidence. A name will always be translated to the name even though it may have a different spelling in the target language. For example, "Okayu" will always be "Okayu" and not "Okaru" or "Okaru" will always be "Okaru" and not "Okayu" given enough context. The A.I. will only translate "Okayu" if it's in the context of a sentence is detected with enough confidence.
- The tool is not meant to replace actual translators. It's meant to be used for fun and to learn languages and enjoy content at a reasonable pace. You may be required to try and understand the content on your own before using this tool.
- Your hardware will affect the outcome of the tool. If you have a weak CPU, the tool will not work as well. If you have a weak GPU, the tool will not work as well. *If you have a weak internet connection, the tool will not be affected. If you have a weak microphone or bad audio input, the tool will not work as well. 
- This is a tool not a service. You are responsible for your own actions and can not blame me if the tool breaks tos or eulas, or if you get banned from Discord or any other service you use the tool with.

# Todo
- [ ] Add support for AMD GPUs.
    - [ ] ROCm support
    - [ ] OpenCL support
- [ ] Add support API access.
- [ ] Custom localhost web server.
- [ ] Add reverse translation.
- [ ] Custom dictionary support.
- [ ] GUI.
- [ ] Linux support.
- [ ] Improve performance.
- [ ] Increase model swapping accuracy.

# System Requirements
## Nvidia GPU is required*, Support for AMD GPUs is coming soon. Windows is required. Linux support is coming soon.
#### *GPU is not fully required, but can improve performance. AMD GPUs are not supported yet, but will be supported soon.
### Minimum Requirements
- CPU with 2 cores running at 2.5 GHz or higher
- *GPU with 2 GB of VRAM or higher
- 4 GB of RAM or higher
- 10 GB of free disk space
* GPU is not required, but can improve performance.

### Moderate Requirements
- CPU with 6 cores running at 3.0 GHz or higher
- *GPU with 6 GB of VRAM or higher
- 8 GB of RAM or higher
- 10 GB of free disk space
* GPU is not required, but can improve performance.

### Recommended Requirements
- CPU with 8 cores running at 3.5 GHz or higher
- *GPU with 8 GB of VRAM or higher
- 16 GB of RAM or higher
- 10 GB of free disk space
* GPU is not required, but can improve performance.

### Best Performance
- CPU with 16 cores running at 4.0 GHz or higher
- *GPU with 12 GB of VRAM or higher
- 16 GB of RAM or higher
- 10 GB of free disk space
* GPU is not required, but can improve performance.

The tool will work on any system that meets the minimum requirements. The tool will work better on systems that meet the recommended requirements. The tool will work best on systems that meet the best performance requirements. You can mix and match the requirements to get the best performance. For example, you can have a CPU that meets the best performance requirements and a GPU that meets the moderate requirements. The tool will work best on systems that meet the best performance requirements.

## Installation
1. Download and install [Python 3.10.9](https://www.python.org/downloads/release/python-3109/).
     * Make sure to check the box that says "Add Python to PATH" when installing. If you don't check the box, you will have to manually add Python to your PATH. You can check this guide: [How to add Python to PATH](https://datatofish.com/add-python-to-windows-path/).
     * You can choose any python version that is 3.10.9 up to the latest version. The tool will work on any python version that is 3.11 or higher. Must be 3.10.9+ not 3.11.x.
2. Download and install [Git](https://git-scm.com/downloads).
     * Using default settings is fine.
3. Run Setup.bat
     * If you get an error saying "Setup.bat is not recognized as an internal or external command, operable program or batch file.", houston we have a problem. This will require you to fix your operating system.
4. Run the newly created batch file. You can edit that file to change the settings.
     * If you get an error saying it is "not recognized as an internal or external command, operable program or batch file.", make sure you have python installed and added to your PATH, and make sure you have git installed. If you have python and git installed and added to your PATH, then create a new issue on the repo and I will try to help you fix the issue.

## Usage 

This script uses argparse to accept command line arguments. The following options are available:

* `--ram`: Change the amount of RAM to use. Default is 4gb. Choices are "1gb", "2gb", "4gb", "6gb", "12gb"
* `--non_english`: Use non-English models for transcription. This flag enables the use of non-English models.
* `--energy_threshold`: Set the energy level for microphone to detect. Default is 100, you can choose from 1 to 1000, anything higher will be harder to trigger the audio detection.
* `--record_timeout`: Set the time in seconds for real-time recording. Default is 2 seconds.
* `--phrase_timeout`: Set the time in seconds for empty space between recordings before considering it a new line in the transcription. Default is 1 second.
* `--translate`: Translate the transcriptions to English. This flag enables translation.
* `--language`: Select the language to translate from. Available choices are a list of languages in ISO 639-1 format, as well as their English names.
* `--auto_model_swap`: Automatically swap the model based on the detected language. This flag enables automatic model swapping.
* `--device`: Select the device to use for the model. Default is "cuda" if available. Available options are "cpu" and "cuda".
* `--cuda_device`: Select the CUDA device to use for the model. Default is 0.
* `--discord_webhook`: Set the Discord webhook to send the transcription to.
* `--list_microphones`: List available microphones and exit.
* `--set_microphone`: Set the default microphone to use.
* `--auto_language_lock`: Automatically lock the language based on the detected language after 5 detections. This flag enables automatic language locking. Will help reduce latency. Use this flag if you are using non-English and if you do not know the current spoken language.
* `--retry`: Retries transations and transcription if they failed.

## Examples
You have a GPU with 6GB of memory and you want to use the Japanese model. You also want to translate the transcription to English. You also want to send the transcription to a Discord channel. You also want to set the energy threshold to 300. You can run the following command:
`python transcribe_audio.py --ram 6gb --non_english --translate --language ja --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890" --energy_threshold 300`

When choosing ram, you can only choose 1gb, 2gb, 4gb, 6gb, 12gb. There is no betweens.

Lets say you have multiple audio devices and you want to use the one that is not the default. You can run the following command:
`python transcribe_audio.py --list_microphones`
This command will list all audio devices and their index. You can then use the index to set the default audio device. For example, if you want to use the second audio device, you can run the following command:
`python transcribe_audio.py --set_microphone "Realtek Audio (2- High Definiti"` to set the device to listen to. *Please note the quotes around the device name. This is required to prevent errors. Some names may be cut off, copy exactly what is in the quotes of the listed devices.

Example lets say i have these devices:
```
Microphone with name "Microsoft Sound Mapper - Input" found
Microphone with name "VoiceMeeter VAIO3 Output (VB-Au" found
Microphone with name "Headset (B01)" found
Microphone with name "Microphone (Realtek USB2.0 Audi" found
Microphone with name "Microphone (NVIDIA Broadcast)" found
```

I would put `python transcribe_audio.py --set_microphone "Microphone (Realtek USB2.0 Audi"` to set the device to listen to.

## Troubleshooting
* Python is not recognized as an internal or external command, operable program or batch file.
    * Make sure you have python installed and added to your PATH.
* Git is not recognized as an internal or external command, operable program or batch file.
    * Make sure you have git installed and added to your PATH.
* CUDA is not recognized or available.
    * Make sure you have CUDA installed. You can get it from [here](https://developer.nvidia.com/cuda-downloads).
    * CUDA is only for NVIDIA GPUs. If you have an AMD GPU, you have to use the CPU model. ROCm is not supported at this time.
* I get an error saying "No module named 'transformers'".
    * Re-run the setup.bat file.
        * If issues persist, make sure you have python installed and added to your PATH.
            * If you have python installed and added to your PATH, create a new issue on the repo and I will try to help you fix the issue.

# Additional Information
* Models used are from OpenAI Whisper - [Whisper](https://github.com/openai/whisper)
    * Models were fine tuned using this [Documentation](https://huggingface.co/blog/fine-tune-whisper#load-whisperfeatureextractor)

# Video Demonstration
Command line arguments used. `--ram 6gb --record_timeout 2 --language ja --energy_threshold 500`
[<img src="https://i.imgur.com/sXTWr76.jpg" width="50%">](https://streamable.com/m9mhfr)

Command line arguments used. `--ram 12gb --record_timeout 5 --language id --energy_threshold 500`
[<img src="https://i.imgur.com/2WbWpH4.jpg" width="50%">](https://streamable.com/skuhoh)

# Things to note!
- When crafting your command line arguments, you need to make sure you adjust the energy threshold to your liking. The default is 100, but you can adjust it to your liking. The higher the number, the harder it is to trigger the audio detection. The lower the number, the easier it is to trigger the audio detection. I recommend you start with 100 and adjust it from there. I seen best results with 250-500.
- When using the discord webhook make sure the url is in quotes. Example: `--discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890"`
- An active internet connection is required for initial usage. Over time you'll no longer need an internet connection. Changing RAM size will download certain models, once downloaded you'll no longer need internet.
- The fine tuned model will automatically be downloaded from OneDrive via Direct Public link. In the event if failure
