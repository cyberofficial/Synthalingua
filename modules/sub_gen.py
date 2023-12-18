# Import necessary modules. Ensure 'modules.imports' contains all required imports.
from modules.imports import *
# Parse command-line arguments. Make sure 'parser_args.parse_arguments()' is properly set up in your project.
args = parser_args.parse_arguments()

# Import the Whisper module.
import whisper

# Function to detect language from an audio file.
def detect_language(file_path, model, device):
    try:
        # Load and process the audio file.
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)
        # Choose the number of Mel frequency channels based on available RAM.
        mel = whisper.log_mel_spectrogram(audio, n_mels=128 if args.ram == "12gb" else 80).to(device)
        # Detect the language.
        _, language_probs = model.detect_language(mel)
        # Return the language with the highest probability.
        return max(language_probs, key=language_probs.get)
    except RuntimeError as e:
        # Handle any runtime errors.
        print(f"Error detecting language: {e}")
        return "n/a"

# Function to format time for SRT subtitles.
def format_time_srt(seconds):
    """ Converts seconds to the SRT time format. """
    millisec = int((seconds % 1) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millisec:03}"

# Function to generate a simple text transcription from an audio file.
def generate_subtitles(fileinput, fileout, model_size):
    try:
        model = whisper.load_model(model_size)
        device = args.device  # Ensure this is correctly defined

        audio = whisper.load_audio(fileinput)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio, n_mels=128 if args.ram == "12gb" else 80).to(device)

        options = whisper.DecodingOptions(fp16=False, task="transcribe")
        result = model.decode(mel, options)

        # Write the transcription to a text file.
        with open(fileout, 'w', encoding='utf-8') as file:
            file.write(result.text)

        print(f"Transcription saved to {fileout}")
    except Exception as e:
        print(f"Error in transcription generation: {e}")

# Indicate that the subtitles generator module is loaded.
print("Subtitles Generator Module Loaded")
