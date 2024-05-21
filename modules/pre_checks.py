from modules.imports import *


def pre_checks(args):
    if len(sys.argv) == 1:
        print("No arguments provided. Please run the script with the --help flag to see a list of available arguments.")
        sys.exit(1)

    if args.about:
        from modules.about import contributors
        from modules.version_checker import ScriptCreator, GitHubRepo
        contributors(ScriptCreator, GitHubRepo)

    # Check for Stream or Microphone is no present then exit
    if args.stream == None and args.microphone_enabled == None:
        if args.makecaptions:
            # skip if makecaptions is set
            pass
        else:
            print("No audio source was set. Please set an audio source.")
            reset_text = Style.RESET_ALL
            input(f"Press {Fore.YELLOW}[enter]{reset_text} to exit.")
            sys.exit("Exiting...")
    # If stream and microphone is set then exit saying you can only use one input source
    if args.stream != None and args.microphone_enabled != None:
        print("You can only use one input source. Please only set one input source.")
        reset_text = Style.RESET_ALL
        input(f"Press {Fore.YELLOW}[enter]{reset_text} to exit.")
        sys.exit("Exiting...")

    if args.stream_transcribe and args.stream_target_language == None:
        print("Stream Transcribe is set but no stream target language is set. Please set a stream target language.")
        sys.exit("Exiting...")