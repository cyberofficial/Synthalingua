"""
Video Processor Module

Handles video file loading, metadata extraction, and audio extraction for
transcription. Leverages FFmpeg for reliable video/audio processing.

This module extends the existing audio extraction logic from sub_gen.py
to work with video files and support chunked extraction for buffering.
"""

import os
import subprocess
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional, List
import tempfile

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Manages video file processing including metadata extraction and audio extraction.
    
    Attributes:
        video_path (str): Path to the input video file
        temp_dir (str): Temporary directory for processed files
        metadata (dict): Video metadata (duration, fps, resolution, etc.)
    """
    
    # Supported video formats
    SUPPORTED_FORMATS = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v']
    
    def __init__(self, video_path: str, temp_dir: Optional[str] = None):
        """
        Initialize Video Processor.
        
        Args:
            video_path: Path to the input video file
            temp_dir: Optional temporary directory (will create if not provided)
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format is not supported
        """
        self.video_path: Path = Path(video_path)
        
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        if self.video_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video format: {self.video_path.suffix}\n"
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Set up temporary directory
        if temp_dir:
            self.temp_dir: Path = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir: Path = Path(tempfile.mkdtemp(prefix="synth_video_"))
        
        self.metadata: Dict = {}
        self.audio_path: Optional[str] = None
        
        logger.info(f"VideoProcessor initialized for: {self.video_path}")
    
    def extract_metadata(self) -> Dict:
        """
        Extract video metadata using FFprobe.
        
        Returns:
            dict: Video metadata including:
                - duration: Video duration in seconds
                - fps: Frames per second
                - width: Video width in pixels
                - height: Video height in pixels
                - audio_codec: Audio codec name
                - video_codec: Video codec name
                - bit_rate: Overall bit rate
                
        Raises:
            RuntimeError: If FFprobe fails
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(self.video_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            probe_data = json.loads(result.stdout)
            
            # Extract format information
            format_info = probe_data.get('format', {})
            duration = float(format_info.get('duration', 0))
            bit_rate = int(format_info.get('bit_rate', 0))
            
            # Extract stream information
            video_stream = None
            audio_stream = None
            
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            # Build metadata dictionary
            self.metadata = {
                'duration': duration,
                'bit_rate': bit_rate,
                'format': format_info.get('format_name', 'unknown'),
            }
            
            if video_stream:
                # Calculate FPS from frame rate
                fps_str = video_stream.get('r_frame_rate', '0/1')
                if '/' in fps_str:
                    num, den = map(float, fps_str.split('/'))
                    fps = num / den if den != 0 else 0
                else:
                    fps = float(fps_str)
                
                self.metadata.update({
                    'width': video_stream.get('width', 0),
                    'height': video_stream.get('height', 0),
                    'fps': round(fps, 2),
                    'video_codec': video_stream.get('codec_name', 'unknown'),
                })
            
            if audio_stream:
                self.metadata.update({
                    'audio_codec': audio_stream.get('codec_name', 'unknown'),
                    'audio_sample_rate': audio_stream.get('sample_rate', 'unknown'),
                    'audio_channels': audio_stream.get('channels', 0),
                })
            else:
                logger.warning(f"No audio stream found in video: {self.video_path}")
            
            logger.info(f"Extracted metadata: duration={duration:.2f}s, "
                       f"resolution={self.metadata.get('width')}x{self.metadata.get('height')}, "
                       f"fps={self.metadata.get('fps')}")
            
            return self.metadata
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe failed: {e}")
            raise RuntimeError(f"Failed to extract video metadata: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse FFprobe output: {e}")
            raise RuntimeError(f"Failed to parse video metadata: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during metadata extraction: {e}")
            raise RuntimeError(f"Failed to extract metadata: {e}")
    
    def extract_audio(self, 
                     output_path: Optional[str] = None,
                     sample_rate: int = 16000,
                     channels: int = 1) -> str:
        """
        Extract complete audio from video file.
        
        Args:
            output_path: Optional custom output path for audio file
            sample_rate: Audio sample rate (default: 16000 Hz for Whisper)
            channels: Number of audio channels (default: 1 for mono)
            
        Returns:
            str: Path to extracted audio file
            
        Raises:
            RuntimeError: If audio extraction fails
        """
        # Handle None case by creating default path
        if not output_path:
            output_path_obj: Path = self.temp_dir / f"{self.video_path.stem}_audio.wav"
        else:
            output_path_obj: Path = Path(output_path) if not isinstance(output_path, Path) else output_path
        
        output_path_str: str = str(output_path_obj)
        
        try:
            cmd = [
                'ffmpeg',
                '-i', str(self.video_path),
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # PCM 16-bit little-endian
                '-ar', str(sample_rate),  # Sample rate
                '-ac', str(channels),  # Audio channels
                '-y',  # Overwrite output file
                output_path_str
            ]
            
            logger.info(f"Extracting audio to: {output_path_str}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path_obj.exists():
                raise RuntimeError("Audio file was not created")
            
            self.audio_path = output_path_str
            logger.info(f"Audio extraction complete: {output_path_str}")
            
            return output_path_str
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio extraction failed: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise RuntimeError(f"Failed to extract audio: {e}")
    
    def extract_audio_segment(self,
                             start_time: float,
                             duration: float,
                             output_path: Optional[str] = None,
                             sample_rate: int = 16000,
                             channels: int = 1) -> str:
        """
        Extract a specific audio segment from video (for buffering).
        
        Args:
            start_time: Start time in seconds
            duration: Duration of segment in seconds
            output_path: Optional custom output path for audio file
            sample_rate: Audio sample rate (default: 16000 Hz)
            channels: Number of audio channels (default: 1 for mono)
            
        Returns:
            str: Path to extracted audio segment file
            
        Raises:
            RuntimeError: If audio extraction fails
        """
        # Handle None case by creating default path
        if not output_path:
            output_path_obj: Path = self.temp_dir / f"{self.video_path.stem}_audio_{start_time}_{duration}.wav"
        else:
            output_path_obj: Path = Path(output_path) if not isinstance(output_path, Path) else output_path
        
        output_path_str: str = str(output_path_obj)
        
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),  # Start time
                '-i', str(self.video_path),
                '-t', str(duration),  # Duration
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-y',
                output_path_str
            ]
            
            logger.debug(f"Extracting audio segment: {start_time}s - {start_time + duration}s")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if not output_path_obj.exists():
                raise RuntimeError("Audio segment file was not created")
            
            logger.debug(f"Audio segment extracted: {output_path_str}")
            return output_path_str
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg segment extraction failed: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio segment: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during segment extraction: {e}")
            raise RuntimeError(f"Failed to extract audio segment: {e}")
    
    def get_video_info_str(self) -> str:
        """
        Get a formatted string of video information.
        
        Returns:
            str: Formatted video information
        """
        if not self.metadata:
            self.extract_metadata()
        
        info_lines = [
            f"Video: {self.video_path.name}",
            f"Duration: {self._format_duration(self.metadata.get('duration', 0))}",
            f"Resolution: {self.metadata.get('width')}x{self.metadata.get('height')}",
            f"FPS: {self.metadata.get('fps', 0):.2f}",
            f"Video Codec: {self.metadata.get('video_codec', 'unknown')}",
            f"Audio Codec: {self.metadata.get('audio_codec', 'unknown')}",
        ]
        
        return "\n".join(info_lines)
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Format duration in seconds to HH:MM:SS.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            str: Formatted duration string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            if self.audio_path and Path(self.audio_path).exists():
                Path(self.audio_path).unlink()
                logger.info(f"Cleaned up audio file: {self.audio_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup audio file: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
