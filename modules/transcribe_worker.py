"""
Transcription Worker Module

This script is designed to be called as a child process from the main subtitle generator.
Its sole purpose is to perform a single transcription/translation task using a
specified Whisper model and audio file.

It takes command-line arguments to define the task, loads the model, runs the
transcription, and writes the output (or any errors) to a specified JSON file.
By running in a separate process, it guarantees that all VRAM and RAM used by
the model are fully released upon completion, preventing memory caching issues
when switching between models.

Usage:
python transcribe_worker.py --audio_path <path> --output_json_path <path> --model_type <type> ...
"""
import argparse
import json
import logging
import sys
import os
from pathlib import Path

import whisper

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='[Worker] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def load_whisper_model(model_type: str, device: str, model_dir: str):
    """
    Loads a Whisper model.
    (Copied from sub_gen.py for standalone execution)
    """
    try:
        download_root = Path(model_dir)
        if not download_root.exists():
            logger.info("Creating model directory: %s", download_root)
            download_root.mkdir(parents=True, exist_ok=True)
            
        logger.info("Loading Whisper model: %s from %s", model_type, download_root)
        return whisper.load_model(model_type, device=device, download_root=str(download_root))
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model '{model_type}': {e}")

def main():
    """Main execution block for the worker process."""
    parser = argparse.ArgumentParser(description="Whisper Transcription Worker")
    parser.add_argument("--audio_path", required=True, type=str, help="Path to the audio file to process.")
    parser.add_argument("--output_json_path", required=True, type=str, help="Path to write the resulting JSON output.")
    parser.add_argument("--model_type", required=True, type=str, help="Whisper model type (e.g., 'base', 'large-v3').")
    parser.add_argument("--model_dir", required=True, type=str, help="Directory to load models from.")
    parser.add_argument("--device", required=True, type=str, help="Device to run on ('cpu' or 'cuda').")
    parser.add_argument("--decode_options_json", required=True, type=str, help="JSON string of Whisper decode options.")
    
    args = parser.parse_args()

    try:
        # Deserialize the decode options from the JSON string
        decode_options = json.loads(args.decode_options_json)
        logger.info("Received decode options: %s", decode_options)

        # Load the specified model
        model = load_whisper_model(args.model_type, args.device, args.model_dir)

        # Perform the transcription
        logger.info("Starting transcription for: %s", args.audio_path)
        result = model.transcribe(args.audio_path, **decode_options)
        logger.info("Transcription complete.")

        # Prepare successful output
        output_data = {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error("An error occurred during transcription: %s", e, exc_info=True)
        # Prepare error output
        output_data = {
            "status": "error",
            "message": str(e)
        }
        # Write error and exit with a non-zero status code
        with open(args.output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        sys.exit(1)

    # Write the successful result to the output JSON file
    try:
        with open(args.output_json_path, 'w', encoding='utf-8') as f:
            # We need a custom default handler for sets that might appear in word data
            def set_default(obj):
                if isinstance(obj, set):
                    return list(obj)
                raise TypeError

            json.dump(output_data, f, ensure_ascii=False, indent=4, default=set_default)
        logger.info("Successfully wrote results to %s", args.output_json_path)
    except Exception as e:
        logger.error("Failed to write output JSON: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()