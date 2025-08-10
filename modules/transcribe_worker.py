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

# CRITICAL: Set up UTF-8 encoding BEFORE any other imports
import sys
import os

# Force UTF-8 encoding for all operations
if sys.platform.startswith('win'):
    # Set environment variables first
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    
    # Try to reconfigure stdout/stderr for UTF-8 if possible
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, OSError):
        # Fallback: ignore if reconfigure not available or fails
        pass

# Now import other modules
import argparse
import json
import logging
from pathlib import Path
import pycountry

# Configure basic logging with UTF-8 support and error handling
try:
    logging.basicConfig(
        level=logging.INFO, 
        format='[Worker] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
except UnicodeError:
    # Fallback logging configuration if UTF-8 fails
    logging.basicConfig(
        level=logging.INFO, 
        format='[Worker] %(levelname)s: %(message)s'
    )

logger = logging.getLogger(__name__)

# Log UTF-8 setup success
try:
    logger.info("Worker started with UTF-8 encoding support")
except UnicodeError:
    # If even this fails, continue silently
    pass

def get_transcription_result(model_source, model_type, device, model_dir, compute_type, audio_path, decode_options):
    """
    Loads the appropriate model and performs transcription.
    """
    # Create a copy of the options to modify safely for each model source
    transcribe_options = decode_options.copy()

    if model_source == "fasterwhisper":
        from faster_whisper import WhisperModel
        
        logger.info(f"Loading FasterWhisper model: {model_type}")
        model = WhisperModel(model_type, device=device, download_root=os.path.join(model_dir, "FasterWhisper"), compute_type=compute_type)
        
        # 1. 'fp16' is handled by compute_type at model load, not during transcription.
        transcribe_options.pop('fp16', None)

        # 2. Rename 'logprob_threshold' to 'log_prob_threshold'
        if 'logprob_threshold' in transcribe_options:
            transcribe_options['log_prob_threshold'] = transcribe_options.pop('logprob_threshold')
            
        # 3. Convert full language name to ISO code if necessary
        lang_option = transcribe_options.get('language')
        if lang_option and len(lang_option) > 2:
            try:
                language_obj = pycountry.languages.get(name=lang_option)
                if language_obj and hasattr(language_obj, 'alpha_2'):
                    lang_code = language_obj.alpha_2
                    transcribe_options['language'] = lang_code
                    logger.info(f"Converted language '{lang_option}' to code '{lang_code}' for faster-whisper.")
                else:
                    logger.warning(f"Could not find alpha_2 code for language '{lang_option}'. Transcription may fail if the code is not already valid.")
            except (AttributeError, KeyError):
                logger.warning(f"Could not convert language '{lang_option}' to a 2-letter code. Transcription may fail if the code is not already valid.")

        segments_generator, info = model.transcribe(audio_path, **transcribe_options)
        
        # Convert generator to a list of dictionaries in OpenAI Whisper format
        result_segments = []
        full_text_list = []
        for segment in segments_generator:
            seg_dict = {
                "id": segment.id,
                "seek": segment.seek,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "tokens": segment.tokens,
                "temperature": segment.temperature,
                "avg_logprob": segment.avg_logprob,
                "compression_ratio": segment.compression_ratio,
                "no_speech_prob": segment.no_speech_prob,
                "words": [{"start": w.start, "end": w.end, "word": w.word, "probability": w.probability} for w in segment.words] if segment.words else []
            }
            result_segments.append(seg_dict)
            full_text_list.append(segment.text)
            
        return {
            "text": "".join(full_text_list).strip(),
            "segments": result_segments,
            "language": info.language
        }

    elif model_source == "openvino":
        from optimum.intel import OVModelForSpeechSeq2Seq
        from transformers import AutoProcessor
        from transformers.pipelines import pipeline
        from transformers.generation.configuration_utils import GenerationConfig

        model_id = f"openai/whisper-{model_type}"
        ov_model_path = os.path.join(model_dir, "OpenVINO", model_id)
        
        logger.info(f"Loading OpenVINO model: {model_id} from {ov_model_path}")
        
        ov_model = OVModelForSpeechSeq2Seq.from_pretrained(ov_model_path, device=device, compile=False)
        ov_model.compile()  # type: ignore
        
        processor = AutoProcessor.from_pretrained(model_id)
        
        pipe = pipeline(
            "automatic-speech-recognition",
            model=ov_model,  # type: ignore
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
        )
        
        # OpenVINO also doesn't use these in its generate_kwargs
        transcribe_options.pop('fp16', None)
        transcribe_options.pop('condition_on_previous_text', None)
        transcribe_options.pop('logprob_threshold', None)


        # Add timestamp requests to generate_kwargs
        generate_kwargs = {
            "task": transcribe_options.get("task"),
            "language": f"<|{transcribe_options.get('language')}|>",
        }
        
        outputs = pipe(audio_path, generate_kwargs=generate_kwargs, return_timestamps=True, chunk_level_timestamps=True)
        
        # Convert pipeline output to Whisper format
        result_segments = []
        if isinstance(outputs, dict) and "chunks" in outputs:
            chunks = outputs.get("chunks", [])
            for i, chunk in enumerate(chunks):
                result_segments.append({
                    "id": i, "seek": 0,
                    "start": chunk["timestamp"][0],
                    "end": chunk["timestamp"][1],
                    "text": chunk["text"].strip()
                })
        
        return {
            "text": outputs.get("text", "").strip() if isinstance(outputs, dict) else "",
            "segments": result_segments,
            "language": transcribe_options.get("language", "unknown")
        }

    else:  # Default to standard Whisper
        import whisper
        logger.info(f"Loading standard Whisper model: {model_type}")
        model = whisper.load_model(model_type, device=device, download_root=model_dir)
        # Standard whisper uses 'fp16', so we use the original options
        return model.transcribe(audio_path, **decode_options)

def main():
    """Main execution block for the worker process."""
    parser = argparse.ArgumentParser(description="Whisper Transcription Worker")
    parser.add_argument("--audio_path", required=True, type=str, help="Path to the audio file to process.")
    parser.add_argument("--output_json_path", required=True, type=str, help="Path to write the resulting JSON output.")
    parser.add_argument("--model_type", required=True, type=str, help="Whisper model type (e.g., 'base', 'large-v3').")
    parser.add_argument("--model_dir", required=True, type=str, help="Directory to load models from.")
    parser.add_argument("--device", required=True, type=str, help="Device to run on ('cpu' or 'cuda').")
    parser.add_argument("--decode_options_json", required=True, type=str, help="JSON string of Whisper decode options.")
    parser.add_argument("--model_source", required=True, type=str.lower, choices=["whisper", "fasterwhisper", "openvino"], help="The model engine to use.")
    parser.add_argument("--compute_type", required=True, type=str, help="Compute type for FasterWhisper models (e.g., 'int8', 'float16').")
    
    args = parser.parse_args()

    try:
        decode_options = json.loads(args.decode_options_json)
        try:
            logger.info("Received decode options: %s", decode_options)
        except UnicodeError:
            logger.info("Received decode options (details suppressed due to encoding)")
        
        result = get_transcription_result(
            args.model_source, args.model_type, args.device, 
            args.model_dir, args.compute_type, args.audio_path, decode_options
        )

        output_data = {"status": "success", "result": result}

    except Exception as e:
        error_msg = str(e)
        try:
            logger.error("An error occurred during transcription: %s", error_msg, exc_info=True)
        except UnicodeError:
            logger.error("An error occurred during transcription (details suppressed due to encoding)")
            
        output_data = {"status": "error", "message": error_msg}
        
        # Write error result with robust encoding handling
        try:
            with open(args.output_json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=4)
        except UnicodeError:
            # Fallback: write with ASCII encoding
            with open(args.output_json_path, 'w', encoding='ascii') as f:
                json.dump(output_data, f, ensure_ascii=True, indent=4)
        sys.exit(1)

    # Write the successful result to the output JSON file
    try:
        with open(args.output_json_path, 'w', encoding='utf-8') as f:
            # Custom default handler for sets that might appear in word data
            def set_default(obj):
                if isinstance(obj, set):
                    return list(obj)
                raise TypeError

            json.dump(output_data, f, ensure_ascii=False, indent=4, default=set_default)
        try:
            logger.info("Successfully wrote results to %s", args.output_json_path)
        except UnicodeError:
            logger.info("Successfully wrote results to output file")
    except UnicodeError:
        # Fallback: write with ASCII encoding if UTF-8 fails
        try:
            with open(args.output_json_path, 'w', encoding='ascii') as f:
                def set_default(obj):
                    if isinstance(obj, set):
                        return list(obj)
                    raise TypeError
                json.dump(output_data, f, ensure_ascii=True, indent=4, default=set_default)
            logger.info("Successfully wrote results with ASCII encoding fallback")
        except Exception as e:
            logger.error("Failed to write output JSON: %s", e, exc_info=True)
            sys.exit(1)
    except Exception as e:
        logger.error("Failed to write output JSON: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()