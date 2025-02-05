import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from datetime import timedelta

import whisper
import numpy as np
from whisper.utils import get_writer
from modules import parser_args

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse command-line arguments
args = parser_args.parse_arguments()

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp
    """
    td = timedelta(seconds=seconds)
    hours = td.seconds//3600
    minutes = (td.seconds//60)%60
    seconds = td.seconds%60
    milliseconds = td.microseconds//1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def write_caption(segment: Dict[str, Any], file_handle: Any) -> None:
    """
    Write a single caption segment.
    
    Args:
        segment (Dict[str, Any]): Caption segment data
        file_handle (Any): File handle to write to
    """
    index = segment.get("id", 0) + 1
    start = format_timestamp(segment["start"])
    end = format_timestamp(segment["end"])
    text = segment["text"].strip()
    
    # Write to file in SRT format
    caption = f"{index}\n{start} --> {end}\n{text}\n\n"
    file_handle.write(caption)

def load_whisper_model(
    model_type: str, 
    device: str, 
    model_dir: Optional[str] = None
) -> whisper.Whisper:
    """
    Load the Whisper model with specified parameters.
    
    Args:
        model_type (str): Type of the Whisper model to load
        device (str): Device to run the model on ('cpu' or 'cuda')
        model_dir (str, optional): Directory where models are stored. 
            If None, uses the default from args.model_dir
    
    Returns:
        whisper.Whisper: Loaded Whisper model
    
    Raises:
        RuntimeError: If model loading fails
    """
    try:
        # Use provided model_dir or fall back to args.model_dir
        download_root = model_dir if model_dir else str(args.model_dir)
        model_path = Path(download_root)
        
        if not model_path.exists():
            logger.info("Creating model directory: %s", model_path)
            model_path.mkdir(parents=True, exist_ok=True)
            
        logger.info("Loading Whisper model: %s from %s", model_type, model_path)
        return whisper.load_model(model_type, device=device, download_root=str(model_path))
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model: {str(e)}")

def run_sub_gen(
    input_path: str, 
    output_name: str = "", 
    output_directory: str = "./",
    task: str = "translate",
    model_dir: Optional[str] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Generate subtitles for an audio file using Whisper.
    
    Args:
        input_path (str): Path to the input audio file
        output_name (str, optional): Name for the output subtitle file. Defaults to "".
        output_directory (str, optional): Directory to save subtitles. Defaults to "./".
        task (str, optional): Whisper task type ('transcribe' or 'translate'). Defaults to "translate".
        model_dir (str, optional): Custom directory for model files. 
            If None, uses the directory from command line args.
    
    Returns:
        Tuple[Dict[str, Any], str]: Tuple containing the transcription result and output filename
    
    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If subtitle generation fails
    """
    # Input validation
    if not input_path:
        raise ValueError("Input path cannot be empty")
    
    input_path = Path(input_path)
    if not input_path.exists():
        raise ValueError(f"Input file does not exist: {input_path}")
    
    if task not in ["transcribe", "translate"]:
        raise ValueError("Task must be either 'transcribe' or 'translate'")
    
    output_directory = Path(output_directory)
    if not output_directory.exists():
        output_directory.mkdir(parents=True, exist_ok=True)

    try:
        # Determine model type based on available RAM
        model_type = parser_args.set_model_by_ram(args.ram, args.language)
        
        # Load the model with optional custom model directory
        model = load_whisper_model(
            model_type=model_type,
            device=args.device,
            model_dir=model_dir
        )

        # Load audio
        logger.info("Loading audio file...")
        audio = whisper.load_audio(str(input_path))
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # Detect language if needed
        language = args.language
        if language is None and model.is_multilingual:
            logger.info("Detecting language...")
            _, probs = model.detect_language(mel)
            language = max(probs, key=probs.get)
            logger.info(f"Detected language: {language}")

        # Set up decoding options
        decode_options = {
            "fp16": args.fp16,
            "language": language,
            "task": task
        }

        # Process in segments with progress updates
        logger.info("Starting transcription process...")
        segments = []
        
        # Process in 30-second segments
        chunk_size = 30 * whisper.audio.SAMPLE_RATE
        for i in range(0, len(audio), chunk_size):
            chunk_end = min(i + chunk_size, len(audio))
            chunk = audio[i:chunk_end]
            chunk_mel = whisper.log_mel_spectrogram(chunk).to(model.device)
            
            # Transcribe chunk
            result = model.transcribe(chunk, **decode_options)
            
            # Calculate and show progress
            progress = min(1.0, chunk_end / len(audio))
            
            # Add segments with adjusted timestamps
            for seg in result["segments"]:
                seg["start"] += i / whisper.audio.SAMPLE_RATE
                seg["end"] += i / whisper.audio.SAMPLE_RATE
                text = seg["text"].strip()
                if text:  # Only show non-empty segments
                    logger.info("[%.2f%%] %s", progress * 100, text)
                segments.append(seg)

        result = {"segments": segments, "language": language}

        # Generate subtitle file
        logger.info("\nWriting subtitle file...")
        output_path = output_directory / f"{output_name}.srt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, segment in enumerate(result["segments"]):
                segment["id"] = idx
                write_caption(segment, f)
        
        logger.info("Subtitle file saved to: %s", output_path)
        return result, output_name

    except Exception as e:
        logger.error("Failed to generate subtitles: %s", str(e))
        raise RuntimeError(f"Subtitle generation failed: {str(e)}")

# Indicate that the subtitles generator module is loaded.
logger.info("Subtitles Generator Module Loaded")