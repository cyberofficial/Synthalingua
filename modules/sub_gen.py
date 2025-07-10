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

# Global variable to track auto-proceed mode for detection reviews
_auto_proceed_detection = False

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

def format_human_time(seconds: float) -> str:
    """
    Convert seconds to human-readable format (e.g., 1m40.2s).
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Human-readable time format
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}h{minutes:02d}m{remaining_seconds:04.1f}s"
    else:
        return f"{minutes}m{remaining_seconds:04.1f}s"

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
                  f"({format_human_time(start_time)} - {format_human_time(end_time)}) "
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
        
        # Interactive adjustment options
        global _auto_proceed_detection
        
        # Check if auto-proceed is enabled
        if _auto_proceed_detection:
            print(f"\n{Fore.GREEN}🚀 Auto-proceeding with current detection (skip mode enabled){Style.RESET_ALL}")
            # Show speech regions that will be processed (simplified now since detailed info is above)
            if speech_regions:
                print(f"\n{Fore.GREEN}🎵 Speech regions to be processed: {len(speech_regions)}{Style.RESET_ALL}")
            return merged_regions
        
        while True:
            print(f"\n{Fore.CYAN}🔧 Detection Review:{Style.RESET_ALL}")
            print(f"   Do you want to:")
            print(f"   1. {Fore.GREEN}Proceed with current detection{Style.RESET_ALL}")
            print(f"   2. {Fore.YELLOW}Adjust threshold settings and re-analyze{Style.RESET_ALL}")
            print(f"   3. {Fore.CYAN}Manually modify region classifications{Style.RESET_ALL}")
            if getattr(args, 'isolate_vocals', False):
                print(f"   4. {Fore.MAGENTA}Try different Demucs model and re-analyze{Style.RESET_ALL}")
            print(f"   5. {Fore.BLUE}Proceed with current detection and skip asking again{Style.RESET_ALL}")
            
            max_choice = 5 if getattr(args, 'isolate_vocals', False) else 5
            max_choice_vocals = 4 if getattr(args, 'isolate_vocals', False) else 3
            
            try:
                choice = input(f"\n{Fore.CYAN}Enter your choice (1-{max_choice}): {Style.RESET_ALL}").strip()
                
                if choice == "1":
                    break  # Proceed with current detection
                    
                elif choice == "5":
                    _auto_proceed_detection = True
                    print(f"{Fore.GREEN}✅ Auto-proceed mode enabled. Future segments will skip detection review.{Style.RESET_ALL}")
                    break  # Proceed and skip future reviews
                    
                elif choice == "2":
                    # Re-run with new settings
                    print(f"\n{Fore.CYAN}Current settings:{Style.RESET_ALL}")
                    print(f"   Threshold: {silence_threshold_db:.1f}dB")
                    print(f"   Min duration: {min_silence_duration:.1f}s")
                    
                    # Get new threshold
                    new_threshold_input = input(f"\n{Fore.CYAN}Enter new threshold (current: {silence_threshold_db:.1f}dB) or press Enter to keep: {Style.RESET_ALL}").strip()
                    if new_threshold_input:
                        try:
                            new_threshold = float(new_threshold_input)
                            print(f"{Fore.GREEN}✅ New threshold: {new_threshold:.1f}dB{Style.RESET_ALL}")
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid threshold. Keeping current: {silence_threshold_db:.1f}dB{Style.RESET_ALL}")
                            new_threshold = silence_threshold_db
                    else:
                        new_threshold = silence_threshold_db
                    
                    # Get new duration
                    new_duration_input = input(f"{Fore.CYAN}Enter new min duration (current: {min_silence_duration:.1f}s) or press Enter to keep: {Style.RESET_ALL}").strip()
                    if new_duration_input:
                        try:
                            new_duration = float(new_duration_input)
                            print(f"{Fore.GREEN}✅ New min duration: {new_duration:.1f}s{Style.RESET_ALL}")
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid duration. Keeping current: {min_silence_duration:.1f}s{Style.RESET_ALL}")
                            new_duration = min_silence_duration
                    else:
                        new_duration = min_silence_duration
                    
                    # Re-run analysis
                    print(f"\n{Fore.CYAN}🔄 Re-analyzing with new settings...{Style.RESET_ALL}")
                    return detect_silence_in_audio(audio_path, new_threshold, new_duration)
                
                elif choice == "4" and getattr(args, 'isolate_vocals', False):
                    # Try different Demucs model
                    print(f"\n{Fore.CYAN}🎛️ Demucs Model Selection:{Style.RESET_ALL}")
                    print(f"   Available models:")
                    print(f"   1. {Fore.YELLOW}htdemucs{Style.RESET_ALL} (default, Hybrid Transformer v4)")
                    print(f"   2. {Fore.YELLOW}htdemucs_ft{Style.RESET_ALL} (fine-tuned htdemucs, better quality, slower)")
                    print(f"   3. {Fore.YELLOW}htdemucs_6s{Style.RESET_ALL} (6-source: drums, bass, other, vocals, piano, guitar)")
                    print(f"   4. {Fore.YELLOW}hdemucs_mmi{Style.RESET_ALL} (Hybrid Demucs v3, MusDB + 800 songs)")
                    print(f"   5. {Fore.YELLOW}mdx{Style.RESET_ALL} (MDX challenge Track A winner)")
                    print(f"   6. {Fore.YELLOW}mdx_extra{Style.RESET_ALL} (MDX Track B, trained with extra data)")
                    print(f"   7. {Fore.YELLOW}mdx_q{Style.RESET_ALL} (quantized mdx, smaller/faster)")
                    print(f"   8. {Fore.YELLOW}mdx_extra_q{Style.RESET_ALL} (quantized mdx_extra, smaller/faster)")
                    print(f"   9. {Fore.YELLOW}hdemucs{Style.RESET_ALL} (original Hybrid Demucs v3)")
                    print(f"  10. {Fore.YELLOW}demucs{Style.RESET_ALL} (original time-only Demucs)")
                    
                    print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
                    print(f"   🎯 {Fore.GREEN}Best Quality{Style.RESET_ALL}: htdemucs_ft (fine-tuned)")
                    print(f"   🎯 {Fore.BLUE}Fastest{Style.RESET_ALL}: mdx_q or mdx_extra_q (quantized)")
                    print(f"   🎯 {Fore.MAGENTA}Detailed Separation{Style.RESET_ALL}: htdemucs_6s (6 sources)")
                    print(f"   🎯 {Fore.CYAN}Balanced{Style.RESET_ALL}: mdx_extra (good quality + speed)")
                    print(f"   🎯 {Fore.YELLOW}Legacy/Compatibility{Style.RESET_ALL}: hdemucs or demucs")
                    
                    model_choice = input(f"\n{Fore.CYAN}Select Demucs model (1-10): {Style.RESET_ALL}").strip()
                    
                    model_map = {
                        "1": "htdemucs",
                        "2": "htdemucs_ft", 
                        "3": "htdemucs_6s",
                        "4": "hdemucs_mmi",
                        "5": "mdx",
                        "6": "mdx_extra",
                        "7": "mdx_q",
                        "8": "mdx_extra_q",
                        "9": "hdemucs",
                        "10": "demucs"
                    }
                    
                    if model_choice in model_map:
                        selected_model = model_map[model_choice]
                        print(f"{Fore.GREEN}✅ Selected model: {selected_model}{Style.RESET_ALL}")
                        
                        # Show model info
                        model_info = {
                            "htdemucs": "Latest Hybrid Transformer model (default)",
                            "htdemucs_ft": "Fine-tuned version for better quality",
                            "htdemucs_6s": "6-source separation (includes piano/guitar)",
                            "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                            "mdx": "Frequency-domain model, MDX winner",
                            "mdx_extra": "Enhanced MDX with extra training data",
                            "mdx_q": "Quantized MDX (faster, smaller)",
                            "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                            "hdemucs": "Original Hybrid Demucs v3",
                            "demucs": "Original time-domain Demucs"
                        }
                        
                        print(f"{Fore.CYAN}ℹ️  {model_info[selected_model]}{Style.RESET_ALL}")
                        
                        # Re-run vocal isolation with new model and then re-analyze
                        print(f"\n{Fore.CYAN}🔄 Re-running vocal isolation with {selected_model} model...{Style.RESET_ALL}")
                        
                        # Import the original audio path from the calling function
                        # We need to get the original path before vocal isolation
                        original_audio_path = audio_path.replace("_vocals.wav", "") if "_vocals" in audio_path else audio_path
                        
                        try:
                            import tempfile
                            import subprocess
                            import os
                            import glob
                            
                            with tempfile.TemporaryDirectory() as tmpdir:
                                # Run demucs with selected model
                                result = subprocess.run([
                                    'demucs',
                                    '-n', selected_model,
                                    '-o', tmpdir,
                                    '--two-stems', 'vocals',
                                    original_audio_path
                                ], capture_output=True, text=True, encoding='utf-8', errors='replace')
                                
                                if result.returncode != 0:
                                    print(f"{Fore.RED}❌ Demucs failed with model {selected_model}: {result.stderr}{Style.RESET_ALL}")
                                    continue
                                
                                # Find the vocals file
                                base_name = os.path.splitext(os.path.basename(original_audio_path))[0]
                                vocals_pattern = os.path.join(tmpdir, selected_model, base_name, "vocals.wav")
                                vocals_files = glob.glob(vocals_pattern)
                                
                                if not vocals_files:
                                    print(f"{Fore.RED}❌ Could not find vocals file after Demucs processing{Style.RESET_ALL}")
                                    continue
                                
                                new_vocals_path = vocals_files[0]
                                print(f"{Fore.GREEN}✅ Vocal isolation complete with {selected_model} model{Style.RESET_ALL}")
                                
                                # Re-analyze with the new vocals file
                                print(f"\n{Fore.CYAN}🔄 Re-analyzing audio with new vocal isolation...{Style.RESET_ALL}")
                                return detect_silence_in_audio(new_vocals_path, silence_threshold_db, min_silence_duration)
                                
                        except Exception as e:
                            print(f"{Fore.RED}❌ Error running Demucs with {selected_model}: {e}{Style.RESET_ALL}")
                            print(f"{Fore.YELLOW}   Continuing with current analysis...{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.RED}❌ Invalid model choice. Please select 1-10.{Style.RESET_ALL}")
                        continue
                    
                elif choice == "3":
                    # Manual region modification - this should loop back to menu
                    while True:
                        print(f"\n{Fore.CYAN}Manual Region Modification:{Style.RESET_ALL}")
                        print(f"Enter region numbers to toggle (e.g., '1,3,5' to toggle regions 1, 3, and 5)")
                        print(f"Enter 'back' to return to main menu")
                        print(f"Current regions:")
                        
                        # Update statistics for current display
                        current_speech_regions = [r for r in merged_regions if r['type'] == 'speech']
                        current_silence_regions = [r for r in merged_regions if r['type'] == 'silence']
                        current_speech_duration = sum(r['end'] - r['start'] for r in current_speech_regions)
                        current_silence_duration = sum(r['end'] - r['start'] for r in current_silence_regions)
                        
                        print(f"   • Current: {len(current_speech_regions)} speech ({current_speech_duration:.1f}s), {len(current_silence_regions)} silence ({current_silence_duration:.1f}s)")
                        
                        for i, region in enumerate(merged_regions, 1):
                            region_type = region['type']
                            start_time = region['start']
                            end_time = region['end']
                            duration = region['duration']
                            type_color = Fore.GREEN if region_type == 'speech' else Fore.YELLOW
                            print(f"   {i:2d}. {type_color}{region_type.upper():<7}{Style.RESET_ALL} "
                                  f"{start_time:6.1f}s - {end_time:6.1f}s ({format_human_time(start_time)} - {format_human_time(end_time)})")
                        
                        toggle_input = input(f"\n{Fore.CYAN}Enter region numbers to toggle (or 'back' to return): {Style.RESET_ALL}").strip()
                        
                        if toggle_input.lower() == 'back':
                            break  # Go back to main menu
                            
                        if toggle_input:
                            try:
                                # Parse region numbers
                                region_numbers = [int(x.strip()) for x in toggle_input.split(',') if x.strip()]
                                
                                # Toggle specified regions
                                changes_made = False
                                for region_num in region_numbers:
                                    if 1 <= region_num <= len(merged_regions):
                                        region_idx = region_num - 1
                                        old_type = merged_regions[region_idx]['type']
                                        new_type = 'silence' if old_type == 'speech' else 'speech'
                                        merged_regions[region_idx]['type'] = new_type
                                        
                                        print(f"   {Fore.GREEN}✅ Region {region_num}: {old_type} → {new_type}{Style.RESET_ALL}")
                                        changes_made = True
                                    else:
                                        print(f"   {Fore.RED}❌ Invalid region number: {region_num}{Style.RESET_ALL}")
                                
                                if changes_made:
                                    print(f"\n{Fore.GREEN}✅ Manual modifications applied!{Style.RESET_ALL}")
                                    # Update statistics after manual changes
                                    speech_regions = [r for r in merged_regions if r['type'] == 'speech']
                                    silence_regions = [r for r in merged_regions if r['type'] == 'silence']
                                    
                                    total_speech_duration = sum(r['end'] - r['start'] for r in speech_regions)
                                    total_silence_duration = sum(r['end'] - r['start'] for r in silence_regions)
                                    
                                    print(f"   • Updated speech regions: {len(speech_regions)} ({total_speech_duration:.1f}s)")
                                    print(f"   • Updated silence regions: {len(silence_regions)} ({total_silence_duration:.1f}s)")
                                    
                            except ValueError:
                                print(f"{Fore.RED}❌ Invalid input format. Use comma-separated numbers (e.g., '1,3,5'){Style.RESET_ALL}")
                        else:
                            # Empty input, continue the loop to show regions again
                            continue
                    
                    # Continue to main menu after manual modification
                    continue
                    
                else:
                    max_choice_text = "5"
                    print(f"{Fore.RED}❌ Invalid choice. Please enter 1-{max_choice_text}.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Proceeding with current detection.{Style.RESET_ALL}")
                break
            except EOFError:
                print(f"\n{Fore.YELLOW}⚠️  Input ended. Proceeding with current detection.{Style.RESET_ALL}")
                break
        
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

def get_media_duration(file_path: str) -> Optional[float]:
    """
    Get the duration of a media file using ffprobe.
    
    Args:
        file_path (str): Path to the media file
        
    Returns:
        Optional[float]: Duration in seconds, or None if failed to detect
    """
    try:
        import subprocess
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json', 
            '-show_format', file_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            duration_str = data.get('format', {}).get('duration')
            if duration_str:
                return float(duration_str)
    except Exception as e:
        logger.warning(f"Failed to get media duration: {e}")
    
    return None

def parse_timestamp(timestamp: str) -> float:
    """
    Parse timestamp in HH:MM:SS.mmm or MM:SS.mmm format to seconds.
    
    Args:
        timestamp (str): Timestamp string
        
    Returns:
        float: Time in seconds
        
    Raises:
        ValueError: If timestamp format is invalid
    """
    try:
        parts = timestamp.split(':')
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        elif len(parts) == 2:  # MM:SS.mmm
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        else:
            # Just seconds
            return float(timestamp)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {timestamp}. Use HH:MM:SS.mmm, MM:SS.mmm, or seconds.")

def suggest_split_points(duration: float, segment_length: int = 1800) -> List[float]:
    """
    Suggest split points for a long media file.
    
    Args:
        duration (float): Total duration in seconds
        segment_length (int): Target segment length in seconds (default: 30 minutes)
        
    Returns:
        List[float]: List of suggested split points in seconds
    """
    split_points = []
    current_time = 0
    
    while current_time + segment_length < duration:
        current_time += segment_length
        split_points.append(current_time)
    
    return split_points

def format_seconds_to_timestamp(seconds: float) -> str:
    """
    Convert seconds to HH:MM:SS.mmm format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def create_segment(input_path: str, start_time: float, end_time: float, output_path: str) -> bool:
    """
    Create a segment of media file using FFmpeg.
    
    Args:
        input_path (str): Path to input media file
        start_time (float): Start time in seconds
        end_time (float): End time in seconds
        output_path (str): Path for output segment
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import subprocess
        
        duration = end_time - start_time
        
        # Use FFmpeg to extract segment
        cmd = [
            'ffmpeg', '-y',  # -y to overwrite output files
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
            '-c', 'copy',  # Copy streams without re-encoding for speed
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating segment: {e}")
        return False

def filter_unwanted_phrases(text: str) -> str:
    """
    Filter out unwanted phrases from subtitle text.
    
    Args:
        text (str): Original subtitle text
        
    Returns:
        str: Filtered text, or empty string if text should be removed entirely
    """
    if not text or not text.strip():
        return ""
    
    # Check for "Thank you for watching" and variations (case-insensitive)
    text_lower = text.lower().strip()
    
    # List of phrases to completely remove
    unwanted_phrases = [
        "thank you for watching"
    ]
    
    # Check if any unwanted phrase is in the text
    for phrase in unwanted_phrases:
        if phrase in text_lower:
            # Only show filtering message in debug mode
            if getattr(args, 'debug', False):
                print(f"{Fore.YELLOW}🚫 Filtered out unwanted phrase: '{text}'{Style.RESET_ALL}")
            return ""  # Remove the entire line
    
    return text.strip()

def combine_segment_subtitles(segments_data: List[Dict], output_path: str) -> None:
    """
    Combine subtitle segments into a single SRT file with proper timing.
    
    Args:
        segments_data (List[Dict]): List of segment data with results and timing info
        output_path (str): Path for combined subtitle file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            subtitle_index = 1
            
            for segment_data in segments_data:
                result = segment_data['result']
                time_offset = segment_data['start_time']
                
                for segment in result.get("segments", []):
                    if isinstance(segment, dict) and segment.get("text", "").strip():
                        # Adjust timestamps to account for the segment's position in the original file
                        start_time = segment.get("start", 0.0) + time_offset
                        end_time = segment.get("end", 0.0) + time_offset
                        text = segment.get("text", "").strip()
                        
                        # Filter unwanted phrases
                        filtered_text = filter_unwanted_phrases(text)
                        
                        # Only write if text remains after filtering
                        if filtered_text:
                            # Write SRT format
                            f.write(f"{subtitle_index}\n")
                            f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
                            f.write(f"{filtered_text}\n\n")
                            
                            subtitle_index += 1
                        
        logger.info(f"Combined subtitles saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Error combining subtitles: {e}")
        raise

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

    # Check media duration and offer segmentation for all files
    duration = get_media_duration(str(input_path_obj))
    use_segmentation = False
    split_points = []
    
    if duration:  # Offer segmentation for any file with detectable duration
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60
        
        # Determine appropriate messaging and defaults based on file length
        if duration > 3600:  # Over 1 hour
            file_category = "Very long"
            warning_color = Fore.RED
            default_segment_length = 1800  # 30 minutes for very long files
            recommendation = "Strongly recommended to use segmentation to avoid memory issues."
        elif duration > 1800:  # Over 30 minutes
            file_category = "Long"
            warning_color = Fore.YELLOW
            default_segment_length = 900   # 15 minutes for long files
            recommendation = "Recommended to use segmentation for better memory management."
        elif duration > 300:  # 5-30 minutes
            file_category = "Medium"
            warning_color = Fore.CYAN
            default_segment_length = 600   # 10 minutes for medium files
            recommendation = "Optional segmentation available for better control or memory management."
        else:  # Under 5 minutes
            file_category = "Short"
            warning_color = Fore.GREEN
            default_segment_length = 120   # 2 minutes for short files
            recommendation = "Optional segmentation available (may not be necessary for such short files)."
        
        print(f"\n{warning_color}📊 {file_category} media file detected:{Style.RESET_ALL}")
        print(f"   Duration: {hours:02d}:{minutes:02d}:{seconds:06.3f} ({duration:.1f} seconds)")
        print(f"   File size: {input_path_obj.stat().st_size / (1024*1024*1024):.2f} GB")
        
        print(f"\n{Fore.CYAN}💡 {recommendation}{Style.RESET_ALL}")
        
        # Suggest automatic split points based on file length
        suggested_points = suggest_split_points(duration, default_segment_length)
        if suggested_points:
            segment_minutes = default_segment_length // 60
            print(f"\n{Fore.CYAN}🎯 Suggested split points (every {segment_minutes} minutes):{Style.RESET_ALL}")
            for i, point in enumerate(suggested_points):
                timestamp = format_seconds_to_timestamp(point)
                print(f"   {i+1}. {timestamp}")
        
        print(f"\n{Fore.CYAN}Options:{Style.RESET_ALL}")
        print(f"   1. {Fore.GREEN}Process entire file{Style.RESET_ALL}")
        print(f"   2. {Fore.YELLOW}Use suggested split points{Style.RESET_ALL}")
        print(f"   3. {Fore.CYAN}Enter custom split points{Style.RESET_ALL}")
        print(f"   4. {Fore.MAGENTA}Choose different segment length{Style.RESET_ALL}")
        
        while True:
            try:
                choice = input(f"\n{Fore.CYAN}Select option (1-4): {Style.RESET_ALL}").strip()
                
                if choice == "1":
                    print(f"{Fore.GREEN}✅ Processing entire file...{Style.RESET_ALL}")
                    break
                    
                elif choice == "2":
                    if suggested_points:
                        use_segmentation = True
                        split_points = suggested_points
                        print(f"{Fore.GREEN}✅ Using suggested split points{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED}❌ No suggested points available{Style.RESET_ALL}")
                        continue
                        
                elif choice == "3":
                    print(f"\n{Fore.CYAN}Enter split points:{Style.RESET_ALL}")
                    print(f"   Format: HH:MM:SS.mmm or MM:SS.mmm or seconds")
                    print(f"   Example: 30:00,1:00:00,1:30:00,2:00:00")
                    print(f"   Current duration: {format_seconds_to_timestamp(duration)}")
                    
                    split_input = input(f"\n{Fore.CYAN}Split points (comma-separated): {Style.RESET_ALL}").strip()
                    
                    if split_input:
                        try:
                            custom_points = []
                            for point_str in split_input.split(','):
                                point_str = point_str.strip()
                                if point_str:
                                    point_seconds = parse_timestamp(point_str)
                                    if 0 < point_seconds < duration:
                                        custom_points.append(point_seconds)
                                    else:
                                        print(f"{Fore.YELLOW}⚠️  Skipping invalid split point: {point_str} (out of range){Style.RESET_ALL}")
                            
                            if custom_points:
                                custom_points.sort()  # Sort in chronological order
                                use_segmentation = True
                                split_points = custom_points
                                
                                print(f"{Fore.GREEN}✅ Using custom split points:{Style.RESET_ALL}")
                                for i, point in enumerate(split_points):
                                    print(f"   {i+1}. {format_seconds_to_timestamp(point)}")
                                break
                            else:
                                print(f"{Fore.RED}❌ No valid split points provided{Style.RESET_ALL}")
                                continue
                                
                        except ValueError as e:
                            print(f"{Fore.RED}❌ Error parsing split points: {e}{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.YELLOW}⚠️  No split points entered, processing entire file{Style.RESET_ALL}")
                        break

                elif choice == "4":
                    print(f"\n{Fore.CYAN}Choose segment length:{Style.RESET_ALL}")
                    print(f"   1. {Fore.GREEN}5 minutes{Style.RESET_ALL} (for high memory constraints)")
                    print(f"   2. {Fore.YELLOW}10 minutes{Style.RESET_ALL} (balanced)")
                    print(f"   3. {Fore.CYAN}15 minutes{Style.RESET_ALL} (good for most files)")
                    print(f"   4. {Fore.MAGENTA}30 minutes{Style.RESET_ALL} (for long files)")
                    print(f"   5. {Fore.BLUE}Custom minutes{Style.RESET_ALL} (enter your own)")
                    
                    segment_choice = input(f"\n{Fore.CYAN}Select segment length (1-5): {Style.RESET_ALL}").strip()
                    
                    segment_length_map = {
                        "1": 300,   # 5 minutes
                        "2": 600,   # 10 minutes
                        "3": 900,   # 15 minutes
                        "4": 1800,  # 30 minutes
                    }
                    
                    if segment_choice in segment_length_map:
                        new_segment_length = segment_length_map[segment_choice]
                        minutes = new_segment_length // 60
                        print(f"{Fore.GREEN}✅ Using {minutes}-minute segments{Style.RESET_ALL}")
                        
                        # Regenerate split points with new length
                        suggested_points = suggest_split_points(duration, new_segment_length)
                        if suggested_points:
                            print(f"\n{Fore.CYAN}🎯 New split points (every {minutes} minutes):{Style.RESET_ALL}")
                            for i, point in enumerate(suggested_points):
                                timestamp = format_seconds_to_timestamp(point)
                                print(f"   {i+1}. {timestamp}")
                            
                            use_segmentation = True
                            split_points = suggested_points
                            break
                        else:
                            print(f"{Fore.YELLOW}⚠️  File is shorter than segment length, processing entire file{Style.RESET_ALL}")
                            break
                            
                    elif segment_choice == "5":
                        try:
                            custom_minutes = input(f"\n{Fore.CYAN}Enter segment length in minutes: {Style.RESET_ALL}").strip()
                            custom_length = int(float(custom_minutes) * 60)
                            
                            if custom_length > 0 and custom_length < duration:
                                print(f"{Fore.GREEN}✅ Using {custom_minutes}-minute segments{Style.RESET_ALL}")
                                
                                # Generate split points with custom length
                                suggested_points = suggest_split_points(duration, custom_length)
                                if suggested_points:
                                    print(f"\n{Fore.CYAN}🎯 Custom split points (every {custom_minutes} minutes):{Style.RESET_ALL}")
                                    for i, point in enumerate(suggested_points):
                                        timestamp = format_seconds_to_timestamp(point)
                                        print(f"   {i+1}. {timestamp}")
                                    
                                    use_segmentation = True
                                    split_points = suggested_points
                                    break
                                else:
                                    print(f"{Fore.YELLOW}⚠️  File is shorter than segment length, processing entire file{Style.RESET_ALL}")
                                    break
                            else:
                                print(f"{Fore.RED}❌ Invalid segment length. Must be positive and less than file duration.{Style.RESET_ALL}")
                                continue
                                
                        except ValueError:
                            print(f"{Fore.RED}❌ Invalid input. Please enter a valid number of minutes.{Style.RESET_ALL}")
                            continue
                    else:
                        print(f"{Fore.RED}❌ Invalid choice. Please select 1-5.{Style.RESET_ALL}")
                        continue
                        
                else:
                    print(f"{Fore.RED}❌ Invalid choice. Please select 1-4.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Processing entire file.{Style.RESET_ALL}")
                break
            except EOFError:
                print(f"\n{Fore.YELLOW}⚠️  Input ended. Processing entire file.{Style.RESET_ALL}")
                break
    
    # Process with segmentation if requested
    if use_segmentation and split_points and duration is not None:
        return process_with_segmentation(
            input_path_obj, split_points, duration, output_name, 
            output_directory, task, model_dir, ram_setting
        )
    
    # Standard processing for non-segmented files
    return process_single_file(
        input_path_obj, output_name, output_directory, 
        task, model_dir, ram_setting
    )

def process_with_segmentation(
    input_path_obj: Path, split_points: List[float], total_duration: float,
    output_name: str, output_directory: str, task: str, 
    model_dir: Optional[str], ram_setting: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """
    Process a long media file by splitting it into segments.
    
    Args:
        input_path_obj (Path): Path object for input file
        split_points (List[float]): List of split points in seconds
        total_duration (float): Total duration of the media file
        output_name (str): Base output name
        output_directory (str): Output directory
        task (str): Processing task type
        model_dir (Optional[str]): Model directory
        ram_setting (Optional[str]): RAM setting
        
    Returns:
        Tuple[Dict[str, Any], str]: Combined result and output filename
    """
    try:
        import tempfile
        import shutil
        
        # Create temporary directory for segments
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            segments_data = []
            
            # Create segment boundaries (include start and end)
            segment_boundaries = [0.0] + split_points + [total_duration]
            
            print(f"\n{Fore.CYAN}🔪 Creating {len(segment_boundaries) - 1} segments...{Style.RESET_ALL}")
            
            # Process each segment
            for i in range(len(segment_boundaries) - 1):
                start_time = segment_boundaries[i]
                end_time = segment_boundaries[i + 1]
                segment_duration = end_time - start_time
                
                print(f"\n{Fore.CYAN}📁 Segment {i + 1}/{len(segment_boundaries) - 1}:{Style.RESET_ALL}")
                print(f"   Time: {format_seconds_to_timestamp(start_time)} → {format_seconds_to_timestamp(end_time)}")
                print(f"   Duration: {format_human_time(segment_duration)}")
                
                # Create segment file
                segment_filename = f"segment_{i+1:03d}_{input_path_obj.stem}.{input_path_obj.suffix[1:]}"
                segment_path = temp_path / segment_filename
                
                print(f"   🔄 Extracting segment...")
                if not create_segment(str(input_path_obj), start_time, end_time, str(segment_path)):
                    raise RuntimeError(f"Failed to create segment {i + 1}")
                
                print(f"   ✅ Segment created: {segment_path.name}")
                
                # Process this segment
                try:
                    print(f"   🎵 Processing segment {i + 1}...")
                    
                    # Use the same processing logic as the main function
                    segment_result, _ = process_single_file(
                        segment_path, f"{output_name}_segment_{i+1:03d}", 
                        str(temp_path), task, model_dir, ram_setting
                    )
                    
                    # Store segment data with timing information
                    segments_data.append({
                        'result': segment_result,
                        'start_time': start_time,
                        'end_time': end_time,
                        'segment_index': i + 1
                    })
                    
                    print(f"   ✅ Segment {i + 1} processed: {len(segment_result.get('segments', []))} subtitles")
                    
                    # Free memory after each segment
                    del segment_result
                    gc.collect()
                    
                    # Clear CUDA cache if available
                    try:
                        import torch
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                    except ImportError:
                        pass
                        
                except Exception as e:
                    logger.error(f"Error processing segment {i + 1}: {e}")
                    print(f"   {Fore.RED}❌ Segment {i + 1} failed: {e}{Style.RESET_ALL}")
                    # Continue with other segments
                    continue
                
                finally:
                    # Clean up segment file
                    try:
                        if segment_path.exists():
                            segment_path.unlink()
                    except Exception:
                        pass
            
            if not segments_data:
                raise RuntimeError("No segments were successfully processed")
            
            print(f"\n{Fore.GREEN}🎉 All segments processed successfully!{Style.RESET_ALL}")
            print(f"   Total segments: {len(segments_data)}")
            
            # Combine all segment results
            print(f"{Fore.CYAN}🔗 Combining subtitles...{Style.RESET_ALL}")
            
            # Create combined result
            combined_segments = []
            combined_text_parts = []
            
            for segment_data in segments_data:
                segment_result = segment_data['result']
                time_offset = segment_data['start_time']
                
                # Adjust timing for each subtitle in this segment
                for segment in segment_result.get("segments", []):
                    if isinstance(segment, dict) and segment.get("text", "").strip():
                        adjusted_segment = segment.copy()
                        adjusted_segment["start"] = segment.get("start", 0.0) + time_offset
                        adjusted_segment["end"] = segment.get("end", 0.0) + time_offset
                        combined_segments.append(adjusted_segment)
                        combined_text_parts.append(segment.get("text", "").strip())
            
            # Create combined result
            combined_result = {
                "segments": combined_segments,
                "text": " ".join(combined_text_parts),
                "language": segments_data[0]['result'].get('language', 'en') if segments_data else 'en'
            }
            
            # Save combined subtitle file
            output_directory_obj = Path(output_directory)
            if not output_directory_obj.exists():
                output_directory_obj.mkdir(parents=True, exist_ok=True)
                
            output_path = output_directory_obj / f"{output_name}.srt"
            combine_segment_subtitles(segments_data, str(output_path))
            
            print(f"{Fore.GREEN}✅ Segmented processing complete!{Style.RESET_ALL}")
            print(f"   Combined subtitles: {len(combined_segments)} entries")
            print(f"   Output file: {output_path}")
            
            return combined_result, output_name
            
    except Exception as e:
        logger.error(f"Segmentation processing failed: {e}")
        raise RuntimeError(f"Segmented processing failed: {str(e)}")

def process_single_file(
    input_path_obj: Path, output_name: str, output_directory: str,
    task: str, model_dir: Optional[str], ram_setting: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """
    Process a single media file (original processing logic).
    
    Args:
        input_path_obj (Path): Path to input file
        output_name (str): Output name
        output_directory (str): Output directory  
        task (str): Processing task
        model_dir (Optional[str]): Model directory
        ram_setting (Optional[str]): RAM setting
        
    Returns:
        Tuple[Dict[str, Any], str]: Result and output filename
    """
    if task not in ["transcribe", "translate"]:
        raise ValueError("Task must be either 'transcribe' or 'translate'")
    
    output_directory_obj = Path(output_directory)
    if not output_directory_obj.exists():
        output_directory_obj.mkdir(parents=True, exist_ok=True)

    # Vocal isolation step if requested
    processed_audio_path = str(input_path_obj)
    if getattr(args, 'isolate_vocals', False):
        import shutil, tempfile, os
        if not shutil.which('demucs'):
            raise RuntimeError("demucs is not installed or not in PATH. Please install demucs to use --isolate_vocals.")
        
        # Determine which Demucs model to use
        selected_model = getattr(args, 'demucs_model', None)
        
        if selected_model and selected_model != 'htdemucs':
            # User specified a model via command line
            print(f"{Fore.GREEN}✅ Using specified Demucs model: {selected_model}{Style.RESET_ALL}")
            
            # Show model info
            model_info = {
                "htdemucs": "Latest Hybrid Transformer model (default)",
                "htdemucs_ft": "Fine-tuned version for better quality",
                "htdemucs_6s": "6-source separation (includes piano/guitar)",
                "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                "mdx": "Frequency-domain model, MDX winner",
                "mdx_extra": "Enhanced MDX with extra training data",
                "mdx_q": "Quantized MDX (faster, smaller)",
                "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                "hdemucs": "Original Hybrid Demucs v3",
                "demucs": "Original time-domain Demucs"
            }
            print(f"{Fore.CYAN}ℹ️  {model_info.get(selected_model, 'Unknown model')}{Style.RESET_ALL}")
            
        else:
            # Ask user which Demucs model to use
            print(f"\n{Fore.CYAN}🎛️ Demucs Model Selection for Vocal Isolation:{Style.RESET_ALL}")
            print(f"   Available models:")
            print(f"   1. {Fore.YELLOW}htdemucs{Style.RESET_ALL} (default, Hybrid Transformer v4)")
            print(f"   2. {Fore.YELLOW}htdemucs_ft{Style.RESET_ALL} (fine-tuned htdemucs, better quality, slower)")
            print(f"   3. {Fore.YELLOW}htdemucs_6s{Style.RESET_ALL} (6-source: drums, bass, other, vocals, piano, guitar)")
            print(f"   4. {Fore.YELLOW}hdemucs_mmi{Style.RESET_ALL} (Hybrid Demucs v3, MusDB + 800 songs)")
            print(f"   5. {Fore.YELLOW}mdx{Style.RESET_ALL} (MDX challenge Track A winner)")
            print(f"   6. {Fore.YELLOW}mdx_extra{Style.RESET_ALL} (MDX Track B, trained with extra data)")
            print(f"   7. {Fore.YELLOW}mdx_q{Style.RESET_ALL} (quantized mdx, smaller/faster)")
            print(f"   8. {Fore.YELLOW}mdx_extra_q{Style.RESET_ALL} (quantized mdx_extra, smaller/faster)")
            print(f"   9. {Fore.YELLOW}hdemucs{Style.RESET_ALL} (original Hybrid Demucs v3)")
            print(f"  10. {Fore.YELLOW}demucs{Style.RESET_ALL} (original time-domain Demucs)")
            
            print(f"\n{Fore.CYAN}💡 Recommendations:{Style.RESET_ALL}")
            print(f"   🎯 {Fore.GREEN}Best Quality{Style.RESET_ALL}: htdemucs_ft (fine-tuned)")
            print(f"   🎯 {Fore.BLUE}Fastest{Style.RESET_ALL}: mdx_q or mdx_extra_q (quantized)")
            print(f"   🎯 {Fore.MAGENTA}Detailed Separation{Style.RESET_ALL}: htdemucs_6s (6 sources)")
            print(f"   🎯 {Fore.CYAN}Balanced{Style.RESET_ALL}: mdx_extra (good quality + speed)")
            print(f"   🎯 {Fore.YELLOW}Legacy/Compatibility{Style.RESET_ALL}: hdemucs or demucs")
            
            # Get user choice
            while True:
                try:
                    model_choice = input(f"\n{Fore.CYAN}Select Demucs model (1-10, or Enter for default htdemucs): {Style.RESET_ALL}").strip()
                    
                    if not model_choice:  # User pressed Enter for default
                        selected_model = "htdemucs"
                        print(f"{Fore.GREEN}✅ Using default model: {selected_model}{Style.RESET_ALL}")
                        break
                    
                    model_map = {
                        "1": "htdemucs",
                        "2": "htdemucs_ft", 
                        "3": "htdemucs_6s",
                        "4": "hdemucs_mmi",
                        "5": "mdx",
                        "6": "mdx_extra",
                        "7": "mdx_q",
                        "8": "mdx_extra_q",
                        "9": "hdemucs",
                        "10": "demucs"
                    }
                    
                    if model_choice in model_map:
                        selected_model = model_map[model_choice]
                        print(f"{Fore.GREEN}✅ Selected model: {selected_model}{Style.RESET_ALL}")
                        
                        # Show model info
                        model_info = {
                            "htdemucs": "Latest Hybrid Transformer model (default)",
                            "htdemucs_ft": "Fine-tuned version for better quality",
                            "htdemucs_6s": "6-source separation (includes piano/guitar)",
                            "hdemucs_mmi": "Hybrid v3 trained on expanded dataset",
                            "mdx": "Frequency-domain model, MDX winner",
                            "mdx_extra": "Enhanced MDX with extra training data",
                            "mdx_q": "Quantized MDX (faster, smaller)",
                            "mdx_extra_q": "Quantized MDX Extra (faster, smaller)",
                            "hdemucs": "Original Hybrid Demucs v3",
                            "demucs": "Original time-domain Demucs"
                        }
                        
                        print(f"{Fore.CYAN}ℹ️  {model_info[selected_model]}{Style.RESET_ALL}")
                        break
                    else:
                        print(f"{Fore.RED}❌ Invalid choice. Please select 1-10 or press Enter for default.{Style.RESET_ALL}")
                        
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}⚠️  Operation cancelled. Using default model: htdemucs{Style.RESET_ALL}")
                    selected_model = "htdemucs"
                    break
                except EOFError:
                    print(f"\n{Fore.YELLOW}⚠️  Input ended. Using default model: htdemucs{Style.RESET_ALL}")
                    selected_model = "htdemucs"
                    break
        
        try:
            print(f"\n{Fore.CYAN}🔄 Isolating vocals from input audio using Demucs model: {selected_model}...{Style.RESET_ALL}")
            with tempfile.TemporaryDirectory() as tmpdir:
                # Run demucs CLI to separate vocals with proper encoding and selected model
                result = subprocess.run([
                    'demucs',
                    '-n', selected_model,
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
                
                # Try different possible output locations based on selected model
                possible_locations = [
                    os.path.join(tmpdir, selected_model, base_name, 'vocals.wav'),  # Model-specific location
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
            subtitle_index = 1
            for segment in filtered_segments:
                # Write SRT format: index, timestamp, text, blank line
                start_time = format_timestamp(segment.get("start", 0.0))
                end_time = format_timestamp(segment.get("end", 0.0))
                text = segment.get("text", "").strip()
                
                # Filter unwanted phrases
                filtered_text = filter_unwanted_phrases(text)
                
                # Only write if text remains after filtering
                if filtered_text:
                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{filtered_text}\n\n")
                    subtitle_index += 1
        
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