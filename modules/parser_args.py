import argparse
import sys
import os
import warnings
from colorama import Fore, Back, Style
from modules.languages import get_valid_languages
from modules.version_checker import version

# Suppress the pkg_resources deprecation warning from ctranslate2
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API.*", category=UserWarning)

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

def valid_batchjobsize(value):
    """Validate batch job size parameter for --batchjobsize argument."""
    try:
        size = float(value)
        if size < 0.1 or size > 12.0:
            raise argparse.ArgumentTypeError(f"Batch job size must be between 0.1 and 12.0 GB. Got: {size}")
        return size
    except ValueError:
        raise argparse.ArgumentTypeError(f"Batch job size must be a number between 0.1 and 12.0. Got: {value}")

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

def valid_batchmode(value):
    """Validate batchmode parameter for parallel processing of speech regions."""
    try:
        batch_size = int(value)
        max_cores = get_cpu_count()
        
        if batch_size < 1:
            raise argparse.ArgumentTypeError(f"Batch size must be at least 1. Got: {batch_size}")
        elif batch_size > max_cores:
            raise argparse.ArgumentTypeError(f"Batch size ({batch_size}) exceeds available CPU cores ({max_cores}). Maximum recommended: {max_cores}")
        else:
            return batch_size
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid batch size value: '{value}'. Must be a positive integer (1-{get_cpu_count()}).")

def show_substyle_help():
    """Display comprehensive help information for the --substyle parameter."""
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    print(f"{Fore.CYAN} SUBTITLE STYLING HELP - --substyle Parameter{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}OVERVIEW:{Style.RESET_ALL}")
    print("The --substyle parameter allows you to customize the appearance of burned subtitles")
    print("(when using --subtype burn). You can control font, size, and color using a simple")
    print("comma-separated format.")
    
    print(f"\n{Fore.YELLOW}USAGE FORMAT:{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}--substyle \"font,size,color\"{Style.RESET_ALL}")
    print("  • Parameters can be in any order")
    print("  • Any parameter can be omitted (defaults will be used)")
    print("  • Font files must be placed in the 'fonts/' folder")
    
    print(f"\n{Fore.YELLOW}AVAILABLE FONTS:{Style.RESET_ALL}")
    # Check available fonts in fonts directory
    import os
    from pathlib import Path
    fonts_dir = Path("fonts")
    if fonts_dir.exists():
        font_files = [f for f in os.listdir(fonts_dir) if f.lower().endswith(('.ttf', '.otf', '.woff', '.woff2'))]
        if font_files:
            print("  Available custom fonts:")
            for font in sorted(font_files):
                print(f"    • {Fore.GREEN}{font}{Style.RESET_ALL}")
        else:
            print(f"    {Fore.YELLOW}No custom fonts found in fonts/ directory{Style.RESET_ALL}")
    else:
        print(f"    {Fore.YELLOW}No fonts/ directory found{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}SUPPORTED COLORS:{Style.RESET_ALL}")
    colors = ["white", "black", "red", "green", "blue", "yellow", "cyan", "magenta", "orange"]
    color_display = "  "
    for color in colors:
        color_display += f"{Fore.GREEN}{color}{Style.RESET_ALL}, "
    print(color_display.rstrip(", "))
    
    print(f"\n{Fore.YELLOW}EXAMPLES:{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN} Custom Font with Size and Color:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}python synthalingua --makecaptions --subtype burn --substyle \"FiraSans-Bold.otf,24,yellow\" --file_input video.mp4{Style.RESET_ALL}")
    print(f"    ➤ Uses FiraSans-Bold font, 24pt size, yellow color")
    
    print(f"\n{Fore.CYAN} Size and Color Only (System Default Font):{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}synthalingua --makecaptions --subtype burn --substyle \"20,red\" --file_input video.mp4{Style.RESET_ALL}")
    print(f"    ➤ Uses system default font, 20pt size, red color")
    
    print(f"\n{Fore.CYAN} Font and Size (Default Color):{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}synthalingua --makecaptions --subtype burn --substyle \"FiraSans-UltraLightItalic.otf,18\" --file_input video.mp4{Style.RESET_ALL}")
    print(f"    ➤ Uses italic font, 18pt size, default white color")
    
    print(f"\n{Fore.CYAN} Color Only (Default Font and Size):{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}synthalingua --makecaptions --subtype burn --substyle \"cyan\" --file_input video.mp4{Style.RESET_ALL}")
    print(f"    ➤ Uses system default font and size, cyan color")
    
    print(f"\n{Fore.CYAN} Flexible Parameter Order:{Style.RESET_ALL}")
    print(f"  {Fore.WHITE}synthalingua --makecaptions --subtype burn --substyle \"24,FiraSans-Bold.otf,green\" --file_input video.mp4{Style.RESET_ALL}")
    print(f"    ➤ Same as font,size,color but parameters in different order")
    
    print(f"\n{Fore.YELLOW}NOTES:{Style.RESET_ALL}")
    print(f"  • Font files must be placed in the {Fore.GREEN}fonts/{Style.RESET_ALL} directory")
    print(f"  • Supported font formats: {Fore.GREEN}.ttf, .otf, .woff, .woff2{Style.RESET_ALL}")
    print(f"  • If a font is not found, the system default will be used with a warning")
    print(f"  • Font size is in points (typical range: 12-72)")
    print(f"  • Subtitles include automatic black outline for better readability")
    print(f"  • The {Fore.GREEN}--substyle{Style.RESET_ALL} parameter only works with {Fore.GREEN}--subtype burn{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

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
    # Base parser
    parser = argparse.ArgumentParser()

    # General information and controls
    general = parser.add_argument_group("General")
    general.add_argument("--version", action="version", version=f"Synthalingua v{version}", help="Show the current version of Synthalingua and exit.")
    general.add_argument("--about", action='store_true', help="Display detailed information about Synthalingua including version, capabilities, model information, device compatibility, and credits. Shows current configuration and exits. Useful for troubleshooting and verifying installation.")
    general.add_argument("--checkupdate", action='store_true', help="Check for available updates by comparing local version with the latest GitHub release. Shows current version, remote version, and whether an update is available, then exits. Useful for quickly checking if a newer version is available without running the main application.")
    general.add_argument("--bugreport", action='store_true', help="Generate a comprehensive bug report file with system information, Python environment details, installed packages, and Synthalingua configuration. Creates 'bugreport_info_[timestamp].txt' in the current directory. Useful for troubleshooting issues and providing detailed information when reporting bugs.")
    general.add_argument("--updatebranch", default="master", help="Software update channel to check for new versions. 'master' is stable releases (recommended), 'dev-testing' has latest features with testing, 'bleeding-under-work' has newest changes but may be unstable, 'disable' turns off all update checks. Choose based on your stability vs features preference.", choices=["master", "dev-testing", "disable", "bleeding-under-work"])
    general.add_argument("--no_log", action='store_true', help="Minimize console output to show only the final transcription result. Hides intermediate processing messages, status updates, and verbose logging. Useful for clean output when piping results to other programs or when you only need the final text. Does not affect file output or error messages.")
    general.add_argument("--debug", action='store_true', help="Enable detailed debugging output for troubleshooting. Shows internal processing steps, model loading details, audio chunk information, timing data, and error traces. Use when experiencing issues with transcription accuracy, performance problems, or unexpected behavior. Significantly increases console output volume.")

    # Model, device, and inference settings
    model_grp = parser.add_argument_group("Model & Inference")
    model_grp.add_argument("--model_source", type=str.lower, default="whisper", help="AI model backend to use for transcription. 'whisper' uses OpenAI's original implementation (slowest, most compatible), 'fasterwhisper' uses optimized C++ implementation (fastest, recommended), 'openvino' uses Intel optimization for Intel hardware (good for Intel CPUs/GPUs).", choices=["whisper", "fasterwhisper", "openvino"])
    model_grp.add_argument("--ram", default="2gb", help="Model size based on VRAM/RAM requirements. Larger models are more accurate but slower: 1gb=tiny (fastest, least accurate), 2gb=base (good balance), 3gb=small, 6gb=medium, 7gb=turbo (fast large model), 11gb-v2/v3=large (most accurate, slowest). Choose based on your hardware capabilities.", choices=["1gb", "2gb", "3gb", "6gb", "7gb", "11gb-v2", "11gb-v3"])
    model_grp.add_argument("--ramforce", action='store_true', help="Force the model to use the RAM setting provided. Warning: This may cause the model to crash.")
    model_grp.add_argument("--fp16", action='store_true', default=False, help="Sets Models to FP16 Mode, increases speed with a light decrease in accuracy.")
    model_grp.add_argument("--compute_type", default="default", help="Quantization of model while loading", choices=["default", "int8", "int8_float32", "int8_float16", "int8_float16", "int8_bfloat16", "int16", "float16", "bfloat16", "float32"])
    model_grp.add_argument("--device", default="cuda", help="Processing device for AI model inference. 'auto' automatically selects best available device, 'cuda' uses NVIDIA GPU (fastest), 'cpu' uses processor (universally compatible), 'intel-igpu' uses Intel integrated graphics, 'intel-dgpu' uses Intel discrete GPU, 'intel-npu' uses Intel Neural Processing Unit. GPU acceleration significantly improves processing speed. Falls back to CPU if specified device unavailable.")
    model_grp.add_argument("--cuda_device", default=0, help="Specific NVIDIA GPU device ID when multiple GPUs are available. Use 0 for first GPU, 1 for second GPU, etc. Check available GPUs with 'nvidia-smi' command. Only relevant when --device is set to 'cuda'. Single GPU systems should use default value 0.", type=int)
    model_grp.add_argument("--model_dir", default="models", help="Directory path where AI models are stored and downloaded. Models can be several GB in size, so ensure adequate disk space. Use absolute path for custom locations (e.g., 'D:/AI_Models') or relative path from script location. Models are automatically downloaded on first use and cached for subsequent runs.")
    model_grp.add_argument("--intelligent_mode", action='store_true', help="If enabled, the system will automatically determine if the current output is below accuracy threshold and switch to a larger model for improved transcription quality.")
    model_grp.add_argument("--condition_on_previous_text", action='store_true', help="Use previous transcription output as context for next audio window to improve consistency and flow. Enabled: better coherence but may get stuck repeating errors. Disabled: each segment processed independently, more resilient to errors but may have inconsistent terminology. Recommended for longer conversations or presentations.")

    # Language and translation
    lang_grp = parser.add_argument_group("Language & Translation")
    lang_grp.add_argument("--language", help="Source language of the audio content for improved transcription accuracy. Use language codes like 'en' (English), 'es' (Spanish), 'fr' (French), 'de' (German), 'ja' (Japanese), etc. When specified, Whisper skips language detection and uses this language directly, improving speed and accuracy for known content.", type=str, choices=VALID_LANGUAGES)
    lang_grp.add_argument("--target_language", help="Target language for translation output when using --translate mode. Specify the language code you want the transcribed text translated into. Examples: 'en' for English, 'es' for Spanish, 'fr' for French. Must be used in combination with --translate flag. Quality varies by language pair.", type=str, choices=VALID_LANGUAGES)
    lang_grp.add_argument("--translate", action='store_true', help="Automatically translate transcribed text to English using built-in translation capabilities. Works with both live microphone input and file processing. Translation occurs after transcription, so you'll see both original and translated text. Quality depends on source language - works best with major world languages.")
    lang_grp.add_argument("--transcribe", action='store_true', help="Force transcription mode instead of real-time processing. Useful for ensuring complete processing of audio files rather than streaming analysis. Automatically enabled for file inputs, but can be explicitly set for microphone input to use batch processing instead of continuous streaming.")

    # Microphone (live input)
    mic_grp = parser.add_argument_group("Microphone (Live Input)")
    mic_grp.add_argument("--list_microphones", action='store_true', help="Display all available audio input devices (microphones) on your system and exit. Shows device names, IDs, sample rates, and channel information in a detailed table. Use the Device ID number (not the name) to select a microphone with --set_microphone. Lower Device IDs typically have faster response times and lower latency. Helpful for troubleshooting audio input issues and identifying optimal microphone settings.")
    mic_grp.add_argument("--set_microphone", default=None, help="Set the default microphone device by exact name (case-sensitive). Use --list_microphones first to see available device names. Example: 'Microphone (USB Audio Device)'. This becomes the primary audio input source. Useful when you have multiple microphones and want to specify which one to use.", type=str)
    mic_grp.add_argument("--microphone_enabled", default=None, help="Enable a specific microphone by name and start real-time transcription immediately. Similar to --set_microphone but automatically begins listening. Use exact device name from --list_microphones output. Convenient for scripted or automated transcription setups.", type=str)
    mic_grp.add_argument("--energy_threshold", default=100, help="Energy level for mic to detect.", type=int)
    mic_grp.add_argument("--mic_calibration_time", help="How long to calibrate the mic for in seconds. To skip user input type 0 and time will be set to 5 seconds.", type=int)
    mic_grp.add_argument("--record_timeout", default=1, help="Recording buffer timeout in seconds. Lower values (e.g., 1-2) provide more real-time processing but may cut off words. Higher values (e.g., 3-5) allow for more complete phrases but introduce processing delay. Recommended: 2-3 seconds for balanced performance.", type=float)
    mic_grp.add_argument("--phrase_timeout", default=5, help="Silence duration in seconds before considering audio as a new phrase/sentence. When this timeout is reached, accumulated audio is processed and the buffer is cleared. Lower values (1-2s) process shorter phrases quickly, higher values (5-10s) wait for longer complete sentences. Recommended: 2-5 seconds depending on speech patterns.", type=float)
    mic_grp.add_argument("--mic_chunk_size", default=1, help="Number of audio chunks to collect before processing a batch when using microphone input with --paddedaudio enabled. Example: --mic_chunk_size 2 --paddedaudio 1 will process 2 new chunks + 1 previous chunk (3 total) per batch. Higher values provide more context but increase processing delay. Set to 1 for immediate processing. Recommended: 1-3 chunks.", type=int)
    mic_grp.add_argument("--paddedaudio", default=0, help="Number of audio chunks from the previous batch to include as context when processing new audio. Helps maintain conversation flow and reduces word-boundary errors. Example: --paddedaudio 1 --mic_chunk_size 2 processes each batch with 1 previous chunk + 2 new chunks. For streaming: works with --stream_chunks. For microphone: works with --mic_chunk_size. Set to 0 to disable. Recommended: 1-2 chunks for better accuracy.", type=int)
    mic_grp.add_argument("--discord_webhook", default=None, help="Discord webhook URL for sending live transcription results to a Discord channel. Format: https://discord.com/api/webhooks/[ID]/[TOKEN]. Useful for live streaming integration, remote monitoring, or collaborative transcription. Test webhook URL in Discord before using. Only works with real-time microphone mode.", type=str)

    # Streaming & HLS
    stream_grp = parser.add_argument_group("Streaming & HLS")
    stream_grp.add_argument("--stream", default=None, help="Live stream URL for real-time transcription and translation. Supports YouTube Live, Twitch, and direct media streams. Examples: 'https://twitch.tv/laplusdarknesss_hololive', 'https://youtube.com/watch?v=LIVESTREAM_ID', or direct HLS/M3U8 URLs. Enables continuous processing of streaming audio with automatic chunk management and reconnection handling.")
    stream_grp.add_argument("--stream_original_text", action='store_true', help="Display the automatically detected source language of stream audio alongside transcriptions. Useful for multilingual streams or when stream language changes during broadcast. Shows confidence level of language detection to help verify accuracy of transcription language selection.")
    stream_grp.add_argument("--stream_chunks", default=5, help="Number of audio segments to divide stream processing into for parallel processing and memory management. Larger values (7-10) better for stable internet but use more memory. Smaller values (1-3) better for unstable connections. YouTube: 1-2 recommended, Twitch: 5-10 recommended, Direct streams: 3-5 recommended.", type=int)
    stream_grp.add_argument("--stream_language", default=None, help="Force specific source language for stream transcription instead of automatic detection. Use language codes like 'en', 'ja', 'es', 'fr', etc. Improves accuracy and processing speed when stream language is known and consistent. Leave empty for automatic language detection.", type=str, choices=VALID_LANGUAGES)
    stream_grp.add_argument("--stream_translate", action='store_true', help="Enable automatic translation of stream transcriptions to English (or target language if specified). Translation occurs after transcription, showing both original and translated text. Useful for understanding foreign language streams. Requires additional processing time and internet connection for best quality.")
    stream_grp.add_argument("--stream_transcribe", nargs='?', const=True, default=False, help="Enable stream transcription with optional target language specification. Use '--stream_transcribe English' to transcribe to specific language, or just '--stream_transcribe' for default transcription. Processes live audio into text with timing information suitable for real-time applications.", type=str)
    stream_grp.add_argument("--auto_hls", action="store_true", help="Automatically analyze HLS stream characteristics and optimize chunk processing settings. Samples segment duration and suggests optimal --stream_chunks value before starting transcription. Improves processing efficiency and reduces buffering issues for unknown streams. Recommended for first-time processing of new HLS sources.")
    stream_grp.add_argument("--selectsource", nargs='?', const='interactive', default=None, help="Choose specific audio quality/format from available stream options. Use without value for interactive selection menu, or specify format directly: 'bestaudio' (highest quality), '140' (specific format ID), 'worst' (lowest quality/fastest). Helpful for streams with multiple audio tracks or quality options. Youtube usually works best when set to 91.")
    stream_grp.add_argument("--cookies", default=None, help="Path to browser cookies file for accessing private or age-restricted streams/videos. Supports multiple formats: absolute path (C:\\path\\to\\cookies.txt), filename in current directory (cookies.txt), or shorthand for cookies folder (youtube = cookies/youtube.txt). Must be in NetScape format. Use browser extensions to export cookies.")
    stream_grp.add_argument("--cookies-from-browser", default=None, help="Automatically extract cookies from installed browser for stream/video access. Eliminates need for manual cookie file export. Supported browsers: brave, chrome, chromium, edge, firefox, opera, safari, vivaldi, whale. Example: --cookies-from-browser chrome. Requires browser to be closed during extraction.", choices=["brave", "chrome", "chromium", "edge", "firefox", "opera", "safari", "vivaldi", "whale"])
    stream_grp.add_argument("--remote_hls_password_id", type=str, help="Authentication parameter name for password-protected HLS streams or web servers. Typically 'id', 'key', 'auth', or 'token' depending on server configuration. Used in combination with --remote_hls_password to access private streaming content. Check stream provider documentation for correct parameter name.")
    stream_grp.add_argument("--remote_hls_password", type=str, help="Authentication password/token for accessing password-protected HLS streams or remote web servers. Used with --remote_hls_password_id to authenticate against private streams. Keep secure and don't include in scripts that may be shared. Required for accessing premium or restricted streaming content.")

    # File mode / caption generation
    file_grp = parser.add_argument_group("File Mode / Captioning")
    file_grp.add_argument("--makecaptions", nargs='?', const=True, default=False, help="Generate subtitle files (SRT format) from audio/video files instead of real-time transcription. Use '--makecaptions' for default processing, or '--makecaptions compare' to test all available model sizes (11gb-v3, 11gb-v2, 7gb, 6gb, 3gb, 2gb, 1gb) and compare accuracy vs speed tradeoffs. Output saved to specified folder with timing information.")
    file_grp.add_argument("--file_input", default=None, help="Path to audio or video file for batch transcription/translation. Supports most common formats: MP3, WAV, MP4, AVI, MKV, FLAC, OGG, M4A, etc. Can be absolute path (C:\\path\\to\\file.mp3) or relative path (audio/file.wav). Used with --makecaptions for subtitle generation or standalone for text transcription.")
    file_grp.add_argument("--file_output", default=None, help="Custom output file path for transcription results. Specify full path including filename and extension (e.g., 'transcripts/result.txt' or 'C:\\output\\transcript.srt'). If not specified, output filename is automatically generated based on input filename. Directory will be created if it doesn't exist.")
    file_grp.add_argument("--file_output_name", default=None, help="Custom base filename for output files without extension or path. Example: 'my_transcript' will create 'my_transcript.srt'. Used when you want to control filename but keep default output directory. Extension is automatically added based on output type (srt).")
    file_grp.add_argument("--word_timestamps", action='store_true', default=False, help="Generate word-level timestamps in subtitle files (SRT format). Only works with subtitle generation mode (--makecaptions), not with real-time microphone or streaming modes. Useful for precise subtitle timing and editing.")
    file_grp.add_argument("--subtype", choices=["burn", "embed"], default=None, help="Process video with subtitles after generation. 'burn' overlays subtitles permanently onto the video using FFmpeg. 'embed' adds subtitle track to video container as a separate stream. Only works with --makecaptions mode and video input files. Requires FFmpeg to be available in PATH.")
    file_grp.add_argument("--substyle", default=None, help="Customize subtitle appearance when burning subtitles (--subtype burn). Accepts comma-separated style options: 'font,fontsize,color'. Font files should be placed in 'fonts/' folder (e.g., fonts/FiraSans-Bold.otf). Examples: '--substyle FiraSans-Bold.otf,24' for custom font and size, '--substyle 20,white' for size and color, '--substyle Arial,16,yellow' for all options. Only works with --subtype burn.")
    file_grp.add_argument("--print_srt_to_console", action='store_true', default=False, help="Display generated SRT subtitle content in the console/terminal after creating subtitle files. Useful for quick preview, debugging subtitle timing, or piping subtitle content to other programs. Only works with --makecaptions mode, not real-time transcription.")
    file_grp.add_argument("--silent_detect", action='store_true', help="Skip processing of silent audio segments during subtitle generation to improve efficiency and reduce processing time. Automatically detects quiet periods and excludes them from transcription. Only works with --makecaptions mode, not compatible with live streaming or microphone input. Use with --silent_threshold and --silent_duration for fine-tuning.")
    file_grp.add_argument("--silent_threshold", type=float, default=-35.0, help="Audio volume threshold in decibels (dB) for silence detection. Lower values (e.g., -45.0) are more sensitive and detect quieter speech like whispers. Higher values (e.g., -25.0) only detect louder, clearer speech. Typical range: -45.0 to -20.0 dB. Only used with --silent_detect flag.")
    file_grp.add_argument("--silent_duration", type=float, default=0.5, help="Minimum duration in seconds for audio to be classified as silence. Higher values (e.g., 2.0) treat brief pauses as speech, preserving natural conversation flow. Lower values (e.g., 0.1) detect shorter silent periods for more aggressive silence removal. Typical range: 0.1 to 3.0 seconds. Only used with --silent_detect flag.")
    file_grp.add_argument("--batchmode", type=valid_batchmode, default=1, help="Number of speech regions to process simultaneously in parallel for faster transcription. Higher values (2-4) can significantly improve processing speed on multi-core systems but use more VRAM/RAM. Example: '--batchmode 2' processes 2 regions at once. Recommended: 1-4 depending on your hardware capabilities. Only works with --makecaptions mode.")
    file_grp.add_argument("--adaptive_batch", action='store_true', help="Enable intelligent adaptive batch processing that dynamically allocates jobs between GPU and CPU based on available VRAM, performance learning, and smart job sorting. Automatically detects GPU capacity and optimizes job distribution for maximum throughput. Works with --batchmode and --makecaptions. When enabled, --batchmode value is ignored in favor of auto-detected optimal GPU/CPU slot allocation.")
    file_grp.add_argument("--cpu_batches", type=int, default=None, help="Number of concurrent CPU batch slots for adaptive batch processing. If not specified, system automatically suggests optimal value based on available RAM (1 for <16GB, 2 for 16-32GB, 3 for >32GB). Higher values increase CPU parallelization but may cause system slowdown. Recommended: 1-4. Only used with --adaptive_batch.")
    file_grp.add_argument("--max_cpu_time", type=int, default=300, help="Maximum time in seconds that a single job can run on CPU during adaptive batch processing. Jobs predicted to exceed this time will wait for GPU instead. Default: 300 seconds (5 minutes). Lower values prioritize GPU for longer jobs, higher values allow more CPU usage. Recommended: 60-600. Only used with --adaptive_batch.")
    file_grp.add_argument("--stop_cpu_at", type=float, default=0.8, help="Progress threshold (0.0-1.0) at which to stop allocating new jobs to CPU and use GPU-only for remaining work. This 'endgame strategy' ensures predictable completion times. Default: 0.8 (80%% complete). Lower values (0.6-0.7) finish faster with more GPU usage, higher values (0.85-0.95) maximize CPU utilization. Only used with --adaptive_batch.")
    file_grp.add_argument("--batchjobsize", type=valid_batchjobsize, default=4, help="Model size in GB used for GPU capacity calculation in adaptive batch processing. Specifies how much VRAM each concurrent job requires. Range: 0.1-12.0 GB. Default: 4 GB (typical for medium models like 'small'). Use smaller values (0.1-2) for tiny models or larger values (6-11) for large models to accurately calculate how many jobs fit in VRAM. Only used with --adaptive_batch.")
    file_grp.add_argument("--isolate_vocals", nargs='?', const='0', default=False, type=valid_demucs_jobs, help="Use AI-powered audio separation to isolate vocals from background music/noise before transcription. Improves accuracy for music videos, podcasts with background music, or noisy audio. Specify parallel processing: 'all' for all CPU cores, a number (1-8) for specific core count, or leave empty for single-threaded. Requires additional processing time.")
    file_grp.add_argument("--demucs_model", default="htdemucs", help="AI model for vocal isolation when --isolate_vocals is enabled. 'htdemucs' (recommended) offers best quality, 'htdemucs_ft' is fine-tuned version, 'mdx' models are faster but less accurate. Choose based on quality vs speed preference.", choices=["htdemucs", "htdemucs_ft", "htdemucs_6s", "hdemucs_mmi", "mdx", "mdx_extra", "mdx_q", "mdx_extra_q", "hdemucs", "demucs"])
    file_grp.add_argument("--keep_temp", action='store_true', help="Preserve temporary audio files created during processing instead of deleting them. Useful for debugging audio quality issues, analyzing preprocessing effects, or manual audio inspection. Files saved to temp/ directory. Warning: can consume significant disk space with large audio files.")
    file_grp.add_argument("--timeout", type=int, default=0, help="Set the timeout duration for the transcription worker process (in seconds).")

    # Output and Web UI
    output_grp = parser.add_argument_group("Output & Web UI")
    output_grp.add_argument("--save_transcript", action='store_true', help="Automatically save transcription results to text files. Creates timestamped files with complete transcription text in the output directory. Useful for record keeping, further analysis, or batch processing workflows. Files are saved with datetime stamps for easy organization.")
    output_grp.add_argument("--save_folder", default="out", help="Output directory for saved transcripts, subtitle files, and processed audio. Creates directory if it doesn't exist. Use relative path (e.g., 'transcripts') or absolute path (e.g., 'C:/MyTranscripts'). All output files including SRT captions and TXT transcripts are saved here.")
    output_grp.add_argument("--serverip", default="127.0.0.1", type=str, help="IP address for the web server to bind to. Use 127.0.0.1 for localhost only (default), 0.0.0.0 to listen on all interfaces, or a specific IP available on your machine.")
    output_grp.add_argument("--portnumber", default=None, help="TCP port number for web interface server (8000-65535 recommended). When specified, starts a web-based control panel accessible via browser at http://localhost:[PORT]. Enables remote control, file uploads, and live transcription monitoring. Use unique port numbers to avoid conflicts with other applications. Ports below 8000 may require administrator privileges on Windows.", type=valid_port_number)
    output_grp.add_argument("--https", default=None, help="TCP port number for HTTPS web interface server (8443 recommended). When specified, starts an additional HTTPS server with self-signed certificate alongside the HTTP server. Example: '--portnumber 8000 --https 8443' runs HTTP on port 8000 and HTTPS on port 8443. Both servers provide the same functionality simultaneously. Ports below 8000 may require administrator privileges on Windows.", type=valid_port_number)

    # Filtering & blocklist
    filter_grp = parser.add_argument_group("Filtering & Blocklist")
    filter_grp.add_argument("--ignorelist", type=str, help="Path to blacklist/filter file containing words or phrases to exclude from transcription output. Must be a .txt file with one term per line. Useful for filtering profanity, repetitive phrases, or background noise words. Works with both real-time and file processing modes. Use with --auto_blocklist for automatic blacklist management.")
    filter_grp.add_argument("--auto_blocklist", action='store_true', help="Automatically add frequently filtered phrases to the blacklist file for permanent filtering. When a phrase is blocked 3 or more times during transcription, it's automatically added to --ignorelist file. Requires --ignorelist to be specified. Useful for learning and removing recurring background noise or unwanted content.")

    # Reliability
    reliability_grp = parser.add_argument_group("Reliability & Retries")
    reliability_grp.add_argument("--retry", action='store_true', help="Automatically retry failed transcription attempts. Useful for handling temporary network issues, memory problems, or audio processing glitches. May increase total processing time but improves reliability for important transcriptions. Particularly helpful with large files or unstable system conditions.")

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
        print(f"{Fore.YELLOW}  The --word_timestamps flag is only supported for subtitle generation (sub_gen). Please remove the redundant command flag as it serves no purpose in microphone or HLS modes.{Style.RESET_ALL}")
        exit(1)

    # Validate --subtype usage
    if args.subtype and not args.makecaptions:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} --subtype can only be used with --makecaptions for video subtitle processing.")
        print("The --subtype option requires subtitle generation mode to work with video files.")
        sys.exit(1)

    # Check for --substyle help
    if args.substyle and args.substyle.lower() == "help":
        show_substyle_help()
        sys.exit(0)

    # Validate --substyle usage
    if args.substyle and (not args.subtype or args.subtype != "burn"):
        print(f"{Fore.RED}Error:{Style.RESET_ALL} --substyle can only be used with --subtype burn for customizing burned subtitle appearance.")
        print("The --substyle option requires subtitle burning mode (--subtype burn) to apply visual customizations.")
        sys.exit(1)

    # Validate port ranges for Windows compatibility
    if sys.platform.startswith('win'):
        if args.portnumber and args.portnumber < 8000:
            print(f"{Fore.YELLOW}Warning:{Style.RESET_ALL} Port {args.portnumber} is below 8000 and may require administrator privileges on Windows.")
            print(f"{Fore.YELLOW}Recommendation:{Style.RESET_ALL} Use ports 8000-65535 for better compatibility (e.g., --portnumber 8000)")
        if args.https and args.https < 8000:
            print(f"{Fore.YELLOW}Warning:{Style.RESET_ALL} HTTPS port {args.https} is below 8000 and may require administrator privileges on Windows.")
            print(f"{Fore.YELLOW}Recommendation:{Style.RESET_ALL} Use ports 8000-65535 for better compatibility (e.g., --https 8443)")

    return args
