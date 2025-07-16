import argparse
import sys
import os
from colorama import Fore, Back, Style
from modules.languages import get_valid_languages

# Define a constant variable for valid language choices
VALID_LANGUAGES = get_valid_languages()

def valid_port_number(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError(f"Invalid port number: {value}. Please choose a number between 1 and 65535.")
    return port

def get_cpu_count():
    """Get the number of CPU cores available on the system."""
    try:
        return os.cpu_count() or 1
    except:
        return 1

def valid_demucs_jobs(value):
    """Validate demucs jobs parameter for --isolate_vocals argument."""
    if value is None:
        return 0  # Default: no parallel jobs
    
    if isinstance(value, bool):
        return 0  # For backwards compatibility with store_true
    
    if value.lower() == 'all':
        return get_cpu_count()
    
    try:
        jobs = int(value)
        max_cores = get_cpu_count()
        
        if jobs < 0:
            raise argparse.ArgumentTypeError(f"Number of jobs cannot be negative. Got: {jobs}")
        elif jobs == 0:
            return 0  # Valid: use default (single-threaded)
        elif jobs > max_cores:
            raise argparse.ArgumentTypeError(f"Number of jobs ({jobs}) exceeds available CPU cores ({max_cores}). Maximum allowed: {max_cores}")
        else:
            return jobs
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid jobs value: '{value}'. Use 'all', a number (1-{get_cpu_count()}), or leave empty for default.")

def set_model_by_ram(ram, language):
    ram = ram.lower()
    language = language.lower() if language else ""
    is_english = language in ("en", "english")
    
    if ram == "1gb":
        if is_english:
            model_en = "tiny.en"
            model_multi = "tiny"
            print(f"{Fore.YELLOW}Note{Style.RESET_ALL}: For English, you can choose between English-specific model (tiny.en) or multilingual model (tiny).")
            if input("Use English-specific model? (y/n): ").lower() == "y":
                model = model_en
            else:
                model = model_multi
        else:
            model = "tiny"
    elif ram == "2gb":
        if is_english:
            model_en = "base.en"
            model_multi = "base"
            print(f"{Fore.YELLOW}Note{Style.RESET_ALL}: For English, you can choose between English-specific model (base.en) or multilingual model (base).")
            if input("Use English-specific model? (y/n): ").lower() == "y":
                model = model_en
            else:
                model = model_multi
        else:
            model = "base"
    elif ram == "3gb":
        if is_english:
            model_en = "small.en"
            model_multi = "small"
            print(f"{Fore.YELLOW}Note{Style.RESET_ALL}: For English, you can choose between English-specific model (small.en) or multilingual model (small).")
            if input("Use English-specific model? (y/n): ").lower() == "y":
                model = model_en
            else:
                model = model_multi
        else:
            model = "small"
    elif ram == "6gb":
        if is_english:
            model_en = "medium.en"
            model_multi = "medium"
            print(f"{Fore.YELLOW}Note{Style.RESET_ALL}: For English, you can choose between English-specific model (medium.en) or multilingual model (medium).")
            if input("Use English-specific model? (y/n): ").lower() == "y":
                model = model_en
            else:
                model = model_multi
        else:
            model = "medium"
    elif ram == "7gb":
        model = "turbo"
        if is_english:
            print(f"{Fore.YELLOW}Note{Style.RESET_ALL}: The turbo model is multilingual and works for all languages.")
    elif ram in ("11gb-v2", "11gb-v3"):
        if ram == "11gb-v2":
            model = "large-v2"
            version = "Version 2"
        else:
            model = "large-v3"
            version = "Version 3"
        if is_english:
            red_text = Fore.RED + Back.BLACK
            green_text = Fore.GREEN + Back.BLACK
            yellow_text = Fore.YELLOW + Back.BLACK
            reset_text = Style.RESET_ALL
            print(f"{red_text}WARNING{reset_text}: {yellow_text}11gb{reset_text} is overkill for English. "
                  f"Do you want to swap to the {green_text}7gb{reset_text} turbo model? "
                  f"If you are transcribing a language other than English, you can ignore this warning and press {green_text}n{reset_text}.")
            if input("y/n: ").lower() == "y":
                model = "turbo"
            else:
                print(f"Using 11GB {version}")
    else:
        raise ValueError("Invalid RAM setting provided")
    return model


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ram", default="2gb", help="Model to use", choices=["1gb", "2gb", "3gb", "6gb", "7gb", "11gb-v2", "11gb-v3"])
    parser.add_argument("--word_timestamps", action='store_true', default=False, help="Enable word-level timestamps in output (default: False)")
    parser.add_argument("--isolate_vocals", nargs='?', const='0', default=False, type=valid_demucs_jobs, help="Attempt to isolate vocals from the input audio before generating subtitles. Optionally specify number of parallel jobs: 'all' for all CPU cores, a number for specific core count, or leave empty for default single-threaded processing. Use --demucs_model to specify which model to use.")
    parser.add_argument("--demucs_model", default="htdemucs", help="Demucs model to use for vocal isolation. Only used when --isolate_vocals is enabled.", choices=["htdemucs", "htdemucs_ft", "htdemucs_6s", "hdemucs_mmi", "mdx", "mdx_extra", "mdx_q", "mdx_extra_q", "hdemucs", "demucs"])
    parser.add_argument("--ramforce", action='store_true', help="Force the model to use the RAM setting provided. Warning: This may cause the model to crash.")
    parser.add_argument("--fp16", action='store_true', default=False, help="Sets Models to FP16 Mode, increases speed with a light decrease in accuracy.")
    parser.add_argument("--energy_threshold", default=100, help="Energy level for mic to detect.", type=int)
    parser.add_argument("--mic_calibration_time", help="How long to calibrate the mic for in seconds. To skip user input type 0 and time will be set to 5 seconds.", type=int)
    parser.add_argument("--record_timeout", default=1, help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=5, help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    parser.add_argument("--no_log", action='store_true', help="Only show the last line of the transcription.")
    parser.add_argument("--debug", action='store_true', help="Debug things")
    parser.add_argument("--translate", action='store_true', help="Translate the transcriptions to English.")
    parser.add_argument("--transcribe", action='store_true', help="transcribe the text into the desired language.")
    parser.add_argument("--language", help="Language to translate from.", type=str, choices=VALID_LANGUAGES)
    parser.add_argument("--target_language", help="Language to translate to.", type=str, choices=VALID_LANGUAGES)
    parser.add_argument("--device", default="cuda", help="Device to use for model. If not specified, will use CUDA if available. Available options: cpu, cuda")
    parser.add_argument("--cuda_device", default=0, help="CUDA device to use for model. If not specified, will use CUDA device 0.", type=int)
    parser.add_argument("--discord_webhook", default=None, help="Discord webhook to send transcription to.", type=str)
    parser.add_argument("--list_microphones", action='store_true', help="List available microphones and exit.")
    parser.add_argument("--set_microphone", default=None, help="Set default microphone to use.", type=str)
    parser.add_argument("--microphone_enabled", default=None, help="Enable microphone by name.", type=str)
    parser.add_argument("--mic_chunk_size", default=1, help="Number of audio chunks to collect before processing when using microphone with --paddedaudio. Default is 1 (process each chunk immediately).", type=int)
    parser.add_argument("--model_dir", default="models", help="Location where to store downloaded models.")
    parser.add_argument("--retry", action='store_true', help="Retries the transcription if it fails. May increase output time.")
    parser.add_argument("--updatebranch", default="master", help="Check which branch from the repo to check for updates. Default is master, choices are master and dev-testing and bleeding-under-work. To turn off update checks use disable. bleeding-under-work is basically latest changes and can break at any time.", choices=["master", "dev-testing", "disable", "bleeding-under-work"])
    parser.add_argument("--keep_temp", action='store_true', help="Keep temporary audio files.")
    parser.add_argument("--portnumber", default=None, help="Port number to run the web server on. If not specified, the web server will not run.", type=valid_port_number)
    parser.add_argument("--about", action='store_true', help="About the project.")
    parser.add_argument("--save_transcript", action='store_true', help="Save the transcript to a file.")
    parser.add_argument("--save_folder", default="out", help="Folder to save the transcript to.")
    parser.add_argument("--stream", default=None, help="Stream mode. Specify the url to the stream. Example: https://twitch.tv/laplusdarknesss_hololive")
    parser.add_argument("--stream_original_text", action='store_true', help="Show's the detected language of the stream.")
    parser.add_argument("--stream_chunks", default=5, help="How many chunks to split the stream into. Default is 5 is recommended to be between 3 and 5. YouTube streams should be 1 or 2, twitch should be 5 to 10.", type=int)
    parser.add_argument("--paddedaudio", default=0, help="Number of chunks to overlap from previous batch for better transcription context. Works with both streaming (--stream) and microphone (--microphone_enabled) input. For streams with --stream_chunks 4 --paddedaudio 1, each batch will contain 1 chunk from the previous batch plus 4 new chunks (5 total). For microphone input, use with --mic_chunk_size to define batch size.", type=int)
    parser.add_argument("--stream_language", default=None, help="Language of the stream. Default is English.", type=str, choices=VALID_LANGUAGES)
    parser.add_argument("--stream_target_language", default=None, help="[DEPRECATED - WILL BE REMOVED SOON] Language to translate the stream to. Use --stream_transcribe <language> instead.", type=str, choices=VALID_LANGUAGES)
    parser.add_argument("--stream_translate", action='store_true', help="Translate the stream.")
    parser.add_argument("--stream_transcribe", nargs='?', const=True, default=False, help="Transcribe the stream to the specified language (e.g., --stream_transcribe English). If no language is provided, will just enable transcription.", type=str)
    parser.add_argument("--cookies", default=None, help="Path to cookies file. Can be: absolute path (C:\\path\\to\\cookies.txt), filename in current directory (cookies.txt), or name for cookies folder (youtube = cookies/youtube.txt). NetScape format.")
    parser.add_argument("--cookies-from-browser", default=None, help="Load cookies from browser. Supported browsers: brave, chrome, chromium, edge, firefox, opera, safari, vivaldi, whale. Example: --cookies-from-browser chrome", choices=["brave", "chrome", "chromium", "edge", "firefox", "opera", "safari", "vivaldi", "whale"])
    #parser.add_argument("--is_portable", action='store_true', help="Run the program in portable mode.")
    parser.add_argument("--makecaptions", nargs='?', const=True, default=False, help="Make captions for the stream. Use '--makecaptions compare' to generate captions with all RAM models for comparison (11gb-v3, 11gb-v2, 7gb, 6gb, 3gb, 2gb, 1gb).")
    parser.add_argument("--print_srt_to_console", action='store_true', default=False, help="Print generated SRT subtitles to the console after file creation.")
    parser.add_argument("--silent_detect", action='store_true', help="Skip processing silent audio chunks during caption generation. Only works with --makecaptions, not with HLS streaming or microphone input.")
    parser.add_argument("--silent_threshold", type=float, default=-35.0, help="dB threshold for silence detection (default: -35.0). Lower values (e.g., -45.0) detect quieter speech like whispers. Higher values (e.g., -25.0) only detect louder speech. Only used with --silent_detect.")
    parser.add_argument("--silent_duration", type=float, default=0.5, help="Minimum duration in seconds for a region to be considered silence (default: 0.5). Higher values (e.g., 2.0) treat brief pauses as speech. Lower values (e.g., 0.1) detect shorter silent periods. Only used with --silent_detect.")
    parser.add_argument("--file_input", default=None, help="Path to file to transcribe or translate.")
    parser.add_argument("--file_output", default=None, help="Path to file to save transcript to.")
    parser.add_argument("--file_output_name", default=None, help="Path to file to save transcript to.")
    parser.add_argument("--ignorelist", type=str, help="Path to the blacklist file (must be .txt format).")
    parser.add_argument("--condition_on_previous_text", action='store_true', help="If True, provide the previous output of the model as a prompt for the next window; disabling may make the text inconsistent across windows, but the model becomes less prone to getting stuck in a failure loop")
    parser.add_argument("--remote_hls_password_id", type=str, help="Password ID for the webserver. Usually like 'id', or 'key'.")
    parser.add_argument("--remote_hls_password", type=str, help="Password for the hls webserver.")
    parser.add_argument(
        "--auto_hls",
        action="store_true",
        help="Auto-adjust HLS chunk batching: sample segment duration and prompt for optimal chunk size before starting stream transcription."
    )
    parser.add_argument(
        "--auto_blocklist",
        action='store_true',
        help="Automatically add phrases that are blocked 3 times to the blocklist file. Requires --ignorelist to be set."
    )
    parser.add_argument(
        "--selectsource", 
        nargs='?', 
        const='interactive', 
        default=None,
        help="Show available audio streams and select one. Use without value for interactive mode, or specify format directly (e.g., 'bestaudio', '140', 'worst')"
    )

    args = parser.parse_args()

    # Validate that cookies and cookies-from-browser are not used together
    if args.cookies and args.cookies_from_browser:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} --cookies and --cookies-from-browser cannot be used together.")
        print("Please use either --cookies to specify a cookies file or --cookies-from-browser to extract cookies from a browser.")
        sys.exit(1)

    # Handle isolate_vocals argument - convert to boolean and add jobs attribute
    if args.isolate_vocals is not False:
        args.demucs_jobs = args.isolate_vocals  # Store the job count
        args.isolate_vocals = True  # Convert to boolean for backward compatibility
    else:
        args.demucs_jobs = 0  # Default: no parallel jobs when not enabled
        args.isolate_vocals = False

    # Restrict --word_timestamps to sub_gen usage only
    # If microphone or HLS/stream mode is enabled, warn and exit if --word_timestamps is set
    using_microphone = (
        (hasattr(args, 'microphone_enabled') and args.microphone_enabled) or
        (hasattr(args, 'set_microphone') and args.set_microphone)
    )
    using_hls = (
        (hasattr(args, 'stream') and args.stream) or
        (hasattr(args, 'auto_hls') and args.auto_hls)
    )
    if args.word_timestamps and (using_microphone or using_hls):
        print(f"{Fore.YELLOW}⚠️  The --word_timestamps flag is only supported for subtitle generation (sub_gen). Please remove the redundant command flag as it serves no purpose in microphone or HLS modes.{Style.RESET_ALL}")
        exit(1)

    return args


print(f"{Fore.GREEN}✅ Parser Args Module Loaded{Style.RESET_ALL}")