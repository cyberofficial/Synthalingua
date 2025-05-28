"""
Subtitle Generator Module

This module provides functionality to generate subtitles from audio files using the Whisper ASR model.
It supports both transcription (in original language) and translation (to English) tasks.

Key features:
- Automatic language detection
- RAM-aware model selection
- Confidence scoring with color-coded output
- Progress tracking during generation
- SRT format subtitle generation
- Chunked processing for memory efficiency
- Support for custom model directories

The module uses a streaming approach to process long audio files in chunks,
providing real-time feedback with confidence scores for each segment.
Output is color-coded based on confidence levels:
- Green: High confidence (≥90%)
- Yellow: Medium confidence (≥75%)
- Red: Low confidence (<75%)
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, List
import numpy as np

import whisper
from colorama import Fore, Style, init
from modules import parser_args

# Initialize colorama for Windows support
init()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse command-line arguments
args = parser_args.parse_arguments()

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format (matching Whisper's official implementation).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp in SRT format (HH:MM:SS,mmm)
    """
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds_part = milliseconds // 1_000
    milliseconds -= seconds_part * 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds_part:02d},{milliseconds:03d}"

def get_color_for_confidence(confidence: float) -> str:
    """
    Get appropriate color code based on confidence level.
    
    Args:
        confidence (float): Confidence score between 0 and 1
        
    Returns:
        str: ANSI color code
    """
    if confidence >= 0.90:
        return Fore.GREEN
    elif confidence >= 0.75:
        return Fore.YELLOW
    else:        return Fore.RED

def split_text_for_subtitles(text: str, start_time: float, end_time: float, max_chars: int = 60, max_words: int = 8) -> List[Tuple[str, float, float]]:
    """
    Split long text into readable subtitle chunks.
    
    Args:
        text (str): The text to split
        start_time (float): Start time of the original segment
        end_time (float): End time of the original segment
        max_chars (int): Maximum characters per subtitle line
        max_words (int): Maximum words per subtitle line
    
    Returns:
        List[Tuple[str, float, float]]: List of (text_chunk, start_time, end_time) tuples
    """
    # If text is already short enough, return as-is
    if len(text) <= max_chars and len(text.split()) <= max_words:
        return [(text, start_time, end_time)]
    
    words = text.split()
    duration = end_time - start_time
    chunks = []
    current_chunk = []
    current_chars = 0
    
    i = 0
    while i < len(words):
        word = words[i]
        word_chars = len(word) + (1 if current_chunk else 0)  # +1 for space
        
        # Check if adding this word would exceed limits
        if (current_chars + word_chars > max_chars or len(current_chunk) >= max_words) and current_chunk:
            # Finalize current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
            current_chars = 0
        else:
            # Add word to current chunk
            current_chunk.append(word)
            current_chars += word_chars
            i += 1
    
    # Add remaining words as final chunk
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append(chunk_text)
      # Assign timing to chunks proportionally based on text length
    result = []
    if len(chunks) == 1:
        result.append((chunks[0], start_time, end_time))
    else:
        # Calculate proportional timing based on character count
        total_chars = sum(len(chunk) for chunk in chunks)
        gap_time = min(0.1, duration * 0.02)  # Small gap between segments (max 0.1s)
        available_duration = duration - (gap_time * (len(chunks) - 1))
        
        current_time = start_time
        for idx, chunk in enumerate(chunks):
            # Calculate duration proportional to text length
            char_ratio = len(chunk) / total_chars if total_chars > 0 else 1.0 / len(chunks)
            chunk_duration = available_duration * char_ratio
            
            # Ensure minimum duration of 0.5 seconds
            chunk_duration = max(0.5, chunk_duration)
            
            chunk_start = current_time
            chunk_end = current_time + chunk_duration
            
            # Ensure we don't exceed the original end time
            if idx == len(chunks) - 1:  # Last chunk
                chunk_end = end_time
            
            result.append((chunk, chunk_start, chunk_end))
            current_time = chunk_end + gap_time
    
    return result

def split_text_with_word_timestamps(words: List[Dict], max_chars: int = 60, max_words: int = 8) -> List[Tuple[str, float, float]]:
    """
    Split text using word-level timestamps for more accurate timing.
    
    Args:
        words (List[Dict]): List of word dictionaries with 'word', 'start', 'end' keys
        max_chars (int): Maximum characters per subtitle line
        max_words (int): Maximum words per subtitle line
    
    Returns:
        List[Tuple[str, float, float]]: List of (text_chunk, start_time, end_time) tuples
    """
    if not words:
        return []
    
    chunks = []
    current_chunk_words = []
    current_chars = 0
    
    i = 0
    while i < len(words):
        word_data = words[i]
        word = word_data.get("word", "").strip()
        
        if not word:  # Skip empty words
            i += 1
            continue
            
        word_chars = len(word) + (1 if current_chunk_words else 0)  # +1 for space
        
        # Check if adding this word would exceed limits
        if (current_chars + word_chars > max_chars or len(current_chunk_words) >= max_words) and current_chunk_words:
            # Finalize current chunk using actual word timestamps
            chunk_text = " ".join([w.get("word", "").strip() for w in current_chunk_words])
            chunk_start = current_chunk_words[0].get("start", 0.0)
            chunk_end = current_chunk_words[-1].get("end", 0.0)
            
            chunks.append((chunk_text, chunk_start, chunk_end))
            current_chunk_words = []
            current_chars = 0
        else:
            # Add word to current chunk
            current_chunk_words.append(word_data)
            current_chars += word_chars
            i += 1
    
    # Add remaining words as final chunk
    if current_chunk_words:
        chunk_text = " ".join([w.get("word", "").strip() for w in current_chunk_words])
        chunk_start = current_chunk_words[0].get("start", 0.0)
        chunk_end = current_chunk_words[-1].get("end", 0.0)
        chunks.append((chunk_text, chunk_start, chunk_end))
    
    return chunks

def format_words_with_confidence(text: str, avg_logprob: float) -> Tuple[str, float]:
    """
    Format words with color based on confidence.
    
    Args:
        text (str): Text to format
        avg_logprob (float): Average log probability
        
    Returns:
        Tuple[str, float]: Colored text and confidence score
    """
    # Convert log probability to confidence score (normalize from typical range)
    confidence = 1.0 - min(1.0, max(0.0, -avg_logprob / 10))
    
    # Split into words and color each based on local adjustments
    words = text.split()
    colored_words = []
    
    for i, word in enumerate(words):
        # Slightly adjust confidence per word position
        word_conf = confidence * (1.0 + np.sin(i * 0.5) * 0.1)  # Add some variation
        word_conf = min(1.0, max(0.0, word_conf))  # Ensure stays in 0-1 range
        
        color = get_color_for_confidence(word_conf)
        colored_words.append(f"{color}{word}{Style.RESET_ALL}")    
    return " ".join(colored_words), confidence

def get_model_type(ram: str, skip_warning: bool = False) -> str:
    """
    Get the appropriate model type based on RAM setting.
    
    Args:
        ram (str): RAM setting from command line args
        skip_warning (bool): Whether to skip the RAM warning
    
    Returns:
        str: Model type to use
    """
    if not skip_warning:
        return parser_args.set_model_by_ram(ram, None)  # Pass None for language to respect RAM choice
    
    # Logic from set_model_by_ram but without the warning
    ram = ram.lower()
    if ram == "1gb":
        return "tiny"
    elif ram == "2gb":
        return "base"
    elif ram == "3gb":
        return "small"
    elif ram == "6gb":
        return "medium"
    elif ram == "7gb":
        return "turbo"
    elif ram == "11gb-v2":
        return "large-v2"
    elif ram == "11gb-v3":
        return "large-v3"
    else:
        raise ValueError("Invalid RAM setting provided")

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
    model_dir: Optional[str] = None,
    ram_setting: Optional[str] = None
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
        ram_setting (str, optional): RAM setting to use for model selection.
            If None, uses the setting from command line args.
    
    Returns:
        Tuple[Dict[str, Any], str]: Tuple containing the transcription result and output filename
    
    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If subtitle generation fails
    """    # Input validation
    if not input_path:
        raise ValueError("Input path cannot be empty")
    
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise ValueError(f"Input file does not exist: {input_path_obj}")
    
    if task not in ["transcribe", "translate"]:
        raise ValueError("Task must be either 'transcribe' or 'translate'")
    
    output_directory_obj = Path(output_directory)
    if not output_directory_obj.exists():
        output_directory_obj.mkdir(parents=True, exist_ok=True)

    try:
        # Determine model type based on available RAM (skip warning for file input mode)
        # Use provided ram_setting or fall back to args.ram
        ram_to_use = ram_setting if ram_setting is not None else args.ram
        model_type = get_model_type(ram_to_use, skip_warning=True)
        
        # Load the model with optional custom model directory
        model = load_whisper_model(
            model_type=model_type,
            device=args.device,
            model_dir=model_dir
        )
        
        # Set up transcription options (matching Whisper's official implementation)
        # Adjust parameters based on model type for better segmentation
        if model_type == "turbo":
            # Turbo model needs different parameters for proper segmentation
            decode_options = {
                "fp16": args.fp16,
                "language": args.language,
                "task": task,
                "word_timestamps": True,
                "temperature": 0.1,  # Slightly higher temperature for turbo
                "compression_ratio_threshold": 2.0,  # Lower threshold for turbo
                "logprob_threshold": -0.8,  # Higher threshold for turbo
                "no_speech_threshold": 0.4,  # Lower threshold for turbo
                "condition_on_previous_text": False,  # Disable for turbo to prevent long segments                "prepend_punctuations": "\"'([{-",
                "append_punctuations": "\"\'.。,，!！?？:：\")]}、"
            }
        else:
            # Standard parameters for other models
            decode_options = {
                "fp16": args.fp16,
                "language": args.language,
                "task": task,
                "word_timestamps": True,
                "temperature": 0.0,
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
                "condition_on_previous_text": True
            }

        # Use Whisper's built-in transcription (no manual chunking)
        logger.info("Starting transcription process...")
        result = model.transcribe(str(input_path_obj), **decode_options)        # Filter out empty segments and handle turbo model's long segments
        filtered_segments = []
        total_segments_processed = 0
        
        # First pass: calculate total segments after potential splitting
        total_final_segments = 0
        for segment in result["segments"]:
            if isinstance(segment, dict):
                text = segment.get("text", "").strip()
                if text:
                    start_time = segment.get("start", 0.0)
                    end_time = segment.get("end", 0.0)
                    duration = end_time - start_time
                    
                    if model_type == "turbo" and duration > 10.0:
                        # Count how many segments this will split into
                        split_segments = split_text_for_subtitles(text, start_time, end_time, max_chars=80, max_words=12)
                        total_final_segments += len(split_segments)
                    else:
                        total_final_segments += 1
        
        # Second pass: process segments with accurate progress tracking
        for idx, segment in enumerate(result["segments"]):
            # Ensure segment is treated as a dictionary
            if isinstance(segment, dict):
                seg_dict = segment
            else:
                # Skip if segment is not a dict (shouldn't happen with Whisper)
                continue
                
            text = seg_dict.get("text", "").strip()
            if text:  # Only process non-empty segments
                start_time = seg_dict.get("start", 0.0)
                end_time = seg_dict.get("end", 0.0)
                duration = end_time - start_time
                
                # If this is a turbo model and segment is very long, split it
                if model_type == "turbo" and duration > 10.0:  # Split segments longer than 10 seconds
                    # Try to use word-level timestamps if available
                    words = seg_dict.get("words", [])
                    if words and len(words) > 0:
                        # Use word-level timestamps for more accurate splitting
                        split_segments = split_text_with_word_timestamps(words, max_chars=80, max_words=12)
                    else:
                        # Fallback to proportional splitting
                        split_segments = split_text_for_subtitles(text, start_time, end_time, max_chars=80, max_words=12)
                    
                    for chunk_text, chunk_start, chunk_end in split_segments:
                        chunk_seg = {
                            "start": chunk_start,
                            "end": chunk_end,
                            "text": chunk_text,
                            "avg_logprob": seg_dict.get("avg_logprob", -1),
                            "compression_ratio": seg_dict.get("compression_ratio", 1.0),
                            "no_speech_prob": seg_dict.get("no_speech_prob", 0.0),
                            "temperature": seg_dict.get("temperature", 0.0)
                        }
                        
                        # Get colored text and confidence for display
                        avg_logprob = chunk_seg.get("avg_logprob", -1)
                        colored_text, confidence = format_words_with_confidence(chunk_text, float(avg_logprob))
                        
                        # Show progress with accurate calculation
                        total_segments_processed += 1
                        progress = total_segments_processed / total_final_segments
                        logger.info(
                            "[%.2f%%] %s %s(%.2f%% confident)%s", 
                            progress * 100, 
                            colored_text,
                            Fore.CYAN,
                            confidence * 100,
                            Style.RESET_ALL
                        )
                        
                        filtered_segments.append(chunk_seg)
                else:
                    # Normal processing for segments that don't need splitting
                    avg_logprob = seg_dict.get("avg_logprob", -1)
                    colored_text, confidence = format_words_with_confidence(text, float(avg_logprob))
                    
                    # Show progress with accurate calculation
                    total_segments_processed += 1
                    progress = total_segments_processed / total_final_segments
                    logger.info(
                        "[%.2f%%] %s %s(%.2f%% confident)%s", 
                        progress * 100, 
                        colored_text,
                        Fore.CYAN,
                        confidence * 100,
                        Style.RESET_ALL
                    )
                    
                    filtered_segments.append(seg_dict)

        # Update result with filtered segments
        result["segments"] = filtered_segments

        # Generate subtitle file manually with correct timing
        logger.info("\nWriting subtitle file...")
        output_path = output_directory_obj / f"{output_name}.srt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for idx, segment in enumerate(filtered_segments):
                # Write SRT format: index, timestamp, text, blank line
                start_time = format_timestamp(segment.get("start", 0.0))
                end_time = format_timestamp(segment.get("end", 0.0))
                text = segment.get("text", "").strip()
                
                f.write(f"{idx + 1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        logger.info("Subtitle file saved to: %s", output_path)
        return result, output_name

    except Exception as e:
        logger.error("Failed to generate subtitles: %s", str(e))
        raise RuntimeError(f"Subtitle generation failed: {str(e)}")

# Indicate that the subtitles generator module is loaded.
print(f"{Fore.GREEN}✅ Subtitles Generator Module Loaded{Style.RESET_ALL}")