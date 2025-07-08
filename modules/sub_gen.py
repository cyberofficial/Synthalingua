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
import gc
import shutil
import tempfile
import os
import librosa

import whisper
import subprocess
from colorama import Fore, Style, init
from modules import parser_args

# Initialize colorama for Windows support
init()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Parse command-line arguments

args = parser_args.parse_arguments()

# Inform user if word_timestamps is enabled
if getattr(args, 'word_timestamps', False):
    print(f"{Fore.CYAN}ℹ️  Word-level timestamps are enabled. This may make subtitle generation a bit slower as it requires more processing power. If you notice any unusual slowdowns, try removing the --word_timestamps flag next time you run this command.{Style.RESET_ALL}")

# Inform user if isolate_vocals is enabled
if getattr(args, 'isolate_vocals', False):
    print(f"{Fore.CYAN}ℹ️  Vocal isolation is enabled. The program will attempt to extract vocals from the input audio before generating subtitles. This may take additional time and requires the demucs package.{Style.RESET_ALL}")

# Inform user if silent_detect is enabled
if getattr(args, 'silent_detect', False):
    custom_threshold = hasattr(args, 'silent_threshold') and args.silent_threshold != -35.0
    custom_duration = hasattr(args, 'silent_duration') and args.silent_duration != 0.5
    
    settings_info = ""
    if custom_threshold or custom_duration:
        parts = []
        if custom_threshold:
            parts.append(f"threshold: {getattr(args, 'silent_threshold', -35.0)}dB")
        if custom_duration:
            parts.append(f"min duration: {getattr(args, 'silent_duration', 0.5)}s")
        settings_info = f" ({', '.join(parts)})"
    
    print(f"{Fore.CYAN}ℹ️  Silent detection is enabled{settings_info}. The program will skip processing silent audio chunks during caption generation. This may improve processing speed for files with long silent periods.{Style.RESET_ALL}")

def detect_silence_in_audio(audio_path: str, silence_threshold_db: float = -35.0, min_silence_duration: float = 0.5) -> List[Dict[str, Any]]:
    """
    Detect silence and speech regions in audio file using intelligent segmentation.
    
    Args:
        audio_path (str): Path to audio file
        silence_threshold_db (float): dB threshold below which audio is considered silent (default: -35.0)
        min_silence_duration (float): Minimum duration in seconds for a region to be considered silence (default: 0.5)
    
    Returns:
        List[Dict[str, Any]]: List of regions with type, start, and end times
                              [{'type': 'speech', 'start': 13.8, 'end': 42.3}, ...]
    """
    try:
        # Try to import librosa, fall back to basic audio loading if not available
        try:
            import librosa
            # Load audio with librosa for better compatibility
            audio, sr = librosa.load(audio_path, sr=None)
        except ImportError:
            # Fallback: use whisper's audio loading
            import whisper.audio
            audio = whisper.audio.load_audio(audio_path)
            sr = 16000  # Whisper's standard sample rate
        
        print(f"{Fore.CYAN}🔍 Analyzing audio for speech/silence regions...{Style.RESET_ALL}")
        
        # Convert dB threshold to linear amplitude
        silence_threshold_linear = 10 ** (silence_threshold_db / 20.0)
        
        # Calculate frame-wise RMS energy with overlapping windows
        frame_length = int(0.025 * sr)  # 25ms frames
        hop_length = int(0.010 * sr)    # 10ms hop (overlap for smoother detection)
        
        # Calculate RMS for each frame
        rms_frames = []
        for i in range(0, len(audio) - frame_length + 1, hop_length):
            frame = audio[i:i + frame_length]
            rms = np.sqrt(np.mean(frame ** 2)) if len(frame) > 0 else 0.0
            rms_frames.append(rms)
        
        # Create time axis for frames
        frame_times = np.arange(len(rms_frames)) * hop_length / sr
        
        # Detect silence/speech regions
        is_silent = np.array(rms_frames) < silence_threshold_linear
        
        # Find transitions between silence and speech
        transitions = []
        current_state = is_silent[0]
        current_start = 0.0
        current_rms_values = []  # Track RMS values for current region
        
        for i, silent in enumerate(is_silent[1:], 1):
            current_rms_values.append(rms_frames[i-1])  # Add previous frame's RMS
            
            if silent != current_state:
                # State change detected
                region_type = 'silence' if current_state else 'speech'
                region_duration = frame_times[i] - current_start
                
                # Calculate average dB level for this region
                if current_rms_values:
                    avg_rms = np.mean(current_rms_values)
                    avg_db = 20 * np.log10(max(avg_rms, 1e-10))  # Avoid log(0)
                    max_rms = np.max(current_rms_values)
                    max_db = 20 * np.log10(max(max_rms, 1e-10))
                else:
                    avg_db = -float('inf')
                    max_db = -float('inf')
                
                # Only add regions that meet minimum duration requirements
                if region_type == 'silence' and region_duration >= min_silence_duration:
                    transitions.append({
                        'type': 'silence',
                        'start': current_start,
                        'end': frame_times[i],
                        'avg_db': avg_db,
                        'max_db': max_db,
                        'duration': region_duration
                    })
                elif region_type == 'speech' and region_duration >= 0.1:  # Minimum 100ms for speech
                    transitions.append({
                        'type': 'speech',
                        'start': current_start,
                        'end': frame_times[i],
                        'avg_db': avg_db,
                        'max_db': max_db,
                        'duration': region_duration
                    })
                
                current_state = silent
                current_start = frame_times[i]
                current_rms_values = []  # Reset for new region
        
        # Add remaining RMS values for final region
        current_rms_values.extend(rms_frames[len(is_silent)-len(current_rms_values):])
        
        # Add final region
        audio_duration = len(audio) / sr
        final_region_type = 'silence' if current_state else 'speech'
        final_duration = audio_duration - current_start
        
        # Calculate dB for final region
        if current_rms_values:
            avg_rms = np.mean(current_rms_values)
            avg_db = 20 * np.log10(max(avg_rms, 1e-10))
            max_rms = np.max(current_rms_values)
            max_db = 20 * np.log10(max(max_rms, 1e-10))
        else:
            avg_db = -float('inf')
            max_db = -float('inf')
        
        if final_region_type == 'silence' and final_duration >= min_silence_duration:
            transitions.append({
                'type': 'silence',
                'start': current_start,
                'end': audio_duration,
                'avg_db': avg_db,
                'max_db': max_db,
                'duration': final_duration
            })
        elif final_region_type == 'speech' and final_duration >= 0.1:
            transitions.append({
                'type': 'speech',
                'start': current_start,
                'end': audio_duration,
                'avg_db': avg_db,
                'max_db': max_db,
                'duration': final_duration
            })
        
        # Merge adjacent speech regions separated by very short silences
        merged_regions = []
        for region in transitions:
            if (region['type'] == 'speech' and 
                merged_regions and 
                merged_regions[-1]['type'] == 'speech' and
                region['start'] - merged_regions[-1]['end'] < 1.0):  # Less than 1 second gap
                # Merge with previous speech region - combine dB values
                prev_region = merged_regions[-1]
                
                # Weight the dB values by duration for proper averaging
                prev_duration = prev_region['duration']
                curr_duration = region['duration']
                total_duration = prev_duration + curr_duration
                
                # Weighted average of dB values
                combined_avg_db = (prev_region['avg_db'] * prev_duration + region['avg_db'] * curr_duration) / total_duration
                combined_max_db = max(prev_region['max_db'], region['max_db'])
                
                merged_regions[-1].update({
                    'end': region['end'],
                    'avg_db': combined_avg_db,
                    'max_db': combined_max_db,
                    'duration': total_duration
                })
            else:
                merged_regions.append(region)
        
        # Filter out speech regions and show statistics
        speech_regions = [r for r in merged_regions if r['type'] == 'speech']
        silence_regions = [r for r in merged_regions if r['type'] == 'silence']
        
        total_speech_duration = sum(r['end'] - r['start'] for r in speech_regions)
        total_silence_duration = sum(r['end'] - r['start'] for r in silence_regions)
        
        print(f"{Fore.GREEN}� Audio analysis complete:{Style.RESET_ALL}")
        print(f"   • Speech regions: {len(speech_regions)} ({total_speech_duration:.1f}s)")
        print(f"   • Silence regions: {len(silence_regions)} ({total_silence_duration:.1f}s)")
        print(f"   • Processing efficiency: {100 * total_speech_duration / audio_duration:.1f}% of audio contains speech")
        print(f"   • Current threshold: {silence_threshold_db:.1f}dB")
        
        # Show detailed breakdown of regions with dB levels
        print(f"\n{Fore.CYAN}🔊 Audio Level Analysis:{Style.RESET_ALL}")
        
        for i, region in enumerate(merged_regions):
            region_type = region['type']
            start_time = region['start']
            end_time = region['end']
            duration = region['duration']
            avg_db = region['avg_db']
            max_db = region['max_db']
            
            # Color-code based on region type and dB levels
            if region_type == 'speech':
                icon = "🎵"
                type_color = Fore.GREEN
                type_label = "SPEECH"
            else:
                icon = "🔇"
                type_color = Fore.YELLOW
                type_label = "SILENCE"
            
            # Add recommendations based on dB levels
            recommendation = ""
            if region_type == 'silence':
                if avg_db > silence_threshold_db + 5:
                    recommendation = f" {Fore.RED}(Maybe increase threshold to {avg_db + 3:.1f}dB?){Style.RESET_ALL}"
                elif avg_db > silence_threshold_db:
                    recommendation = f" {Fore.YELLOW}(Close to threshold){Style.RESET_ALL}"
            else:  # speech
                if avg_db < silence_threshold_db:
                    recommendation = f" {Fore.RED}(Maybe decrease threshold to {avg_db - 3:.1f}dB?){Style.RESET_ALL}"
            
            print(f"   {icon} {type_color}{type_label:<7}{Style.RESET_ALL} "
                  f"{start_time:6.1f}s - {end_time:6.1f}s ({duration:5.1f}s) "
                  f"│ Avg: {avg_db:6.1f}dB │ Peak: {max_db:6.1f}dB{recommendation}")
        
        # Show threshold guidance
        print(f"\n{Fore.CYAN}💡 Threshold Guidance:{Style.RESET_ALL}")
        
        # Analyze if threshold seems appropriate
        misclassified_speech = [r for r in silence_regions if r['avg_db'] < silence_threshold_db - 5]
        misclassified_silence = [r for r in speech_regions if r['avg_db'] > silence_threshold_db + 10]
        
        if misclassified_speech:
            print(f"   {Fore.YELLOW}⚠️  {len(misclassified_speech)} 'silence' regions have very low audio levels{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}   Consider lowering threshold to around {min(r['avg_db'] for r in misclassified_speech) - 3:.1f}dB{Style.RESET_ALL}")
        
        if misclassified_silence:
            print(f"   {Fore.YELLOW}⚠️  {len(misclassified_silence)} 'speech' regions have high audio levels{Style.RESET_ALL}")
            print(f"   {Fore.YELLOW}   Consider raising threshold to around {max(r['avg_db'] for r in misclassified_silence) - 3:.1f}dB{Style.RESET_ALL}")
        
        if not misclassified_speech and not misclassified_silence:
            print(f"   {Fore.GREEN}✅ Current threshold ({silence_threshold_db:.1f}dB) seems well-tuned for this audio{Style.RESET_ALL}")
        
        # Show speech regions that will be processed (simplified now since detailed info is above)
        if speech_regions:
            print(f"\n{Fore.GREEN}🎵 Speech regions to be processed: {len(speech_regions)}{Style.RESET_ALL}")
        
        return merged_regions
        
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️  Silence detection failed: {e}. Processing entire file.{Style.RESET_ALL}")
        # If silence detection fails, return the entire audio as one speech chunk
        try:
            import whisper.audio
            audio = whisper.audio.load_audio(audio_path)
            duration = len(audio) / 16000
            return [{'type': 'speech', 'start': 0.0, 'end': duration}]
        except:
            # Last resort - assume 60 minute max duration
            return [{'type': 'speech', 'start': 0.0, 'end': 3600.0}]

def process_speech_regions(audio_path: str, regions: List[Dict[str, Any]], model, decode_options: Dict) -> List[Dict]:
    """
    Process speech regions and return combined segments with proper timestamps.
    
    Args:
        audio_path (str): Path to audio file
        regions (List[Dict[str, Any]]): List of speech/silence regions from detect_silence_in_audio
        model: Loaded Whisper model
        decode_options (Dict): Whisper decode options
    
    Returns:
        List[Dict]: List of processed segments with adjusted timestamps
    """
    all_segments = []
    
    # Filter to only speech regions
    speech_regions = [r for r in regions if r['type'] == 'speech']
    
    if not speech_regions:
        print(f"{Fore.YELLOW}⚠️  No speech regions detected in audio file.{Style.RESET_ALL}")
        return []
    
    try:
        print(f"{Fore.CYAN}🎵 Processing {len(speech_regions)} speech regions...{Style.RESET_ALL}")
        
        for i, region in enumerate(speech_regions, 1):
            region_start = region['start']
            region_end = region['end']
            region_duration = region_end - region_start
            
            print(f"{Fore.CYAN}🎵 Processing speech region {i}/{len(speech_regions)}: {region_start:.1f}s - {region_end:.1f}s ({region_duration:.1f}s){Style.RESET_ALL}")
            
            # Load full audio for this approach
            import whisper.audio
            full_audio = whisper.audio.load_audio(audio_path)
            sr = 16000  # Whisper's standard sample rate
            
            # Extract the speech region
            start_sample = int(region_start * sr)
            end_sample = int(region_end * sr)
            region_audio = full_audio[start_sample:end_sample]
            
            # Create temporary audio file for this speech region
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                try:
                    # Try using soundfile if available
                    import soundfile as sf
                    sf.write(tmp_file.name, region_audio, sr)
                except ImportError:
                    # Fallback: use basic wave writing
                    import wave
                    with wave.open(tmp_file.name, 'wb') as wav_file:
                        wav_file.setnchannels(1)  # Mono
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(sr)
                        # Convert float audio to 16-bit PCM
                        audio_int16 = (region_audio * 32767).astype(np.int16)
                        wav_file.writeframes(audio_int16.tobytes())
                
                # Transcribe the entire speech region as one chunk
                # Let Whisper handle internal segmentation naturally
                region_result = model.transcribe(tmp_file.name, **decode_options)
                
                # Adjust all timestamps to match original audio timeline
                for segment in region_result.get("segments", []):
                    if isinstance(segment, dict) and segment.get("text", "").strip():
                        # Adjust timestamps relative to original audio
                        segment["start"] = segment.get("start", 0.0) + region_start
                        segment["end"] = segment.get("end", 0.0) + region_start
                        all_segments.append(segment)
                        
                        # Show progress for each segment within the region
                        seg_start = segment["start"]
                        seg_end = segment["end"]
                        seg_text = segment.get("text", "").strip()[:50] + "..." if len(segment.get("text", "").strip()) > 50 else segment.get("text", "").strip()
                        print(f"   📝 Segment: {seg_start:.1f}s-{seg_end:.1f}s: \"{seg_text}\"")
                
                # Clean up temporary file
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass
                    
                print(f"   ✅ Region {i} complete: {len(region_result.get('segments', []))} segments generated")
    
    except Exception as e:
        print(f"{Fore.RED}❌ Error processing speech regions: {e}. Falling back to full file processing.{Style.RESET_ALL}")
        # Fallback to processing entire file
        full_result = model.transcribe(audio_path, **decode_options)
        all_segments = full_result.get("segments", [])
    
    print(f"{Fore.GREEN}🎉 Speech processing complete: {len(all_segments)} total segments generated{Style.RESET_ALL}")
    return all_segments

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

def unload_model(model: whisper.Whisper) -> None:
    """
    Unload the Whisper model and clear VRAM/RAM.
    
    Args:
        model (whisper.Whisper): The Whisper model to unload
    """
    try:
        # Delete the model from memory
        del model
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if using GPU
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("🗑️ VRAM cleared")
        except ImportError:
            # torch not available, skip CUDA cleanup
            pass
            
        logger.info("🗑️ Model unloaded and memory cleared")
        
    except Exception as e:
        logger.warning("Failed to completely unload model: %s", str(e))

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

    # Vocal isolation step if requested
    processed_audio_path = str(input_path_obj)
    if getattr(args, 'isolate_vocals', False):
        import shutil, tempfile, os
        if not shutil.which('demucs'):
            raise RuntimeError("demucs is not installed or not in PATH. Please install demucs to use --isolate_vocals.")
        try:
            print(f"{Fore.CYAN}🔄 Isolating vocals from input audio using Demucs...{Style.RESET_ALL}")
            with tempfile.TemporaryDirectory() as tmpdir:
                # Run demucs CLI to separate vocals with proper encoding
                result = subprocess.run([
                    'demucs',
                    '-o', tmpdir,
                    '--two-stems', 'vocals',
                    str(input_path_obj)
                ], capture_output=True, text=True, encoding='utf-8', errors='replace')
                
                # Debug output
                print(f"{Fore.YELLOW}Debug: Demucs return code: {result.returncode}{Style.RESET_ALL}")
                if result.stdout:
                    print(f"{Fore.YELLOW}Debug: Demucs stdout: {result.stdout[:500]}...{Style.RESET_ALL}")
                if result.stderr:
                    print(f"{Fore.YELLOW}Debug: Demucs stderr: {result.stderr[:500]}...{Style.RESET_ALL}")
                
                if result.returncode != 0:
                    raise RuntimeError(f"Demucs failed with return code {result.returncode}: {result.stderr}")
                
                # Find the actual output directory structure
                base_name = os.path.splitext(os.path.basename(str(input_path_obj)))[0]
                
                # Demucs might create different directory structures, let's search for vocals.wav
                vocals_path = None
                
                # Try different possible output locations
                possible_locations = [
                    os.path.join(tmpdir, 'demucs', base_name, 'vocals.wav'),  # Standard location
                    os.path.join(tmpdir, 'htdemucs', base_name, 'vocals.wav'),  # HTDemucs model
                    os.path.join(tmpdir, 'mdx_extra', base_name, 'vocals.wav'),  # MDX model
                    os.path.join(tmpdir, base_name, 'vocals.wav'),  # Direct output
                ]
                
                # Search recursively for vocals.wav in case structure is different
                for root, dirs, files in os.walk(tmpdir):
                    if 'vocals.wav' in files:
                        vocals_path = os.path.join(root, 'vocals.wav')
                        print(f"{Fore.GREEN}Found vocals.wav at: {vocals_path}{Style.RESET_ALL}")
                        break
                
                # Try the predefined locations if recursive search didn't work
                if not vocals_path:
                    for location in possible_locations:
                        if os.path.exists(location):
                            vocals_path = location
                            print(f"{Fore.GREEN}Found vocals.wav at predefined location: {vocals_path}{Style.RESET_ALL}")
                            break
                
                if not vocals_path or not os.path.exists(vocals_path):
                    # List all files in tmpdir for debugging
                    print(f"{Fore.RED}Debug: Contents of tmpdir ({tmpdir}):{Style.RESET_ALL}")
                    for root, dirs, files in os.walk(tmpdir):
                        level = root.replace(tmpdir, '').count(os.sep)
                        indent = ' ' * 2 * level
                        print(f"{indent}{os.path.basename(root)}/")
                        subindent = ' ' * 2 * (level + 1)
                        for file in files:
                            print(f"{subindent}{file}")
                    raise RuntimeError(f"Vocal isolation failed: vocals.wav not found. Expected at: {possible_locations[0]}")
                
                # Set the demucs_out_dir for file copying
                demucs_out_dir = os.path.dirname(vocals_path)
                # Set the demucs_out_dir for file copying
                demucs_out_dir = os.path.dirname(vocals_path)

                # Use current UTC time for folder name to avoid Unicode issues
                from datetime import datetime
                utc_folder = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                
                # Use absolute path to ensure files are saved in the correct location
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up two levels from modules/
                dest_dir = os.path.join(script_dir, 'temp', 'audio', utc_folder)
                os.makedirs(dest_dir, exist_ok=True)
                for file in os.listdir(demucs_out_dir):
                    src_file = os.path.join(demucs_out_dir, file)
                    if os.path.isfile(src_file):
                        shutil.copy2(src_file, os.path.join(dest_dir, file))
                
                # Update processed_audio_path to point to the copied vocals file
                processed_audio_path = os.path.join(dest_dir, 'vocals.wav')
                print(f"{Fore.GREEN}✅ Vocal isolation complete. Using isolated vocals for transcription. Split files saved to {dest_dir}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Using vocals file: {processed_audio_path}{Style.RESET_ALL}")
        except Exception as e:
            raise RuntimeError(f"Vocal isolation failed: {str(e)}")
    
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
        # Only enable word_timestamps if the argument is set (default False)
        word_timestamps = getattr(args, 'word_timestamps', False)
        if model_type == "turbo":
            # Turbo model needs different parameters for proper segmentation
            decode_options = {
                "fp16": args.fp16,
                "language": args.language,
                "task": task,
                "word_timestamps": word_timestamps,
                "temperature": 0.1,  # Slightly higher temperature for turbo
                "compression_ratio_threshold": 2.0,  # Lower threshold for turbo
                "logprob_threshold": -0.8,  # Higher threshold for turbo
                "no_speech_threshold": 0.4,  # Lower threshold for turbo
                "condition_on_previous_text": False,  # Disable for turbo to prevent long segments
                "prepend_punctuations": "\"'([{-",
                "append_punctuations": "\"\'.。,，!！?？:：)"  # fixed closing string and removed stray characters
            }
        else:
            # Standard parameters for other models
            decode_options = {
                "fp16": args.fp16,
                "language": args.language,
                "task": task,
                "word_timestamps": word_timestamps,
                "temperature": 0.0,
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
                "condition_on_previous_text": True
            }

        # Use Whisper's built-in transcription or chunk-based processing
        logger.info("Starting transcription process...")
        
        # Check if silence detection is enabled and we're in caption mode
        use_silence_detection = getattr(args, 'silent_detect', False) and getattr(args, 'makecaptions', False)
        
        if use_silence_detection:
            print(f"{Fore.CYAN}🔍 Analyzing audio for speech/silence regions...{Style.RESET_ALL}")
            
            # Get custom silence parameters from args if provided
            silence_threshold_db = getattr(args, 'silent_threshold', -35.0)
            min_silence_duration = getattr(args, 'silent_duration', 0.5)
            print(f"{Fore.YELLOW}🔧 Using silence threshold: {silence_threshold_db}dB, minimum duration: {min_silence_duration}s{Style.RESET_ALL}")
            
            audio_regions = detect_silence_in_audio(
                processed_audio_path, 
                silence_threshold_db=silence_threshold_db,
                min_silence_duration=min_silence_duration
            )
            
            # Filter to speech regions only
            speech_regions = [r for r in audio_regions if r['type'] == 'speech']
            
            if len(speech_regions) == 0:
                print(f"{Fore.YELLOW}⚠️  No speech detected in file. Creating empty result.{Style.RESET_ALL}")
                result = {"segments": [], "text": "", "language": args.language or "en"}
            else:
                print(f"{Fore.GREEN}🎵 Processing {len(speech_regions)} speech regions with natural boundaries{Style.RESET_ALL}")
                segments = process_speech_regions(processed_audio_path, audio_regions, model, decode_options)
                result = {
                    "segments": segments,
                    "text": " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text", "").strip()),
                    "language": args.language or "en"
                }
        else:
            # Standard full-file processing
            result = model.transcribe(processed_audio_path, **decode_options)        # Filter out empty segments and handle turbo model's long segments
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
        
        # Unload model to free VRAM/RAM
        unload_model(model)
        
        return result, output_name

    except Exception as e:
        # Ensure model is unloaded even if there's an error
        try:
            unload_model(model)
        except:
            pass  # Model might not be loaded if error occurred during loading
            
        logger.error("Failed to generate subtitles: %s", str(e))
        raise RuntimeError(f"Subtitle generation failed: {str(e)}")

# Indicate that the subtitles generator module is loaded.
print(f"{Fore.GREEN}✅ Subtitles Generator Module Loaded{Style.RESET_ALL}")