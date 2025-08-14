import sys

# Check if this process is being launched as a worker for subtitle generation
if '--run-worker' in sys.argv:
    try:
        # This branch is for the frozen executable to re-launch itself as a worker.
        # It won't be triggered when running from source because sub_gen.py calls
        # transcribe_worker.py directly in that case.
        from modules.transcribe_worker import main as worker_main

        # Re-arrange sys.argv for the worker's argument parser.
        # Original: [exe_path, '--run-worker', '--arg1', 'val1', ...]
        # New for worker: [exe_path, '--arg1', 'val1', ...]
        # The worker's parser will parse from index 1 onwards.
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        worker_main()
    except Exception as e:
        # Log any errors to stderr for the parent process to capture
        print(f"Worker process failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Ensure the worker process exits cleanly
        sys.exit(0)

# If not a worker, proceed with normal imports and execution
import os
import torch
import speech_recognition as sr
import whisper
import openvino as ov
from queue import Queue
from tempfile import NamedTemporaryFile
from colorama import Fore, Style, init

# Set up proper encoding for Windows to handle Unicode characters
if sys.platform.startswith('win'):
    # Set environment variables for proper UTF-8 handling
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from modules.audio_handlers import record_callback, handle_mic_calibration
from modules.device_manager import get_microphone_source, list_microphones, setup_device
from modules.file_handlers import load_blacklist, setup_temp_directory, clean_temp_directory, save_transcript, handle_error, cleanup_temp_cookie_file
from modules.BaseWhisper import BaseWhisperModel
from modules.FasterWhisper import FasterWhisperModel
from modules.OpenVINOWhisper import OpenVINOWhisperModel
from modules.transcription_core import TranscriptionCore
from modules.stream_handler import handle_stream_setup
from modules.stream_transcription_module import stop_transcription
from modules.sub_gen import run_sub_gen
from modules import parser_args
from modules.languages import get_valid_languages
from modules import api_backend
from modules.version_checker import check_for_updates
from modules.discord import send_to_discord_webhook, send_startup_notification, send_shutdown_notification
from modules.about import contributors
from modules.sub_gen import run_sub_gen

# =================================================================
# PyInstaller Compatibility Block
# This section is to help PyInstaller find all the hidden modules
# that the 'transformers' library and its ecosystem load dynamically.
# This is the definitive fix for the FileNotFoundError at runtime.
# =================================================================
try:
    # Explicitly import all known speech models to make them visible to PyInstaller
    from transformers.models.auto import modeling_auto
    for model_class in modeling_auto.MODEL_FOR_SPEECH_SEQ_2_SEQ_MAPPING_NAMES.values():
        try:
            # e.g., __import__("transformers.models.whisper.modeling_whisper")
            __import__(f"transformers.models.{model_class.lower()}.modeling_{model_class.lower()}")
        except ImportError:
            pass  # Ignore if a specific model isn't available
except Exception:
    # This block will likely fail if run outside of a build process, which is fine.
    pass
# =================================================================

init()


def main():
    args = parser_args.parse_arguments()

    # Early exit conditions
    if len(sys.argv) == 1:
        print("No arguments provided. Please run the script with the --help flag to see a list of available arguments.")
        sys.exit(1)

    if args.about:
        from modules.version_checker import ScriptCreator, GitHubRepo
        contributors(ScriptCreator, GitHubRepo)

    # Handle microphone listing and exit if requested
    if args.list_microphones:
        list_microphones()
        sys.exit(0)    # Check input sources
    if args.stream is None and args.microphone_enabled is None and not args.makecaptions:
        print("No audio source was set. Please set an audio source.")
        reset_text = Style.RESET_ALL
        input(f"Press {Fore.YELLOW}[enter]{reset_text} to exit.")
        sys.exit("Exiting...")

    if args.stream is not None and args.microphone_enabled is not None:
        print("You can only use one input source. Please only set one input source.")
        reset_text = Style.RESET_ALL
        input(f"Press {Fore.YELLOW}[enter]{reset_text} to exit.")
        sys.exit("Exiting...")

    # Validate silent_detect usage
    if getattr(args, 'silent_detect', False) and not args.makecaptions:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} --silent_detect can only be used with --makecaptions for caption generation.")
        print("Silent detection is not supported for HLS streaming or microphone input.")
        sys.exit("Exiting...")

    # Validate batchmode usage
    if getattr(args, 'batchmode', 1) > 1 and not args.makecaptions:
        print(f"{Fore.RED}Error:{Style.RESET_ALL} --batchmode can only be used with --makecaptions for caption generation.")
        print("Parallel batch processing is not supported for HLS streaming or microphone input.")
        sys.exit("Exiting...")

    # Check for correct transcription arguments
    if args.stream_transcribe is True and not isinstance(args.stream_transcribe, str):
        # User used --stream_transcribe without a language
        print(f"{Fore.YELLOW}Note:{Style.RESET_ALL} Stream transcribe is set without a target language. Using 'English' as default.")
        args.stream_transcribe = "English"

    # Load blacklist (skip empty lines)
    blacklist = []
    if args.ignorelist:
        print(f"Loaded word filtering list from: {args.ignorelist}")
        blacklist = [word for word in load_blacklist(args.ignorelist) if word]
        if blacklist:
            print(f"Loaded blacklist: {blacklist}")

    # Check for updates
    if args.updatebranch != "disable":
        print("\nChecking for updates...")
        try:
            check_for_updates()
        except Exception as e:
            print(f"Error checking for updates: {str(e)}")
            print("Continuing with script...\n\n")

    # Initialize recording components
    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    # Set up device (CPU/CUDA/iGPU/dGPU/NPU)
    device = setup_device(args)
    if args.model_source == "openvino":
        device_name = ov.Core().get_property(device, "FULL_DEVICE_NAME")
        print(f"Using device: {device_name}")
    else:
        print(f"Using device: {device}")

    # Set up audio source
    source_calibration = None
    source_listening = None
    if args.microphone_enabled:
        try:
            source_calibration, source_listening, mic_name = get_microphone_source(args)
            handle_mic_calibration(recorder, source_calibration, args)
        except ValueError as e:
            print("Error: Unable to initialize microphone. Check your microphone settings and permissions.")
            print(f"Error details: {str(e)}")
            sys.exit(1)

    # Validate languages (normalize to lowercase)
    valid_languages = [lang.lower() for lang in get_valid_languages()]
    if args.language and args.language.lower() not in valid_languages:
        print("Invalid language. Please choose a valid language from the list below:")
        print(valid_languages)
        return

    if args.transcribe and not args.target_language:
        print("Transcribe is set but no target language is set. Please set a target language.")
        return
    elif args.transcribe and args.target_language and args.target_language.lower() not in valid_languages:
        print("Invalid target language. Please choose a valid language from the list below:")
        print(valid_languages)
        return

    # Adjust phrase timeout for Discord webhook
    if args.microphone_enabled and args.phrase_timeout > 1 and args.discord_webhook:
        print(f"{Fore.RED}WARNING{Style.RESET_ALL}: phrase_timeout is set to {args.phrase_timeout} seconds. Setting to 1 second to avoid multiple webhook messages.")
        args.phrase_timeout = 1

    # Set up model directory
    if not os.path.exists(args.model_dir):
        print("Creating models folder...")
        os.makedirs(args.model_dir)    # Configure model
    # Use stream_language for model selection if in stream mode
    model_language = args.stream_language if args.stream else args.language
    model = parser_args.set_model_by_ram(args.ram, model_language)
    if not args.makecaptions:
        if args.model_source == "fasterwhisper":
            audio_model = FasterWhisperModel(model, device=device, download_root=args.model_dir, compute_type=args.compute_type)
        elif args.model_source == "openvino":
            audio_model = OpenVINOWhisperModel(model, device=device, download_root=args.model_dir, compute_type=args.compute_type)
        elif args.model_source == "whisper":
            audio_model = BaseWhisperModel(model, device=device, download_root=args.model_dir)
        else:
            ValueError(f"{args.model_source} is not a valid model source")

    # Set up API backend if needed
    if args.portnumber:
        print("Port number was set, so spinning up a web server...")
        api_backend.flask_server(operation="start", portnumber=args.portnumber)    # Set up temporary directory
    temp_dir = setup_temp_directory()

    # Initialize webhook
    webhook_url = args.discord_webhook if args.discord_webhook else None
    if webhook_url:
        translation_status = args.translate
        model_info = f"{args.ram} model"
        # Include stream source if available
        stream_source = args.stream if args.stream else None
        send_startup_notification(webhook_url, model_info, translation_status, stream_source)    # Handle caption generation
    if args.makecaptions:
        if args.file_output_name is None:
            args.file_output_name = "filename"
        
        # Check if compare mode is enabled
        if args.makecaptions == "compare":
            # Run through all RAM options from 11gb-v3 backwards
            ram_options = ["1gb", "2gb", "3gb", "6gb", "7gb", "11gb-v2", "11gb-v3"]
            original_ram = args.ram  # Save original RAM setting            
            print(f"🔄 Compare mode enabled - generating captions with all RAM models...")
            print(f"📁 Output files will be saved to: {args.file_output}")
            print(f"📝 Base filename: {args.file_output_name}")
            print()
            
            for i, ram_option in enumerate(ram_options):
                print(f"[{i+1}/{len(ram_options)}] Processing with {ram_option} model...")
                args.ram = ram_option  # Temporarily change RAM setting                # Create unique output filename for each model
                model_output_name = f"{args.file_output_name}.{ram_option}"
                
                try:
                    run_sub_gen(args.file_input, model_output_name, args.file_output, ram_setting=ram_option)
                    print(f"✅ Completed {ram_option} model - saved as '{model_output_name}'")
                    print("🗑️ Model unloaded, VRAM/RAM freed for next model")
                except Exception as e:
                    print(f"❌ Error with {ram_option} model: {e}")
                    print(f"⏭️  Continuing with next model...")
                
                print()
            
            args.ram = original_ram  # Restore original RAM setting
            print("🎉 Compare mode completed! Check your output folder for all caption files.")
            print("💡 Tip: Compare the different files to choose the best quality for your needs.")
        else:
            # Standard single model caption generation
            run_sub_gen(args.file_input, args.file_output_name, args.file_output)
        
        print("Press enter to exit...")
        input()
        sys.exit("Exiting...")

    # Set up stream if needed
    stream_thread = None
    if args.stream:
        print(f"Stream mode enabled. Using stream: {args.stream}")
        stream_thread = handle_stream_setup(args, audio_model, temp_dir, webhook_url)
    
    # Start microphone listening if enabled
    if args.microphone_enabled:
        try:
            print(f"Microphone set to: {mic_name}")            # Set up background listening without context manager
            recorder.listen_in_background(source_listening, lambda r, a: record_callback(r, a, data_queue),
                                    phrase_time_limit=args.record_timeout)
        except AssertionError as e:
            print("Error: Unable to initialize microphone. Check your microphone settings and permissions.")
            print(f"Error details: {str(e)}")
            sys.exit(1)

    print("Model loaded.\n")
    print(f"Using {model} model.")

    args.model = model  # Add the model name to args
    transcription_core = TranscriptionCore(args, device, audio_model, blacklist, temp_dir)

    # Start the background processing queue
    transcription_core.start_queue_processing()

    try:        # Main processing loop
        while True:
            if not transcription_core.process_audio(data_queue, source_listening):
                break

    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C detected - Shutting down...")
        
        # Stop the background processing queue
        transcription_core.stop_queue_processing()
        
        if args.stream:
            print("Stopping stream transcription...")
            stop_transcription()
            clean_temp_directory(temp_dir)
        
        # Clean up any temporary cookie files
        if hasattr(args, '_temp_cookie_files'):
            for temp_cookie_file in args._temp_cookie_files:
                cleanup_temp_cookie_file(temp_cookie_file)
        
        if webhook_url:
            print("Sending shutdown notification to Discord...")
            send_shutdown_notification(webhook_url)
        
        if args.save_transcript:
            print("Saving transcript...")
            save_transcript(transcription_core.transcription, args)
            
        if args.portnumber:
            print("Shutting down web server...")
            api_backend.kill_server()
        
        print("✅ Shutdown complete!")
        sys.exit(0)

    except Exception as e:
        # Stop the background processing queue on any error
        transcription_core.stop_queue_processing()
        is_keyboard_interrupt = handle_error(e, webhook_url)
        if is_keyboard_interrupt:
            sys.exit(0)

try:
    from multiprocessing import freeze_support
except ImportError:
    freeze_support = None


if __name__ == "__main__":
    if freeze_support:
        freeze_support()
    main()