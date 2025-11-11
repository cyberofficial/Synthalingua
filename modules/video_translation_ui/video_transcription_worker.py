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

# Worker script version for verification
WORKER_SCRIPT_VERSION = "1.2.6.3"  # Increment when making changes to verify correct version is running
print(f"[VideoWorker] INFO: Video transcription worker started (v{WORKER_SCRIPT_VERSION}) with UTF-8 encoding support")

# Log UTF-8 setup success
try:
    logger.info(f"Video transcription worker started (v{WORKER_SCRIPT_VERSION}) with UTF-8 encoding support")
except UnicodeError:
    # If even this fails, continue silently
    pass


def transcribe_with_model(model_source, model_size, device, model_dir, compute_type, audio_path, language, task, temperature=None, debug=False):
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
        temperature: Fixed temperature (0.0-1.0) or None for fallback
        debug: Enable debug output
        
    Returns:
        dict: Result with 'text', 'language', 'processing_time'
    """
    import time
    start_time = time.time()
    
    # VRAM monitoring before model load
    if debug and device == 'cuda':
        try:
            import torch
            if torch.cuda.is_available():
                allocated_before = torch.cuda.memory_allocated() / (1024**3)
                cached_before = torch.cuda.memory_reserved() / (1024**3)
                logger.debug(f"[DEBUG] VRAM before model load: {allocated_before:.2f}GB allocated, {cached_before:.2f}GB cached")
        except Exception as e:
            logger.debug(f"[DEBUG] Could not check VRAM: {e}")
    
    if model_source == "fasterwhisper":
        from modules.FasterWhisper import FasterWhisperModel
        
        logger.info(f"Loading FasterWhisper model: {model_size}")
        logger.info(f"Using device: {device}, compute_type: {compute_type}")
        if debug:
            logger.debug(f"[DEBUG] Model directory: {model_dir}")
            logger.debug(f"[DEBUG] Audio file size: {os.path.getsize(audio_path) / (1024*1024):.2f}MB")
        
        model = FasterWhisperModel(
            model=model_size,
            device=device,
            download_root=model_dir,
            compute_type=compute_type
        )
        
        if debug and device == 'cuda':
            try:
                import torch
                if torch.cuda.is_available():
                    allocated_after = torch.cuda.memory_allocated() / (1024**3)
                    cached_after = torch.cuda.memory_reserved() / (1024**3)
                    logger.debug(f"[DEBUG] VRAM after model load: {allocated_after:.2f}GB allocated, {cached_after:.2f}GB cached")
            except Exception as e:
                logger.debug(f"[DEBUG] Could not check VRAM after load: {e}")
        
        logger.info(f"Starting {task} of: {audio_path}")
        if language:
            logger.info(f"Using language: {language}")
        else:
            logger.info(f"Auto-detecting language")
        
        # Transcribe or translate
        # If temperature is None, use fallback temperatures (0.0, 0.2, 0.4, 0.6, 0.8)
        # If temperature is provided, use single fixed temperature
        temp_value = temperature if temperature is not None else (0.0, 0.2, 0.4, 0.6, 0.8)
        
        if debug:
            logger.debug(f"[DEBUG] FasterWhisper: Starting transcription with temperature: {temp_value}")
            logger.debug(f"[DEBUG] FasterWhisper: Task={task}, Language={language or 'auto-detect'}")
        
        result_text = model.transcribe(
            file_path=audio_path,
            language=language,
            task=task,
            condition_on_previous_text=True,
            temperature=temp_value,
            compression_ratio_threshold=args.compression_ratio_threshold,
            log_prob_threshold=None,
            no_speech_threshold=0.6
        )
        
        if debug:
            logger.debug(f"[DEBUG] FasterWhisper: Transcription returned {len(result_text)} characters")
        
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
            condition_on_previous_text=True,
            temperature=0.0,
            compression_ratio_threshold=args.compression_ratio_threshold,
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
        # If temperature is None, use fallback temperatures (0.0, 0.2, 0.4, 0.6, 0.8)
        # If temperature is provided, use single fixed temperature
        temp_value = temperature if temperature is not None else (0.0, 0.2, 0.4, 0.6, 0.8)
        
        result_text = model.transcribe(
            file_path=audio_path,
            language=language,
            task=task,
            condition_on_previous_text=True,
            temperature=temp_value,
            compression_ratio_threshold=args.compression_ratio_threshold,
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
    parser.add_argument("--temperature", type=float, default=None, help="Fixed temperature value (0.0-1.0). If not set, uses multiple fallback temperatures.")
    parser.add_argument("--compression_ratio_threshold", type=float, default=2.4, help="Compression ratio threshold for filtering low-quality transcriptions.")
    
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
                        
                        if args.debug:
                            logger.debug(f"[DEBUG] Model source: FasterWhisper, Size: {args.model_size}")
                            logger.debug(f"[DEBUG] Device: {args.device}, Compute type: {args.compute_type}")
                            logger.debug(f"[DEBUG] Model directory: {args.model_dir}")
                            
                            # VRAM before model load
                            if args.device == 'cuda':
                                try:
                                    import torch
                                    if torch.cuda.is_available():
                                        allocated = torch.cuda.memory_allocated() / (1024**3)
                                        cached = torch.cuda.memory_reserved() / (1024**3)
                                        logger.debug(f"[DEBUG] VRAM before model load: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                                except Exception as e:
                                    logger.debug(f"[DEBUG] Could not check VRAM before load: {e}")
                        
                        model = FasterWhisperModel(
                            model=args.model_size,
                            device=args.device,
                            download_root=args.model_dir,
                            compute_type=args.compute_type
                        )
                        
                        if args.debug:
                            logger.debug(f"[DEBUG] FasterWhisper model loaded successfully")
                            
                            # VRAM after model load
                            if args.device == 'cuda':
                                try:
                                    import torch
                                    if torch.cuda.is_available():
                                        allocated = torch.cuda.memory_allocated() / (1024**3)
                                        cached = torch.cuda.memory_reserved() / (1024**3)
                                        logger.debug(f"[DEBUG] VRAM after model load: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                                except Exception as e:
                                    logger.debug(f"[DEBUG] Could not check VRAM after load: {e}")
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
                    if args.debug:
                        logger.debug(f"[DEBUG] Starting segment-by-segment processing for {len(speech_regions)} regions")
                        logger.debug(f"[DEBUG] Model loaded: {args.model_source}/{args.model_size}, Device: {args.device}")
                    
                    for i, region in enumerate(speech_regions):
                        region_start = region['start']
                        region_end = region['end']
                        
                        if args.debug:
                            logger.debug(f"[DEBUG] ===== Processing segment {i+1}/{len(speech_regions)} =====")
                            logger.debug(f"[DEBUG] Region: {region_start:.2f}s - {region_end:.2f}s (duration: {region_end - region_start:.2f}s)")
                            
                            # Check VRAM before each segment
                            if args.device == 'cuda':
                                try:
                                    import torch
                                    if torch.cuda.is_available():
                                        allocated = torch.cuda.memory_allocated() / (1024**3)
                                        cached = torch.cuda.memory_reserved() / (1024**3)
                                        free, total = torch.cuda.mem_get_info()
                                        free_gb = free / (1024**3)
                                        logger.debug(f"[DEBUG] VRAM before segment {i+1}: {allocated:.2f}GB allocated, {cached:.2f}GB cached, {free_gb:.2f}GB free")
                                except Exception as e:
                                    logger.debug(f"[DEBUG] Could not check VRAM: {e}")
                        
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
                            # Use fixed temperature if provided, otherwise None for fallback
                            temp_value = args.temperature if args.temperature is not None else 0.0
                            
                            if args.debug:
                                logger.debug(f"[DEBUG] Transcribing segment {i+1} audio: {os.path.getsize(region_audio_path) / 1024:.2f}KB")
                                logger.debug(f"[DEBUG] Temperature: {temp_value if args.temperature is not None else '(0.0, 0.2, 0.4, 0.6, 0.8)'}")
                            
                            try:
                                result_text = model.transcribe(
                                    file_path=region_audio_path,
                                    language=args.language,
                                    task=args.task,  # "translate" = translate to English, "transcribe" = source language
                                    condition_on_previous_text=True,
                                    temperature=temp_value if args.temperature is not None else (0.0, 0.2, 0.4, 0.6, 0.8),
                                    compression_ratio_threshold=args.compression_ratio_threshold,
                                    log_prob_threshold=None,
                                    no_speech_threshold=0.6
                                )
                                
                                if args.debug:
                                    logger.debug(f"[DEBUG] Segment {i+1} transcription returned {len(result_text)} characters")
                            
                            except Exception as transcribe_error:
                                logger.error(f"[ERROR] Transcription failed for segment {i+1}/{len(speech_regions)}: {transcribe_error}")
                                if args.debug:
                                    import traceback
                                    logger.debug(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
                                raise
                            
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
                                    if args.debug:
                                        logger.debug(f"[DEBUG] Cleaned up temp audio file for segment {i+1}")
                                except Exception as cleanup_error:
                                    if args.debug:
                                        logger.debug(f"[DEBUG] Failed to cleanup temp file: {cleanup_error}")
                            
                            # VRAM check after segment processing
                            if args.debug and args.device == 'cuda':
                                try:
                                    import torch
                                    if torch.cuda.is_available():
                                        allocated = torch.cuda.memory_allocated() / (1024**3)
                                        cached = torch.cuda.memory_reserved() / (1024**3)
                                        logger.debug(f"[DEBUG] VRAM after segment {i+1}: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                                        
                                        # Force CUDA cache clear every few segments to prevent accumulation
                                        if (i + 1) % 3 == 0:
                                            logger.debug(f"[DEBUG] Clearing CUDA cache after segment {i+1}")
                                            torch.cuda.empty_cache()
                                            torch.cuda.synchronize()
                                            allocated_after = torch.cuda.memory_allocated() / (1024**3)
                                            cached_after = torch.cuda.memory_reserved() / (1024**3)
                                            logger.debug(f"[DEBUG] VRAM after cache clear: {allocated_after:.2f}GB allocated, {cached_after:.2f}GB cached")
                                except Exception as e:
                                    logger.debug(f"[DEBUG] Could not check/clear VRAM: {e}")
                    
                    processing_time = time.time() - start_time
                    
                    if args.debug:
                        logger.debug(f"[DEBUG] ===== Post-processing phase started =====")
                        logger.debug(f"[DEBUG] Total segments processed: {len(all_segments)}")
                        logger.debug(f"[DEBUG] Total processing time: {processing_time:.2f}s")
                        
                        # VRAM check before text combination
                        if args.device == 'cuda':
                            try:
                                import torch
                                if torch.cuda.is_available():
                                    allocated = torch.cuda.memory_allocated() / (1024**3)
                                    cached = torch.cuda.memory_reserved() / (1024**3)
                                    logger.debug(f"[DEBUG] VRAM before text combination: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                            except Exception as e:
                                logger.debug(f"[DEBUG] Could not check VRAM: {e}")
                    
                    # Combine all segment text with error handling
                    try:
                        if args.debug:
                            logger.debug(f"[DEBUG] Combining text from {len(all_segments)} segments...")
                            total_chars = sum(len(seg['text']) for seg in all_segments)
                            logger.debug(f"[DEBUG] Total characters to combine: {total_chars}")
                        
                        full_text = ' '.join([seg['text'] for seg in all_segments])
                        
                        if args.debug:
                            logger.debug(f"[DEBUG] Text combination complete: {len(full_text)} characters")
                    except Exception as text_error:
                        logger.error(f"[ERROR] Failed to combine segment text: {text_error}")
                        if args.debug:
                            import traceback
                            logger.debug(f"[DEBUG] Text combination traceback:\n{traceback.format_exc()}")
                        raise
                    
                    # Detect language from first segment or use provided
                    if args.debug:
                        logger.debug(f"[DEBUG] Starting language detection phase...")
                        logger.debug(f"[DEBUG] Provided language: {args.language or 'None (auto-detect)'}")
                        logger.debug(f"[DEBUG] Model object exists: {model is not None}")
                    
                    detected_language = args.language
                    if not detected_language and model and all_segments:
                        try:
                            if args.debug:
                                logger.debug(f"[DEBUG] Attempting auto language detection...")
                                logger.debug(f"[DEBUG] Audio path: {args.audio_path}")
                                logger.debug(f"[DEBUG] Model has detect_language method: {hasattr(model, 'detect_language')}")
                            
                            language_probs = model.detect_language(args.audio_path)
                            
                            if args.debug:
                                logger.debug(f"[DEBUG] Language detection returned: {language_probs}")
                            
                            if language_probs:
                                detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                                if args.debug:
                                    logger.debug(f"[DEBUG] Detected language: {detected_language}")
                        except Exception as lang_error:
                            logger.warning(f"[WARNING] Language detection failed: {lang_error}")
                            if args.debug:
                                import traceback
                                logger.debug(f"[DEBUG] Language detection traceback:\n{traceback.format_exc()}")
                            detected_language = "unknown"
                    
                    if args.debug:
                        logger.debug(f"[DEBUG] Creating output data structure...")
                        logger.debug(f"[DEBUG] Full text length: {len(full_text)} chars")
                        logger.debug(f"[DEBUG] Language: {detected_language or 'unknown'}")
                        logger.debug(f"[DEBUG] Number of timestamp segments: {len(all_segments)}")
                        
                        # VRAM check before creating large dict
                        if args.device == 'cuda':
                            try:
                                import torch
                                if torch.cuda.is_available():
                                    allocated = torch.cuda.memory_allocated() / (1024**3)
                                    cached = torch.cuda.memory_reserved() / (1024**3)
                                    logger.debug(f"[DEBUG] VRAM before output_data creation: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
                            except Exception as e:
                                logger.debug(f"[DEBUG] Could not check VRAM: {e}")
                    
                    try:
                        output_data = {
                            "status": "success",
                            "text": full_text,
                            "language": detected_language or "unknown",
                            "processing_time": processing_time,
                            "timestamps": all_segments
                        }
                        
                        if args.debug:
                            logger.debug(f"[DEBUG] output_data structure created successfully")
                    except Exception as data_error:
                        logger.error(f"[ERROR] Failed to create output_data: {data_error}")
                        if args.debug:
                            import traceback
                            logger.debug(f"[DEBUG] output_data creation traceback:\n{traceback.format_exc()}")
                        raise
                    
                    logger.info(f"Processed {len(all_segments)} segments in {processing_time:.2f}s")
                    
                    if args.debug:
                        logger.debug(f"[DEBUG] Post-processing complete, preparing to write JSON...")
                        logger.debug(f"[DEBUG] Skipping model cleanup - will let OS reclaim memory on process exit")
                
                finally:
                    # NO MODEL CLEANUP - Subprocess pattern relies on OS to reclaim all resources
                    # When subprocess exits, OS automatically frees ALL memory (RAM + VRAM)
                    # Attempting any cleanup causes crashes in PyInstaller frozen executables
                    
                    if args.debug:
                        logger.debug(f"[DEBUG] Finally block - skipping all cleanup (subprocess will exit)")
        
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
                task=args.task,
                temperature=args.temperature,
                debug=args.debug
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
    if args.debug:
        logger.debug(f"[DEBUG] Preparing to write JSON output to: {args.output_json_path}")
        logger.debug(f"[DEBUG] output_data keys: {list(output_data.keys())}")
        logger.debug(f"[DEBUG] output_data status: {output_data.get('status')}")
        
        # Final VRAM check before JSON write
        if args.device == 'cuda':
            try:
                import torch
                if torch.cuda.is_available():
                    allocated = torch.cuda.memory_allocated() / (1024**3)
                    cached = torch.cuda.memory_reserved() / (1024**3)
                    logger.debug(f"[DEBUG] VRAM before JSON write: {allocated:.2f}GB allocated, {cached:.2f}GB cached")
            except Exception as e:
                logger.debug(f"[DEBUG] Could not check VRAM: {e}")
    
    try:
        if args.debug:
            logger.debug(f"[DEBUG] Opening JSON file for writing...")
        
        with open(args.output_json_path, 'w', encoding='utf-8') as f:
            if args.debug:
                logger.debug(f"[DEBUG] File opened, writing JSON data...")
            
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
            if args.debug:
                logger.debug(f"[DEBUG] JSON data written successfully")
        
        try:
            logger.info("Successfully wrote results to %s", args.output_json_path)
            if args.debug:
                file_size = os.path.getsize(args.output_json_path)
                logger.debug(f"[DEBUG] Output file size: {file_size / 1024:.2f}KB")
                logger.debug(f"[DEBUG] Exiting immediately - no cleanup needed (subprocess pattern)")
        except UnicodeError:
            logger.info("Successfully wrote results to output file")
        
        # Exit immediately - OS will reclaim all subprocess resources automatically
        os._exit(0)
    
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
