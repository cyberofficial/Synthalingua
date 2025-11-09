"""
Video Transcription Worker Module

This script is designed to be called as a child process from the video transcription manager.
Its sole purpose is to perform a single transcription/translation task using a
specified Whisper model and audio file.

It takes command-line arguments to define the task, loads the model, runs the
transcription, and writes the output (or any errors) to a specified JSON file.
By running in a separate process, it guarantees that all VRAM and RAM used by
the model are fully released upon completion, preventing memory caching issues.

Usage:
python video_transcription_worker.py --audio_path <path> --output_json_path <path> --model_source <source> ...
"""

# CRITICAL: Set up UTF-8 encoding BEFORE any other imports
import sys
import os

# Add parent directory to path so we can import modules
# This ensures the worker can find modules.BaseWhisper, modules.FasterWhisper, etc.
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(script_dir))  # Go up to Synthalingua_Main
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Force UTF-8 encoding for all operations
if sys.platform.startswith('win'):
    # Set environment variables first
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    
    # Try to reconfigure stdout/stderr for UTF-8 if possible
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        # Fallback: ignore if reconfigure not available or fails
        pass

# Now import other modules
import argparse
import json
import logging
from pathlib import Path

# Configure basic logging with UTF-8 support and error handling
try:
    logging.basicConfig(
        level=logging.INFO, 
        format='[VideoWorker] %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
except UnicodeError:
    # Fallback logging configuration if UTF-8 fails
    logging.basicConfig(
        level=logging.INFO, 
        format='[VideoWorker] %(levelname)s: %(message)s'
    )

logger = logging.getLogger(__name__)

# Log UTF-8 setup success
try:
    logger.info("Video transcription worker started with UTF-8 encoding support")
except UnicodeError:
    # If even this fails, continue silently
    pass


def transcribe_with_model(model_source, model_size, device, model_dir, compute_type, audio_path, language, task):
    """
    Load the appropriate model and perform transcription or translation.
    
    Args:
        model_source: Model engine to use (whisper, fasterwhisper, openvino)
        model_size: Model size (tiny, base, small, medium, large-v2, large-v3)
        device: Device to use (cpu, cuda)
        model_dir: Directory containing models
        compute_type: Compute type for FasterWhisper/OpenVINO
        audio_path: Path to audio file
        language: Language code (None for auto-detect)
        task: Task type (transcribe or translate)
        
    Returns:
        dict: Result with 'text', 'language', 'processing_time'
    """
    import time
    start_time = time.time()
    
    if model_source == "fasterwhisper":
        from modules.FasterWhisper import FasterWhisperModel
        
        logger.info(f"Loading FasterWhisper model: {model_size}")
        logger.info(f"Using device: {device}, compute_type: {compute_type}")
        
        model = FasterWhisperModel(
            model=model_size,
            device=device,
            download_root=model_dir,
            compute_type=compute_type
        )
        
        logger.info(f"Starting {task} of: {audio_path}")
        if language:
            logger.info(f"Using language: {language}")
        else:
            logger.info(f"Auto-detecting language")
        
        # Transcribe or translate
        result_text = model.transcribe(
            file_path=audio_path,
            language=language,
            task=task,
            condition_on_previous_text=False,
            temperature=0.0,  # Single temperature, no fallback
            compression_ratio_threshold=None,
            log_prob_threshold=None,
            no_speech_threshold=0.6
        )
        
        # Detect language if not provided
        detected_language = language
        if not detected_language:
            try:
                language_probs = model.detect_language(audio_path)
                if language_probs:
                    detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                    logger.info(f"Detected language: {detected_language}")
            except:
                detected_language = "unknown"
        
        processing_time = time.time() - start_time
        logger.info(f"{task.capitalize()} complete in {processing_time:.2f}s")
        
        return {
            "text": result_text.strip(),
            "language": detected_language or "unknown",
            "processing_time": processing_time
        }
        
    elif model_source == "openvino":
        from modules.OpenVINOWhisper import OpenVINOWhisperModel
        
        logger.info(f"Loading OpenVINO model: {model_size}")
        logger.info(f"Using device: {device}, compute_type: {compute_type}")
        
        model = OpenVINOWhisperModel(
            model=model_size,
            device=device,
            download_root=model_dir,
            compute_type=compute_type
        )
        
        logger.info(f"Starting {task} of: {audio_path}")
        if language:
            logger.info(f"Using language: {language}")
        else:
            logger.info(f"Auto-detecting language")
        
        # Transcribe or translate
        result_text = model.transcribe(
            file_path=audio_path,
            language=language,
            task=task,
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=None,
            log_prob_threshold=None,
            no_speech_threshold=0.6
        )
        
        # Detect language if not provided
        detected_language = language
        if not detected_language:
            try:
                language_probs = model.detect_language(audio_path)
                if language_probs:
                    detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                    logger.info(f"Detected language: {detected_language}")
            except:
                detected_language = "unknown"
        
        processing_time = time.time() - start_time
        logger.info(f"{task.capitalize()} complete in {processing_time:.2f}s")
        
        return {
            "text": result_text.strip(),
            "language": detected_language or "unknown",
            "processing_time": processing_time
        }
        
    else:  # Default to standard Whisper
        from modules.BaseWhisper import BaseWhisperModel
        
        logger.info(f"Loading BaseWhisper model: {model_size}")
        logger.info(f"Using device: {device}")
        
        model = BaseWhisperModel(
            model=model_size,
            device=device,
            download_root=model_dir
        )
        
        logger.info(f"Starting {task} of: {audio_path}")
        if language:
            logger.info(f"Using language: {language}")
        else:
            logger.info(f"Auto-detecting language")
        
        # Transcribe or translate
        result_text = model.transcribe(
            file_path=audio_path,
            language=language,
            task=task,
            condition_on_previous_text=False,
            temperature=0.0,
            compression_ratio_threshold=None,
            log_prob_threshold=None,
            no_speech_threshold=0.6
        )
        
        # Detect language if not provided
        detected_language = language
        if not detected_language:
            try:
                language_probs = model.detect_language(audio_path)
                if language_probs:
                    detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                    logger.info(f"Detected language: {detected_language}")
            except:
                detected_language = "unknown"
        
        processing_time = time.time() - start_time
        logger.info(f"{task.capitalize()} complete in {processing_time:.2f}s")
        
        return {
            "text": result_text.strip(),
            "language": detected_language or "unknown",
            "processing_time": processing_time
        }


def main():
    """Main execution block for the worker process."""
    parser = argparse.ArgumentParser(description="Video Transcription Worker")
    parser.add_argument("--audio_path", required=True, type=str, help="Path to the audio file to process.")
    parser.add_argument("--output_json_path", required=True, type=str, help="Path to write the resulting JSON output.")
    parser.add_argument("--model_source", required=True, type=str, help="Model source (whisper, fasterwhisper, openvino).")
    parser.add_argument("--model_size", required=True, type=str, help="Whisper model size (e.g., 'base', 'large-v3').")
    parser.add_argument("--device", required=True, type=str, help="Device to run on ('cpu' or 'cuda').")
    parser.add_argument("--compute_type", required=True, type=str, help="Compute type for FasterWhisper/OpenVINO models.")
    parser.add_argument("--model_dir", required=True, type=str, help="Directory to load models from.")
    parser.add_argument("--language", type=str, default=None, help="Language code (optional, will auto-detect if not provided).")
    parser.add_argument("--task", type=str, default="transcribe", choices=["transcribe", "translate"], help="Task type (transcribe or translate).")
    parser.add_argument("--debug", action='store_true', help="Enable debug output.")
    parser.add_argument("--enable_silence_detection", action='store_true', help="Enable silence detection for segment-level processing.")
    parser.add_argument("--silence_threshold_db", type=float, default=-50.0, help="Silence threshold in dB.")
    parser.add_argument("--min_silence_duration", type=float, default=0.1, help="Minimum silence duration in seconds.")
    parser.add_argument("--chunk_start_time", type=float, default=0.0, help="Chunk start time for timestamp calculation.")
    
    args = parser.parse_args()
    
    # Set logging level based on debug flag
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled - verbose output activated")
    
    try:
        logger.info(f"Starting video transcription worker: task={args.task}, model={args.model_source}/{args.model_size}, silence_detection={args.enable_silence_detection}")
        
        if args.enable_silence_detection:
            # Process with silence detection - returns list of timestamped segments
            from modules.video_translation_ui.silence_detector import SilenceDetector
            import tempfile
            import time
            
            logger.info("Initializing silence detector...")
            silence_detector = SilenceDetector(
                silence_threshold_db=args.silence_threshold_db,
                min_silence_duration=args.min_silence_duration,
                min_speech_duration=0.1
            )
            
            # Detect speech regions
            logger.info("Detecting speech regions...")
            regions = silence_detector.detect_regions(args.audio_path)
            speech_regions = [r for r in regions if r['type'] == 'speech']
            
            logger.info(f"Found {len(speech_regions)} speech regions")
            
            if not speech_regions:
                # No speech detected
                output_data = {
                    "status": "success",
                    "text": "",
                    "language": args.language or "unknown",
                    "processing_time": 0.0,
                    "timestamps": []
                }
            else:
                # Process all speech regions with ONE model instance (efficiency!)
                start_time = time.time()
                all_segments = []
                model = None
                
                try:
                    # Load model ONCE
                    if args.model_source.lower() == "fasterwhisper":
                        from modules.FasterWhisper import FasterWhisperModel
                        logger.info(f"Loading FasterWhisper model: {args.model_size}")
                        model = FasterWhisperModel(
                            model=args.model_size,
                            device=args.device,
                            download_root=args.model_dir,
                            compute_type=args.compute_type
                        )
                    elif args.model_source.lower() == "openvino":
                        from modules.OpenVINOWhisper import OpenVINOWhisperModel
                        logger.info(f"Loading OpenVINO model: {args.model_size}")
                        model = OpenVINOWhisperModel(
                            model=args.model_size,
                            device=args.device,
                            download_root=args.model_dir,
                            compute_type=args.compute_type
                        )
                    else:  # whisper
                        from modules.BaseWhisper import BaseWhisperModel
                        logger.info(f"Loading BaseWhisper model: {args.model_size}")
                        model = BaseWhisperModel(
                            model=args.model_size,
                            device=args.device,
                            download_root=args.model_dir
                        )
                    
                    # Process each speech region with the SAME model instance
                    # For task="translate", we translate each segment immediately and emit incrementally
                    for i, region in enumerate(speech_regions):
                        region_start = region['start']
                        region_end = region['end']
                        
                        # Extract speech region to temporary file
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                            region_audio_path = tmp_file.name
                        
                        try:
                            success = silence_detector.extract_speech_region(
                                args.audio_path,
                                region_audio_path,
                                region_start,
                                region_end
                            )
                            
                            if not success:
                                logger.warning(f"Failed to extract speech region {i}")
                                continue
                            
                            # Calculate absolute timestamps
                            absolute_start = args.chunk_start_time + region_start
                            absolute_end = args.chunk_start_time + region_end
                            
                            # For translate task, we need to actually translate to English
                            # For transcribe task, we just transcribe in source language
                            result_text = model.transcribe(
                                file_path=region_audio_path,
                                language=args.language,
                                task=args.task,  # "translate" = translate to English, "transcribe" = source language
                                condition_on_previous_text=False,
                                temperature=0.0,
                                compression_ratio_threshold=None,
                                log_prob_threshold=None,
                                no_speech_threshold=0.6
                            )
                            
                            transcription_text = result_text.strip()
                            if transcription_text:
                                segment_data = {
                                    'start': absolute_start,
                                    'end': absolute_end,
                                    'text': transcription_text,
                                    'translation': ''
                                }
                                
                                all_segments.append(segment_data)
                                
                                # For translate task, emit each segment IMMEDIATELY to stdout for incremental updates
                                # Parent process can parse these and update UI in real-time
                                if args.task == "translate":
                                    import json
                                    import sys
                                    segment_event = {
                                        'type': 'segment',
                                        'index': i,
                                        'total': len(speech_regions),
                                        'start': absolute_start,
                                        'end': absolute_end,
                                        'text': transcription_text
                                    }
                                    # Write to stdout with special marker for parent to parse
                                    print(f"SEGMENT_EVENT:{json.dumps(segment_event)}", flush=True)
                                
                                logger.debug(f"Segment {i+1}/{len(speech_regions)}: {absolute_start:.2f}s - {absolute_end:.2f}s")
                        
                        finally:
                            # Clean up temp file
                            if os.path.exists(region_audio_path):
                                try:
                                    os.remove(region_audio_path)
                                except:
                                    pass
                    
                    processing_time = time.time() - start_time
                    
                    # Combine all segment text
                    full_text = ' '.join([seg['text'] for seg in all_segments])
                    
                    # Detect language from first segment or use provided
                    detected_language = args.language
                    if not detected_language and model and all_segments:
                        try:
                            language_probs = model.detect_language(args.audio_path)
                            if language_probs:
                                detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                        except:
                            detected_language = "unknown"
                    
                    output_data = {
                        "status": "success",
                        "text": full_text,
                        "language": detected_language or "unknown",
                        "processing_time": processing_time,
                        "timestamps": all_segments
                    }
                    
                    logger.info(f"Processed {len(all_segments)} segments in {processing_time:.2f}s")
                
                finally:
                    # Model cleanup happens automatically when subprocess exits
                    pass
        
        else:
            # Process entire audio file as single transcription (original behavior)
            result = transcribe_with_model(
                model_source=args.model_source.lower(),
                model_size=args.model_size,
                device=args.device,
                model_dir=args.model_dir,
                compute_type=args.compute_type,
                audio_path=args.audio_path,
                language=args.language if args.language else None,
                task=args.task
            )
            
            # Flatten result into output_data (don't nest under "result" key)
            output_data = {"status": "success", **result}
        
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
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        try:
            logger.info("Successfully wrote results to %s", args.output_json_path)
        except UnicodeError:
            logger.info("Successfully wrote results to output file")
    except UnicodeError:
        # Fallback: write with ASCII encoding if UTF-8 fails
        try:
            with open(args.output_json_path, 'w', encoding='ascii') as f:
                json.dump(output_data, f, ensure_ascii=True, indent=4)
            logger.info("Successfully wrote results with ASCII encoding fallback")
        except Exception as e:
            logger.error("Failed to write output JSON: %s", e, exc_info=True)
            sys.exit(1)
    except Exception as e:
        logger.error("Failed to write output JSON: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
