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
import time

# Import Demucs helper
from modules.demucs_path_helper import get_demucs_python_path

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Manages video file processing including metadata extraction and audio extraction.
    
    Attributes:
        video_path (str): Path to the input video file
        temp_dir (str): Temporary directory for processed files
        metadata (dict): Video metadata (duration, fps, resolution, etc.)
    """
    
    # Supported video and audio formats
    SUPPORTED_FORMATS = [
        # Video formats
        '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v',
        # Audio formats (will be converted to video with black square)
        '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.wma'
    ]
    
    def __init__(self, video_path: str, temp_dir: Optional[str] = None, device: str = 'auto'):
        """
        Initialize Video Processor.
        
        Args:
            video_path: Path to the input video or audio file
            temp_dir: Optional temporary directory (will create if not provided)
            device: Device to use for encoding ('auto', 'cpu', 'cuda'). Default 'auto' uses CUDA if available.
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format is not supported
        """
        self.video_path: Path = Path(video_path)
        
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
            
        if self.video_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video/audio format: {self.video_path.suffix}\n"
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # Set up temporary directory
        if temp_dir:
            self.temp_dir: Path = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_dir: Path = Path(tempfile.mkdtemp(prefix="synth_video_"))
        
        # Store device for encoding (auto-detect CUDA if 'auto')
        if device and device.lower() == 'auto':
            # Auto-detect: Use CUDA if available, otherwise CPU
            try:
                import torch
                if torch.cuda.is_available():
                    self.device = 'cuda'
                    logger.info(f"CUDA detected and will be used for video encoding (GPU: {torch.cuda.get_device_name(0)})")
                else:
                    self.device = 'cpu'
                    logger.info("CUDA not available, using CPU for video encoding")
            except ImportError:
                self.device = 'cpu'
                logger.info("PyTorch not available, using CPU for video encoding")
        else:
            self.device: str = device.lower() if device else 'cpu'
            if self.device == 'cuda':
                logger.info("CUDA explicitly requested for video encoding")
        
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
    
    def convert_to_mp4(self, output_path: Optional[str] = None) -> str:
        """
        Convert video to MP4 format for browser compatibility.
        
        This ensures HTML5 video player can play any uploaded video format.
        Uses lossless conversion when possible (stream copy).
        For audio-only files, creates a 100x100 black square video.
        
        Args:
            output_path: Optional custom output path for MP4 file
            
        Returns:
            str: Path to converted MP4 file
            
        Raises:
            RuntimeError: If conversion fails
        """
        # If already MP4, just return the original path
        if self.video_path.suffix.lower() == '.mp4':
            logger.info(f"Video is already MP4 format: {self.video_path}")
            return str(self.video_path)
        
        # Create output path
        if not output_path:
            output_path_obj: Path = self.temp_dir / f"{self.video_path.stem}_converted.mp4"
        else:
            output_path_obj: Path = Path(output_path) if not isinstance(output_path, Path) else output_path
        
        output_path_str: str = str(output_path_obj)
        
        try:
            # Extract metadata to check if this is audio-only
            if not self.metadata:
                self.extract_metadata()
            
            has_video = 'width' in self.metadata and self.metadata.get('width', 0) > 0
            has_audio = 'audio_codec' in self.metadata
            
            logger.info(f"Converting {self.video_path.suffix} to MP4 for browser compatibility...")
            logger.info(f"  Input: {self.video_path}")
            logger.info(f"  Output: {output_path_str}")
            logger.info(f"  Has video: {has_video}, Has audio: {has_audio}")
            
            if has_video:
                # Video file: Convert to MP4 H.264 with YUV420p for browser compatibility
                # Preserve source resolution, FPS, and bitrate
                video_codec = self.metadata.get('video_codec', '').lower()
                
                # Get video metadata
                width = self.metadata.get('width', 0)
                height = self.metadata.get('height', 0)
                fps = self.metadata.get('fps', 24)
                bit_rate = self.metadata.get('bit_rate', 0)
                
                logger.info(f"  Preserving source resolution: {width}x{height} @ {fps}fps")
                
                # No scaling - keep original resolution
                scale_filter = []
                
                # Use original bitrate if available, otherwise auto
                bitrate_param = []
                if bit_rate > 0:
                    bitrate_mb = bit_rate / 1_000_000  # Convert to Mbps
                    logger.info(f"  Using source bitrate: {bitrate_mb:.1f} Mbps")
                    bitrate_param = ['-b:v', str(bit_rate)]
                
                # Check if CUDA encoding should be used
                use_cuda = self.device == 'cuda'
                
                if use_cuda:
                    logger.info(f"  Converting to H.264 with YUV420p (CUDA-accelerated)")
                    video_codec_param = [
                        '-c:v', 'h264_nvenc',
                        '-preset', 'p7',           # Highest quality
                        '-pix_fmt', 'yuv420p',     # Browser compatible
                        '-profile:v', 'high',
                        '-r', str(fps)             # Preserve source FPS
                    ]
                    if bitrate_param:
                        video_codec_param.extend(bitrate_param)
                    else:
                        video_codec_param.extend(['-rc:v', 'vbr', '-cq:v', '19'])  # High quality VBR
                    
                    fallback_video_codec_param = [
                        '-c:v', 'libx264',
                        '-preset', 'slow',
                        '-pix_fmt', 'yuv420p',
                        '-profile:v', 'high',
                        '-r', str(fps)
                    ]
                    if bitrate_param:
                        fallback_video_codec_param.extend(bitrate_param)
                    else:
                        fallback_video_codec_param.extend(['-crf', '18'])
                else:
                    logger.info(f"  Converting to H.264 with YUV420p (CPU encoding)")
                    video_codec_param = [
                        '-c:v', 'libx264',
                        '-preset', 'slow',
                        '-pix_fmt', 'yuv420p',
                        '-profile:v', 'high',
                        '-r', str(fps)             # Preserve source FPS
                    ]
                    if bitrate_param:
                        video_codec_param.extend(bitrate_param)
                    else:
                        video_codec_param.extend(['-crf', '18'])
                    scale_filter = []
                
                # Audio: copy if AAC, otherwise encode to AAC
                audio_codec = self.metadata.get('audio_codec', '').lower()
                
                if audio_codec == 'aac':
                    logger.info(f"  Audio is already AAC, using stream copy")
                    audio_codec_param = ['-c:a', 'copy']
                else:
                    logger.info(f"  Re-encoding audio to AAC (320kbps for quality)")
                    audio_codec_param = ['-c:a', 'aac', '-b:a', '320k']
                
                cmd = [
                    'ffmpeg',
                    '-i', str(self.video_path),
                    *scale_filter,  # Add scale filter if resolution exceeds 1080p
                    *video_codec_param,
                    *audio_codec_param,
                    '-movflags', '+faststart',  # Enable streaming
                    '-y',  # Overwrite output file
                    output_path_str
                ]
                
            elif has_audio:
                # Audio-only file: Create 100x100 black square video
                logger.info(f"  Audio-only file detected, creating 100x100 black square video")
                cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', 'color=c=black:s=100x100:r=1',  # 100x100 black square at 1 fps
                    '-i', str(self.video_path),
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',  # Fast encoding for tiny video
                    '-crf', '23',  # Standard quality (tiny overhead anyway)
                    '-pix_fmt', 'yuv420p',  # Browser compatibility
                    '-profile:v', 'high',  # H.264 High Profile
                    '-level', '4.1',  # Compatible with most devices
                    '-c:a', 'aac',
                    '-b:a', '320k',  # High quality audio
                    '-shortest',  # Match audio duration
                    '-movflags', '+faststart',
                    '-y',
                    output_path_str
                ]
            else:
                raise RuntimeError("File has neither video nor audio streams")
            
            logger.info(f"Running FFmpeg conversion...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            # If CUDA encoding failed and we were using CUDA, try CPU fallback
            if result.returncode != 0 and use_cuda and has_video:
                logger.warning(f"  CUDA hardware acceleration failed, falling back to CPU encoding...")
                logger.debug(f"  CUDA error: {result.stderr}")
                
                # Clean up failed output file if it exists
                if output_path_obj.exists():
                    output_path_obj.unlink()
                
                # Build fallback command with CPU encoding
                fallback_cmd = [
                    'ffmpeg',
                    '-i', str(self.video_path),
                    *scale_filter,  # Add scale filter if resolution exceeds 1080p
                    *fallback_video_codec_param,
                    *audio_codec_param,
                    '-movflags', '+faststart',
                    '-y',
                    output_path_str
                ]
                
                logger.info(f"  Retrying with CPU encoding...")
                result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            
            # Check if conversion was successful
            if result.returncode != 0:
                logger.error(f"FFmpeg conversion failed with exit code {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr}")
                raise RuntimeError(f"Failed to convert video to MP4: FFmpeg returned error code {result.returncode}")
            
            if not output_path_obj.exists():
                raise RuntimeError("MP4 file was not created")
            
            original_size_mb = self.video_path.stat().st_size / (1024 * 1024)
            output_size_mb = output_path_obj.stat().st_size / (1024 * 1024)
            
            # Determine which encoder was actually used
            if has_video:
                encoder_type = "CUDA-accelerated" if (use_cuda and result.returncode == 0 and 'nvenc' in ' '.join(cmd)) else "CPU"
                logger.info(f"✅ Video conversion complete using {encoder_type} encoding: {output_path_str}")
            else:
                logger.info(f"✅ Audio-to-video conversion complete: {output_path_str}")
            
            logger.info(f"   Original: {original_size_mb:.2f} MB → Output: {output_size_mb:.2f} MB")
            
            return output_path_str
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            logger.error(f"FFmpeg stderr: {e.stderr}")
            raise RuntimeError(f"Failed to convert video to MP4: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during video conversion: {e}")
            raise RuntimeError(f"Failed to convert video: {e}")
    
    def extract_audio(self, 
                     output_path: Optional[str] = None,
                     sample_rate: int = 16000,
                     channels: int = 1,
                     isolate_vocals: bool = False,
                     demucs_model: str = "htdemucs",
                     demucs_jobs: int = 0) -> str:
        """
        Extract complete audio from video file, optionally with vocal isolation.
        
        Args:
            output_path: Optional custom output path for audio file
            sample_rate: Audio sample rate (default: 16000 Hz for Whisper)
            channels: Number of audio channels (default: 1 for mono)
            isolate_vocals: Whether to use Demucs vocal isolation
            demucs_model: Demucs model to use for vocal isolation
            demucs_jobs: Number of parallel jobs for Demucs (0 = single-threaded)
            
        Returns:
            str: Path to extracted/processed audio file
            
        Raises:
            RuntimeError: If audio extraction or vocal isolation fails
        """
        # Handle None case by creating default path
        if not output_path:
            output_path_obj: Path = self.temp_dir / f"{self.video_path.stem}_audio.wav"
        else:
            output_path_obj: Path = Path(output_path) if not isinstance(output_path, Path) else output_path
        
        output_path_str: str = str(output_path_obj)
        
        try:
            # Step 1: Extract raw audio from video
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
            
            logger.info(f"Audio extraction complete: {output_path_str}")
            
            # Step 2: Vocal isolation with Demucs (if enabled)
            if isolate_vocals:
                logger.info(f" Starting vocal isolation with Demucs model: {demucs_model}")
                processed_audio_path = self._isolate_vocals_demucs(
                    output_path_str,
                    demucs_model,
                    demucs_jobs
                )
                
                # Replace original audio with isolated vocals
                if processed_audio_path != output_path_str:
                    # Move vocals file to replace original
                    import shutil
                    shutil.move(processed_audio_path, output_path_str)
                    logger.info(f"Replaced audio with isolated vocals: {output_path_str}")
            
            self.audio_path = output_path_str
            return output_path_str
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg audio extraction failed: {e.stderr}")
            raise RuntimeError(f"Failed to extract audio: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error during audio extraction: {e}")
            raise RuntimeError(f"Failed to extract audio: {e}")
    
    def _isolate_vocals_demucs(self,
                               audio_path: str,
                               demucs_model: str = "htdemucs",
                               demucs_jobs: int = 0) -> str:
        """
        Isolate vocals from audio using Demucs.
        
        Args:
            audio_path: Path to input audio file
            demucs_model: Demucs model to use
            demucs_jobs: Number of parallel jobs (0 = single-threaded)
            
        Returns:
            str: Path to vocals-only audio file
            
        Raises:
            RuntimeError: If vocal isolation fails
        """
        try:
            # Get Demucs Python path
            demucs_python_path = get_demucs_python_path()
            
            # Create temp directory for Demucs output
            demucs_temp_dir = self.temp_dir / "demucs_output"
            demucs_temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Build Demucs command
            demucs_cmd = [
                demucs_python_path,
                '-m', 'demucs',
                '-n', demucs_model,
                '-o', str(demucs_temp_dir),
                '--two-stems', 'vocals'
            ]
            
            # Add jobs parameter if specified
            if demucs_jobs > 0:
                demucs_cmd.extend(['-j', str(demucs_jobs)])
            
            demucs_cmd.append(audio_path)
            
            # Set up environment variables for Demucs
            demucs_env = os.environ.copy()
            demucs_env['PYTHONIOENCODING'] = 'utf-8'
            demucs_env['TORCHAUDIO_USE_BACKEND_DISPATCHER'] = '1'
            demucs_env['TORIO_USE_FFMPEG'] = '0'
            
            logger.info(f"Running Demucs: {' '.join(demucs_cmd[2:])}")
            
            # Run Demucs with progress monitoring
            process = subprocess.Popen(
                demucs_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=demucs_env
            )
            
            # Monitor progress
            stderr_output = ""
            last_progress = 0.0
            start_time = time.time()
            
            while True:
                if process.stderr is not None:
                    stderr_line = process.stderr.readline()
                    if stderr_line:
                        stderr_output += stderr_line
                        line_stripped = stderr_line.strip()
                        
                        # Show progress updates
                        if '%' in line_stripped or 'processing' in line_stripped.lower():
                            logger.debug(f"Demucs: {line_stripped}")
                
                # Check if process finished
                return_code = process.poll()
                if return_code is not None:
                    # Process finished
                    if return_code != 0:
                        # Read remaining stderr
                        if process.stderr:
                            remaining = process.stderr.read()
                            stderr_output += remaining
                        raise RuntimeError(f"Demucs failed with code {return_code}:\n{stderr_output}")
                    break
                
                # Small delay to avoid busy waiting
                time.sleep(0.1)
            
            # Ensure process is fully terminated and cleaned up
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful exit
            except subprocess.TimeoutExpired:
                logger.warning("Demucs process did not exit gracefully, forcing termination")
                process.kill()
                process.wait()
            
            # Close pipes to release resources
            if process.stdout:
                process.stdout.close()
            if process.stderr:
                process.stderr.close()
            
            # Delete the process object to ensure no lingering references
            del process
            
            elapsed_time = time.time() - start_time
            logger.info(f" Vocal isolation complete in {elapsed_time:.1f}s")
            
            # Force aggressive garbage collection and VRAM cleanup after subprocess completes
            # This ensures any leaked memory from subprocess is cleaned up
            import gc
            
            # Run garbage collection multiple times to catch circular references
            for _ in range(3):
                gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    # Clear CUDA cache multiple times to ensure full cleanup
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()  # Wait for all CUDA operations to complete
                    torch.cuda.empty_cache()  # Clear again after synchronization
                    
                    # Log current VRAM usage if possible
                    if hasattr(torch.cuda, 'memory_allocated'):
                        allocated = torch.cuda.memory_allocated() / (1024**3)  # Convert to GB
                        logger.info(f"VRAM after Demucs cleanup: {allocated:.2f} GB allocated")
                    
                    logger.debug("VRAM cache cleared after Demucs processing")
            except ImportError:
                pass  # torch not available, skip CUDA cleanup
            except Exception as e:
                logger.debug(f"Could not clear CUDA cache: {e}")
            
            # Find vocals.wav output file
            base_name = Path(audio_path).stem
            
            # Search for vocals.wav in output directory
            vocals_path = None
            for root, dirs, files in os.walk(demucs_temp_dir):
                if 'vocals.wav' in files:
                    vocals_path = os.path.join(root, 'vocals.wav')
                    logger.info(f"Found vocals.wav at: {vocals_path}")
                    break
            
            if not vocals_path or not os.path.exists(vocals_path):
                # List directory for debugging
                logger.error(f"Demucs output directory contents:")
                for root, dirs, files in os.walk(demucs_temp_dir):
                    level = root.replace(str(demucs_temp_dir), '').count(os.sep)
                    indent = ' ' * 2 * level
                    logger.error(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        logger.error(f"{subindent}{file}")
                
                raise RuntimeError(f"vocals.wav not found in Demucs output directory")
            
            return vocals_path
            
        except Exception as e:
            logger.error(f"Vocal isolation failed: {e}", exc_info=True)
            raise RuntimeError(f"Vocal isolation failed: {str(e)}")
    
    def extract_audio_segment(self,
                             start_time: float,
                             duration: float,
                             output_path: Optional[str] = None,
                             sample_rate: int = 16000,
                             channels: int = 1,
                             source_audio: Optional[str] = None) -> str:
        """
        Extract a specific audio segment from preprocessed audio or video.
        
        Args:
            start_time: Start time in seconds
            duration: Duration of segment in seconds
            output_path: Optional custom output path for audio file
            sample_rate: Audio sample rate (default: 16000 Hz)
            channels: Number of audio channels (default: 1 for mono)
            source_audio: Optional path to preprocessed audio file (e.g., after Demucs)
                         If provided, segment is extracted from this audio instead of video
            
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
        
        # Determine input source (preprocessed audio or original video)
        input_source = source_audio if source_audio and os.path.exists(source_audio) else str(self.video_path)
        
        try:
            cmd = [
                'ffmpeg',
                '-ss', str(start_time),  # Start time
                '-i', input_source,
                '-t', str(duration),  # Duration
                '-vn',  # Disable video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', str(sample_rate),
                '-ac', str(channels),
                '-y',
                output_path_str
            ]
            
            logger.debug(f"Extracting audio segment: {start_time}s - {start_time + duration}s from {Path(input_source).name}")
            
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
