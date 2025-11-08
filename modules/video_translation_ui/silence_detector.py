"""
Silence Detection Module for Video Translation UI

Detects speech and silence regions in audio to enable selective processing.
Only transcribes speech sections for accurate, phrase-level caption timing.

Based on the silence detection implementation from sub_gen.py.
"""

import os
import logging
import subprocess
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class SilenceDetector:
    """
    Detects speech and silence regions in audio files.
    
    Uses RMS energy analysis to identify speech vs silence regions,
    enabling efficient processing of only the spoken content.
    """
    
    def __init__(self,
                 silence_threshold_db: float = -35.0,
                 min_silence_duration: float = 0.5,
                 min_speech_duration: float = 0.1):
        """
        Initialize Silence Detector.
        
        Args:
            silence_threshold_db: dB threshold below which audio is considered silent
            min_silence_duration: Minimum duration in seconds for a region to be silence
            min_speech_duration: Minimum duration in seconds for a region to be speech
        """
        self.silence_threshold_db = silence_threshold_db
        self.min_silence_duration = min_silence_duration
        self.min_speech_duration = min_speech_duration
        
        logger.info(f"SilenceDetector initialized: threshold={silence_threshold_db}dB, "
                   f"min_silence={min_silence_duration}s, min_speech={min_speech_duration}s")
    
    def detect_regions(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Detect silence and speech regions in audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of regions with type, start, and end times:
            [{'type': 'speech', 'start': 13.8, 'end': 42.3, 'avg_db': -25.4}, ...]
        """
        try:
            # Load audio using Whisper's audio loading (more reliable)
            import whisper
            audio = whisper.load_audio(audio_path)
            sr = 16000  # Whisper uses 16kHz sample rate
            
            logger.info(f"Analyzing audio for speech/silence regions...")
            
            # Convert dB threshold to linear amplitude
            silence_threshold_linear = 10 ** (self.silence_threshold_db / 20.0)
            
            # Calculate frame-wise RMS energy with overlapping windows
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop (overlap for smoother detection)
            
            # Calculate RMS for each frame
            rms_frames = []
            for i in range(0, len(audio) - frame_length + 1, hop_length):
                frame = audio[i:i + frame_length]
                rms = np.sqrt(np.mean(frame ** 2))
                rms_frames.append(rms)
            
            # Create time axis for frames
            frame_times = np.arange(len(rms_frames)) * hop_length / sr
            
            # Detect silence/speech regions
            is_silent = np.array(rms_frames) < silence_threshold_linear
            
            # Find transitions between silence and speech
            transitions = []
            current_state = is_silent[0]
            current_start = 0.0
            current_rms_values = []
            
            for i, silent in enumerate(is_silent[1:], 1):
                current_rms_values.append(rms_frames[i])
                
                if silent != current_state:
                    # State changed - save current region
                    region_end = frame_times[i]
                    region_duration = region_end - current_start
                    region_type = 'silence' if current_state else 'speech'
                    
                    # Calculate average dB for this region
                    if current_rms_values:
                        avg_rms = np.mean(current_rms_values)
                        avg_db = 20 * np.log10(avg_rms + 1e-10)  # Add small value to avoid log(0)
                    else:
                        avg_db = -100.0
                    
                    # Only add regions that meet minimum duration requirements
                    if region_type == 'silence' and region_duration >= self.min_silence_duration:
                        transitions.append({
                            'type': 'silence',
                            'start': current_start,
                            'end': region_end,
                            'duration': region_duration,
                            'avg_db': avg_db
                        })
                    elif region_type == 'speech' and region_duration >= self.min_speech_duration:
                        transitions.append({
                            'type': 'speech',
                            'start': current_start,
                            'end': region_end,
                            'duration': region_duration,
                            'avg_db': avg_db
                        })
                    
                    # Start new region
                    current_state = silent
                    current_start = region_end
                    current_rms_values = []
            
            # Add final region
            audio_duration = len(audio) / sr
            final_region_type = 'silence' if current_state else 'speech'
            final_duration = audio_duration - current_start
            
            if current_rms_values:
                avg_rms = np.mean(current_rms_values)
                avg_db = 20 * np.log10(avg_rms + 1e-10)
            else:
                avg_db = -100.0
            
            if final_region_type == 'silence' and final_duration >= self.min_silence_duration:
                transitions.append({
                    'type': 'silence',
                    'start': current_start,
                    'end': audio_duration,
                    'duration': final_duration,
                    'avg_db': avg_db
                })
            elif final_region_type == 'speech' and final_duration >= self.min_speech_duration:
                transitions.append({
                    'type': 'speech',
                    'start': current_start,
                    'end': audio_duration,
                    'duration': final_duration,
                    'avg_db': avg_db
                })
            
            # Merge adjacent speech regions separated by very short silences
            merged_regions = []
            for region in transitions:
                if not merged_regions:
                    merged_regions.append(region)
                    continue
                
                last_region = merged_regions[-1]
                
                # If both are speech and separated by less than 0.3s, merge them
                if (region['type'] == 'speech' and 
                    last_region['type'] == 'speech' and 
                    region['start'] - last_region['end'] < 0.3):
                    # Merge by extending the last region
                    last_region['end'] = region['end']
                    last_region['duration'] = last_region['end'] - last_region['start']
                    last_region['avg_db'] = (last_region['avg_db'] + region['avg_db']) / 2
                else:
                    merged_regions.append(region)
            
            # Filter and calculate statistics
            speech_regions = [r for r in merged_regions if r['type'] == 'speech']
            silence_regions = [r for r in merged_regions if r['type'] == 'silence']
            
            total_speech_duration = sum(r['duration'] for r in speech_regions)
            total_silence_duration = sum(r['duration'] for r in silence_regions)
            
            workload_reduction = (total_silence_duration / audio_duration) * 100 if audio_duration > 0 else 0
            
            logger.info(f"Audio analysis complete:")
            logger.info(f"  • Speech regions: {len(speech_regions)} ({total_speech_duration:.1f}s)")
            logger.info(f"  • Silence regions: {len(silence_regions)} ({total_silence_duration:.1f}s)")
            logger.info(f"  • Processing efficiency: {100 * total_speech_duration / audio_duration:.1f}% of audio contains speech")
            logger.info(f"  • Workload reduction: {workload_reduction:.1f}% (skipping silence)")
            
            return merged_regions
            
        except Exception as e:
            logger.error(f"Failed to detect silence regions: {e}", exc_info=True)
            # Fallback: return single speech region covering entire audio
            try:
                # Get audio duration using ffprobe
                result = subprocess.run(
                    ['ffprobe', '-v', 'error', '-show_entries', 
                     'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
                    capture_output=True,
                    text=True
                )
                duration = float(result.stdout.strip())
                
                logger.warning(f"Silence detection failed, treating entire audio as speech ({duration:.1f}s)")
                return [{
                    'type': 'speech',
                    'start': 0.0,
                    'end': duration,
                    'duration': duration,
                    'avg_db': -30.0
                }]
            except:
                logger.error("Failed to get audio duration for fallback")
                return []
    
    def get_speech_regions(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Get only the speech regions from audio.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of speech regions only (filters out silence)
        """
        all_regions = self.detect_regions(audio_path)
        speech_regions = [r for r in all_regions if r['type'] == 'speech']
        
        logger.debug(f"Found {len(speech_regions)} speech regions in audio")
        return speech_regions
    
    def group_speech_regions_by_silence(self, regions: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group consecutive speech regions separated by silence into batches.
        
        Args:
            regions: List of regions with 'type', 'start', 'end', etc.
            
        Returns:
            List of groups, each a list of consecutive speech regions
        """
        groups = []
        current_group = []
        
        for region in regions:
            if region['type'] == 'speech':
                current_group.append(region)
            else:
                # Silence region - finalize current group if it has content
                if current_group:
                    groups.append(current_group)
                    current_group = []
        
        # Add final group if it has content
        if current_group:
            groups.append(current_group)
        
        logger.debug(f"Grouped speech regions into {len(groups)} batches")
        return groups
    
    def extract_speech_region(self,
                             input_audio_path: str,
                             output_audio_path: str,
                             start_time: float,
                             end_time: float) -> bool:
        """
        Extract a speech region from audio file using FFmpeg.
        
        Args:
            input_audio_path: Source audio file
            output_audio_path: Destination for extracted region
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            True if extraction succeeded, False otherwise
        """
        try:
            # Use FFmpeg to extract the speech region with high precision
            ffmpeg_command = [
                'ffmpeg', '-y', '-i', input_audio_path,
                '-ss', str(start_time),
                '-to', str(end_time),
                '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
                output_audio_path
            ]
            
            result = subprocess.run(
                ffmpeg_command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg extraction failed: {result.stderr}")
                return False
            
            logger.debug(f"Extracted speech region: {start_time:.2f}s - {end_time:.2f}s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to extract speech region: {e}", exc_info=True)
            return False
    
    def get_statistics(self, regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about detected regions.
        
        Args:
            regions: List of detected regions
            
        Returns:
            Dictionary with statistics
        """
        speech_regions = [r for r in regions if r['type'] == 'speech']
        silence_regions = [r for r in regions if r['type'] == 'silence']
        
        total_speech_duration = sum(r['duration'] for r in speech_regions)
        total_silence_duration = sum(r['duration'] for r in silence_regions)
        total_duration = total_speech_duration + total_silence_duration
        
        return {
            'total_regions': len(regions),
            'speech_regions': len(speech_regions),
            'silence_regions': len(silence_regions),
            'total_speech_duration': round(total_speech_duration, 2),
            'total_silence_duration': round(total_silence_duration, 2),
            'total_duration': round(total_duration, 2),
            'speech_percentage': round(100 * total_speech_duration / total_duration, 2) if total_duration > 0 else 0,
            'workload_reduction': round(100 * total_silence_duration / total_duration, 2) if total_duration > 0 else 0,
        }
