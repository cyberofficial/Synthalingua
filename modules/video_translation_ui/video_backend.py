"""
Video Translation Backend Module

Flask backend for video translation UI. Provides REST API and WebSocket
endpoints for video upload, processing control, and real-time caption updates.

Integrates with existing api_backend.py infrastructure.
"""

import os
import logging
import json
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List
from flask import Blueprint, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import uuid

# Import video translation modules
from modules.video_translation_ui.video_processor import VideoProcessor
from modules.video_translation_ui.chunk_manager import ChunkManager
from modules.video_translation_ui.buffer_manager import BufferManager
from modules.video_translation_ui.video_transcription import VideoTranscriptionManager

logger = logging.getLogger(__name__)

# Create Blueprint for video routes
video_bp = Blueprint('video', __name__, url_prefix='/api/video')

# Global state management
video_sessions = {}
session_lock = threading.Lock()

# Global configuration (set from parser_args)
_global_model_dir = './models'  # Default, can be overridden
_debug_mode = False  # Default, can be overridden
_keep_temp_global = False  # Default, can be overridden - tracks if any session wants to keep temp files

def set_model_dir(model_dir: str):
    """Set the global model directory from parser_args."""
    global _global_model_dir
    _global_model_dir = model_dir
    logger.info(f"Video UI model directory set to: {model_dir}")

def set_debug_mode(debug: bool):
    """Set debug mode for video backend logging."""
    global _debug_mode
    _debug_mode = debug
    if debug:
        logger.setLevel(logging.DEBUG)
        # Also set debug for child loggers
        for name in ['modules.video_translation_ui.video_processor',
                     'modules.video_translation_ui.chunk_manager',
                     'modules.video_translation_ui.buffer_manager',
                     'modules.video_translation_ui.video_transcription']:
            child_logger = logging.getLogger(name)
            child_logger.setLevel(logging.DEBUG)
        logger.debug("Video backend debug mode enabled")
    else:
        logger.setLevel(logging.INFO)

def set_keep_temp(keep_temp: bool):
    """Set keep_temp flag for video backend."""
    global _keep_temp_global
    _keep_temp_global = keep_temp
    if keep_temp:
        logger.info("Video backend will keep temporary files")
    else:
        logger.info("Video backend will clean temporary files on shutdown")

# Upload configuration
# Use absolute path from current working directory to avoid module-relative issues
import sys
WORKSPACE_ROOT = Path(os.getcwd())
UPLOAD_FOLDER = WORKSPACE_ROOT / 'temp' / 'video_uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {
    # Video formats
    '.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v',
    # Audio formats (will be converted to video with black square)
    '.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus', '.wma'
}
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB


class VideoSession:
    """
    Manages a video translation session.
    
    Handles video processing, chunk management, buffer management,
    and transcription for a single video file.
    """
    
    def __init__(self, session_id: str, video_path: str, config: Dict):
        """
        Initialize video session.
        
        Args:
            session_id: Unique session identifier
            video_path: Path to uploaded video file
            config: Session configuration (model, language, buffer settings, etc.)
        """
        self.session_id = session_id
        self.video_path = video_path
        self.config = config
        
        # Components
        self.video_processor = None
        self.chunk_manager = None
        self.buffer_manager = None
        self.transcription_manager = None
        
        # State
        self.is_initialized = False
        self.is_processing = False
        self.current_playback_time = 0.0
        self.metadata = {}
        self.full_audio_path = None  # Current audio path (may be vocals if Demucs used)
        self.original_audio_path = None  # Original audio before Demucs
        self.vocals_audio_path = None  # Isolated vocals from Demucs
        self.waveform_image_path = None  # Waveform PNG image
        self.mp4_path = None  # MP4 version for browser playback (converted if needed)
        
        # Thread safety
        self.state_lock = threading.Lock()
        
        # Processing thread
        self.processing_thread = None
        self.stop_processing = threading.Event()
        
        logger.info(f"VideoSession created: {session_id}")
    
    def update_config(self, new_config):
        """Update session configuration and initialize components."""
        if self.is_initialized and self.is_processing:
            logger.warning(f"Cannot update config while processing is active for session {self.session_id}")
            return False
        
        # Allow reconfiguration if processing has completed (for reprocessing same video)
        if self.is_initialized and not self.is_processing:
            logger.info(f"Reconfiguring completed session {self.session_id} for reprocessing")
            # Reset all components for fresh reprocessing
            self.is_initialized = False
            
            # Clear all managers to force reinitialization
            if self.chunk_manager:
                self.chunk_manager = None
            if self.transcription_manager:
                self.transcription_manager = None
            if self.buffer_manager:
                self.buffer_manager = None
            if self.video_processor:
                self.video_processor = None
            
            # Clear audio path to trigger re-extraction (important if Demucs settings changed)
            self.full_audio_path = None
            
            logger.info(f"✅ Session reset complete, ready for reprocessing with new settings")
        
        # Config defaults
        global _global_model_dir
        config_defaults = {
            'model_source': 'fasterwhisper',
            'model_size': 'base',
            'device': 'auto',
            'compute_type': 'float16',
            'source_language': None,
            'target_language': 'en',
            'enable_translation': True,
            'enable_silence_detection': True,
            'silence_threshold_db': -35.0,
            'min_silence_duration': 0.5,
            'max_concurrent': 2,
            'model_dir': _global_model_dir,  # Use global model_dir from parser_args
            'enable_vocal_isolation': True,
            'demucs_model': 'htdemucs',
            'demucs_jobs': 0,  # Single-threaded by default
            'enable_temperature': False,  # Use multiple temperature fallbacks by default
            'temperature': None,  # None = use fallback, float = fixed temperature
            'compression_ratio_threshold': 2.4  # Default from Whisper
        }
        
        # Merge defaults with current config
        for key, default_value in config_defaults.items():
            if key not in self.config:
                self.config[key] = default_value
        
        # Update with new configuration
        self.config.update(new_config)
        logger.info(f"Session {self.session_id} config updated: {new_config}")
        
        # Initialize with new configuration
        return self.initialize()
    
    def initialize(self):
        """Initialize all components and extract video metadata."""
        try:
            # Initialize video processor with device from config (auto-detect if not specified)
            device = self.config.get('device', 'auto')
            self.video_processor = VideoProcessor(
                self.video_path,
                temp_dir=str(UPLOAD_FOLDER / self.session_id),
                device=device
            )
            
            # Convert to MP4 for browser compatibility (if not already done during upload)
            if not self.mp4_path:
                logger.info(f"🎬 Converting video to MP4 format for browser playback...")
                self.mp4_path = self.video_processor.convert_to_mp4()
                logger.info(f"✅ MP4 video ready for playback: {self.mp4_path}")
            else:
                logger.info(f"📺 Using existing MP4 video: {self.mp4_path}")
            
            # Extract metadata
            self.metadata = self.video_processor.extract_metadata()
            
            # Extract full audio (with optional Demucs preprocessing)
            # This MUST happen before chunking so Demucs can process the entire audio
            enable_vocals = self.config.get('enable_vocal_isolation', False)
            
            # Always extract original audio first
            original_audio_path = self.video_processor.extract_audio(
                isolate_vocals=False,
                demucs_model=self.config.get('demucs_model', 'htdemucs'),
                demucs_jobs=self.config.get('demucs_jobs', 0)
            )
            self.original_audio_path = original_audio_path
            logger.info(f" Original audio extracted: {original_audio_path}")
            
            # If vocal isolation is enabled, extract vocals separately
            if enable_vocals:
                logger.info(f"Extracting full audio for vocal isolation preprocessing...")
                # Create a separate vocals file
                vocals_output_path = str(Path(original_audio_path).parent / f"{Path(original_audio_path).stem}_vocals.wav")
                logger.info(f"  Target vocals path: {vocals_output_path}")
                
                # Use Demucs to isolate vocals
                vocals_audio_path = self.video_processor.extract_audio(
                    output_path=vocals_output_path,
                    isolate_vocals=True,
                    demucs_model=self.config.get('demucs_model', 'htdemucs'),
                    demucs_jobs=self.config.get('demucs_jobs', 0)
                )
                self.vocals_audio_path = vocals_audio_path
                logger.info(f"✅ Vocals audio isolated and saved to: {vocals_audio_path}")
                logger.info(f"  File exists: {Path(vocals_audio_path).exists()}")
                
                # Use vocals for processing
                self.full_audio_path = vocals_audio_path
                
                # Generate waveform from vocals
                try:
                    self.waveform_image_path = self.video_processor.generate_waveform_image(
                        audio_path=vocals_audio_path,
                        width=1260,
                        height=64
                    )
                    logger.info(f"🎨 Waveform generated from vocals: {self.waveform_image_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate waveform from vocals: {e}")
                    self.waveform_image_path = None
            else:
                # Use original audio for processing
                self.full_audio_path = original_audio_path
                self.vocals_audio_path = None
                
                # Generate waveform from original audio
                try:
                    self.waveform_image_path = self.video_processor.generate_waveform_image(
                        audio_path=original_audio_path,
                        width=1260,
                        height=64
                    )
                    logger.info(f"🎨 Waveform generated from original audio: {self.waveform_image_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate waveform from original: {e}")
                    self.waveform_image_path = None
            
            logger.info(f" Full audio ready for processing: {self.full_audio_path}")
            
            # Initialize chunk manager
            # Process ENTIRE video as one chunk (no buffering/splitting)
            chunk_duration = self.metadata['duration']  # Use full video duration
            self.chunk_manager = ChunkManager(
                video_duration=self.metadata['duration'],
                chunk_duration=chunk_duration
            )
            
            # Initialize transcription manager
            # Temperature: if enable_temperature is False, pass None to use fallback temps
            temp_value = self.config.get('temperature') if self.config.get('enable_temperature', False) else None
            
            # Compression ratio threshold
            compression_ratio = self.config.get('compression_ratio_threshold', 2.4)
            
            self.transcription_manager = VideoTranscriptionManager(
                model_source=self.config.get('model_source', 'fasterwhisper'),
                model_size=self.config.get('model_size', 'base'),
                device=self.config.get('device', 'auto'),
                compute_type=self.config.get('compute_type', 'float16'),
                source_language=self.config.get('source_language'),
                target_language=self.config.get('target_language', 'en'),
                enable_translation=self.config.get('enable_translation', True),
                enable_silence_detection=self.config.get('enable_silence_detection', True),
                silence_threshold_db=self.config.get('silence_threshold_db', -35.0),
                min_silence_duration=self.config.get('min_silence_duration', 0.5),
                model_dir=self.config.get('model_dir', './models'),
                temperature=temp_value,
                compression_ratio_threshold=compression_ratio,
                debug_mode=_debug_mode
            )
            
            # Initialize buffer manager
            self.buffer_manager = BufferManager(
                chunk_manager=self.chunk_manager,
                buffer_seconds=self.metadata['duration'],  # Buffer entire video
                max_concurrent=self.config.get('max_concurrent', 2),
                on_chunk_processed=self._on_chunk_processed,
                debug=_debug_mode
            )
            
            self.is_initialized = True
            logger.info(f"Session {self.session_id} initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize session {self.session_id}: {e}", exc_info=True)
            return False
    
    def start_processing(self):
        """Start background processing of video chunks."""
        if not self.is_initialized:
            logger.error("Cannot start processing: session not initialized")
            return False
        
        if self.is_processing:
            logger.warning("Processing already started")
            return False
        
        # Attach socketio reference if available
        if '_socketio_instance' in globals():
            self.socketio = globals()['_socketio_instance']
        
        self.is_processing = True
        self.stop_processing.clear()
        
        # Start buffer manager
        if self.buffer_manager:
            self.buffer_manager.start_processing()
        
        # Start chunk processing thread
        self.processing_thread = threading.Thread(
            target=self._process_chunks,
            daemon=True
        )
        self.processing_thread.start()
        
        logger.info(f"Processing started for session {self.session_id}")
        return True
    
    def pause_processing(self):
        """Pause chunk processing."""
        if self.buffer_manager:
            self.buffer_manager.pause_processing()
        logger.info(f"Processing paused for session {self.session_id}")
    
    def resume_processing(self):
        """Resume chunk processing."""
        if self.buffer_manager:
            self.buffer_manager.resume_processing()
        logger.info(f"Processing resumed for session {self.session_id}")
    
    def stop(self):
        """Stop all processing and cleanup."""
        logger.info(f"Stopping session {self.session_id}")
        
        self.is_processing = False
        self.stop_processing.set()
        
        if self.buffer_manager:
            self.buffer_manager.stop_processing()
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        logger.info(f"Session {self.session_id} stopped")
    
    def _process_chunks(self):
        """Background thread for processing chunks."""
        logger.debug(f"Chunk processing thread started for session {self.session_id}")
        if _debug_mode:
            logger.debug(f"[DEBUG] VideoBackend: Starting chunk processing thread for session {self.session_id}")
        
        # Get total chunk count for progress tracking
        total_chunks = len(self.chunk_manager.chunks) if self.chunk_manager else 0
        processed_count = 0
        start_time = time.time()
        
        logger.info(f" Starting video processing: {total_chunks} chunks to process")
        if _debug_mode:
            logger.debug(f"[DEBUG] VideoBackend: Total chunks to process: {total_chunks}")
        
        while not self.stop_processing.is_set():
            try:
                # Check if components are initialized
                if not self.buffer_manager or not self.video_processor or not self.transcription_manager or not self.chunk_manager:
                    logger.error("Components not initialized")
                    break
                
                # Get next chunk from buffer manager's queue
                if not self.buffer_manager.processing_queue.empty():
                    chunk = self.buffer_manager.processing_queue.get(timeout=1.0)
                    
                    processed_count += 1
                    logger.info(f" Processing chunk {processed_count}/{total_chunks} "
                              f"[{chunk.start_time:.1f}s - {chunk.end_time:.1f}s]")
                    
                    if _debug_mode:
                        logger.debug(f"[DEBUG] VideoBackend: ===== Processing chunk {processed_count}/{total_chunks} =====")
                        logger.debug(f"[DEBUG] VideoBackend: Chunk ID: {chunk.chunk_id}, Range: {chunk.start_time:.2f}s - {chunk.end_time:.2f}s")
                        logger.debug(f"[DEBUG] VideoBackend: Audio source: {getattr(self, 'full_audio_path', 'None')}")
                    
                    # Extract audio segment from preprocessed full audio (if available)
                    # This ensures Demucs-processed audio is used for all chunks
                    audio_path = self.video_processor.extract_audio_segment(
                        start_time=chunk.start_time,
                        duration=chunk.duration,
                        source_audio=getattr(self, 'full_audio_path', None)
                    )
                    chunk.audio_path = audio_path
                    
                    # Process chunk with incremental timestamp updates
                    def on_segment_complete(timestamp_dict, segment_num, total_segments):
                        """Callback to add timestamps incrementally so captions show in real-time"""
                        chunk.timestamps.append(timestamp_dict)
                        
                        # Update processed_until to include this segment + any silence before it
                        # This represents how far we've analyzed (speech + silence)
                        segment_end_relative = timestamp_dict['end'] - chunk.start_time
                        chunk.processed_until = segment_end_relative
                        
                        # Calculate cumulative segment count across all chunks
                        cumulative_segments = sum(len(c.timestamps) for c in self.chunk_manager.chunks) if self.chunk_manager else 0
                        
                        # Calculate buffer status after each segment
                        buffer_status = self.chunk_manager.get_buffer_status(
                            current_time=self.current_playback_time,
                            buffer_distance=self.metadata['duration']
                        ) if self.chunk_manager else {'seconds_buffered': 0}
                        seconds_buffered = buffer_status['seconds_buffered']
                        
                        # Log segment completion with buffer status
                        print(f"✓ Segment {segment_num}/{total_segments} in chunk {chunk.chunk_id}: "
                              f"{timestamp_dict['start']:.2f}s - {timestamp_dict['end']:.2f}s | "
                              f"Buffer: {seconds_buffered:.1f}s ahead")
                        import sys
                        sys.stdout.flush()  # Force console output to appear immediately
                        
                        # Emit WebSocket update with total segments count (we know this from silence detector)
                        if hasattr(self, '_emit_buffer_update'):
                            self._emit_buffer_update(buffer_status, cumulative_segments, total_segments, chunk.chunk_id)
                    
                    result = self.transcription_manager.process_chunk(
                        audio_path=audio_path,
                        chunk_id=chunk.chunk_id,
                        start_time=chunk.start_time,
                        end_time=chunk.end_time,
                        on_segment_complete=on_segment_complete
                    )
                    
                    if _debug_mode:
                        logger.debug(f"[DEBUG] VideoBackend: Chunk {chunk.chunk_id} processing returned: success={result['success']}")
                    
                    # Update chunk status
                    if result['success']:
                        if _debug_mode:
                            logger.debug(f"[DEBUG] VideoBackend: Marking chunk {chunk.chunk_id} as completed")
                            logger.debug(f"[DEBUG] VideoBackend: Transcription length: {len(result.get('transcription', ''))}")
                            logger.debug(f"[DEBUG] VideoBackend: Timestamps count: {len(result.get('timestamps', []))}")
                        self.chunk_manager.mark_chunk_completed(
                            chunk_id=chunk.chunk_id,
                            transcription=result['transcription'],
                            translation=result.get('translation', ''),
                            timestamps=result.get('timestamps', []),
                            language=result.get('language', 'unknown')
                        )
                        
                        # Calculate buffer status (how much is ready ahead of playback position)
                        if self.chunk_manager:
                            buffer_status = self.chunk_manager.get_buffer_status(
                                current_time=self.current_playback_time,
                                buffer_distance=self.metadata['duration']
                            )
                            seconds_buffered = buffer_status['seconds_buffered']
                        else:
                            seconds_buffered = 0
                        
                        # Calculate overall progress
                        elapsed = time.time() - start_time
                        avg_time = elapsed / processed_count
                        remaining = (total_chunks - processed_count) * avg_time
                        progress_pct = (processed_count / total_chunks * 100) if total_chunks > 0 else 0
                        
                        logger.info(f" Chunk {processed_count}/{total_chunks} completed "
                                  f"({progress_pct:.1f}% done) | "
                                  f"Buffer: {seconds_buffered:.1f}s ahead | "
                                  f"ETA: {remaining/60:.1f} minutes")
                    else:
                        self.chunk_manager.mark_chunk_failed(
                            chunk_id=chunk.chunk_id,
                            error_message=result.get('error', 'Unknown error')
                        )
                        logger.warning(f"⚠️  Chunk {processed_count} failed: {result.get('error', 'Unknown error')}")
                    
                    # Notify buffer manager
                    self.buffer_manager.mark_task_complete(chunk.chunk_id)
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error processing chunk: {e}", exc_info=True)
                time.sleep(1.0)
        
        # Final summary
        total_time = time.time() - start_time
        logger.info(f"🎉 Video processing completed! Processed {processed_count}/{total_chunks} chunks in {total_time/60:.1f} minutes")
        
        # Unload the transcription model to free VRAM/RAM
        # NOTE: With subprocess isolation, models are automatically cleaned up after each transcription
        # This call is a no-op but kept for code clarity
        if self.transcription_manager:
            try:
                logger.info("Ensuring transcription model cleanup...")
                self.transcription_manager.unload_model()
                logger.info("Transcription model cleanup complete (subprocess handles automatic VRAM release)")
            except Exception as e:
                logger.error(f"Error during transcription model cleanup: {e}")
        
        # Reset processing flag so user can process another video
        self.is_processing = False
        
        # Emit final buffer update to show 100% completion in UI
        if self.socketio and self.chunk_manager:
            try:
                # Get final buffer status
                final_buffer_status = self.chunk_manager.get_buffer_status(
                    current_time=self.current_playback_time,
                    buffer_distance=self.metadata['duration']
                )
                
                # Count total segments across all chunks
                total_segments = sum(len(chunk.timestamps) for chunk in self.chunk_manager.chunks)
                
                # Emit final buffer update showing all segments complete
                self.socketio.emit('buffer_update', {
                    'buffer_status': final_buffer_status,
                    'segment_num': total_segments,
                    'total_segments': total_segments,
                    'chunk_id': 'final'
                }, to=self.session_id, namespace='/')
                logger.debug(f"Emitted final buffer update: {total_segments}/{total_segments} segments")
            except Exception as e:
                logger.error(f"Could not emit final buffer update: {e}")
        
        # Emit completion event to frontend
        if self.socketio and self.chunk_manager:
            try:
                # Count total segments for completion event
                total_segments = sum(len(chunk.timestamps) for chunk in self.chunk_manager.chunks)
                
                self.socketio.emit('processing_complete', {
                    'session_id': self.session_id,
                    'total_chunks': total_chunks,
                    'processed_chunks': processed_count,
                    'total_time': total_time,
                    'total_segments': total_segments
                }, to=self.session_id, namespace='/')
                logger.debug(f"Emitted processing_complete event for session {self.session_id}")
            except Exception as e:
                logger.error(f"Could not emit processing_complete event: {e}")
        
        logger.debug(f"Chunk processing thread ended for session {self.session_id}")
    
    def _on_chunk_processed(self, chunk):
        """Callback when a chunk is processed (for WebSocket updates)."""
        # This will be used to emit WebSocket events
        pass
    
    def _emit_buffer_update(self, buffer_status, segment_num, total_segments, chunk_id):
        """Emit buffer status update via WebSocket."""
        if self.socketio:
            try:
                self.socketio.emit('buffer_update', {
                    'buffer_status': buffer_status,
                    'segment_num': segment_num,
                    'total_segments': total_segments,
                    'chunk_id': chunk_id
                }, to=self.session_id, namespace='/')
            except Exception as e:
                logger.debug(f"Could not emit buffer update: {e}")
    
    def update_playback_position(self, timestamp: float):
        """Update current playback position."""
        self.current_playback_time = timestamp
        if self.buffer_manager:
            self.buffer_manager.update_playback_position(timestamp)
    
    def seek_to(self, timestamp: float):
        """Handle seek operation."""
        self.current_playback_time = timestamp
        if self.buffer_manager:
            self.buffer_manager.seek_to(timestamp)
    
    def get_status(self) -> Dict:
        """Get current session status."""
        status = {
            'session_id': self.session_id,
            'is_initialized': self.is_initialized,
            'is_processing': self.is_processing,
            'current_time': self.current_playback_time,
            'metadata': self.metadata,
        }
        
        if self.chunk_manager:
            status['progress'] = self.chunk_manager.get_progress()
            
            # Add segment count for status bar
            total_segments = sum(len(chunk.timestamps) for chunk in self.chunk_manager.chunks)
            status['segment_count'] = total_segments
        
        if self.buffer_manager:
            status['buffer'] = self.buffer_manager.get_status()
        
        if self.transcription_manager:
            status['transcription_stats'] = self.transcription_manager.get_statistics()
        
        return status
    
    def get_captions_at_time(self, timestamp: float) -> Dict:
        """
        Get captions for a specific timestamp.
        
        With silence detection, this returns the specific caption segment(s)
        that should be displayed at the given timestamp, not the entire chunk.
        
        Args:
            timestamp: Current playback timestamp in seconds
            
        Returns:
            dict: Caption data with:
                - transcription: Text to display in source language
                - translation: Text to display in target language
                - language: Detected language code
        """
        if not self.chunk_manager:
            return {'transcription': '', 'translation': '', 'language': 'unknown', 'duration': 3.0}
        
        chunk = self.chunk_manager.get_chunk_at_time(timestamp)
        
        if not chunk:
            logger.debug(f"No chunk found for timestamp {timestamp:.2f}s")
            return {'transcription': '', 'translation': '', 'language': 'unknown', 'duration': 3.0}
        
        logger.debug(f"Chunk found for {timestamp:.2f}s: id={chunk.chunk_id}, "
                    f"status={chunk.status.name}, "
                    f"has_transcription={bool(chunk.transcription)}, "
                    f"has_translation={bool(chunk.translation)}, "
                    f"timestamps_count={len(chunk.timestamps)}")
        
        # If chunk has timestamp segments (from silence detection), find the active one
        if chunk.timestamps:
            for segment in chunk.timestamps:
                segment_start = segment.get('start', 0)
                segment_end = segment.get('end', 0)
                
                # Check if timestamp falls within this segment
                if segment_start <= timestamp < segment_end:
                    translation = segment.get('translation', '')
                    transcription = segment.get('text', '')
                    duration = segment_end - segment_start  # Calculate caption duration
                    
                    logger.debug(f"Found active caption segment at {timestamp:.2f}s: "
                               f"{segment_start:.2f}s - {segment_end:.2f}s (duration={duration:.2f}s)")
                    logger.debug(f"  Transcription: '{transcription[:50]}...' (len={len(transcription)})")
                    logger.debug(f"  Translation: '{translation[:50]}...' (len={len(translation)})")
                    
                    return {
                        'transcription': transcription,
                        'translation': translation,
                        'language': self.transcription_manager.source_language if self.transcription_manager else 'unknown',
                        'duration': duration  # Add duration for word highlighting timing
                    }
            
            # Timestamp is between caption segments (silence) - return empty
            logger.debug(f"Timestamp {timestamp:.2f}s is between caption segments (silence)")
            return {'transcription': '', 'translation': '', 'language': 'unknown', 'duration': 3.0}  # Default for empty
        
        # Fallback: chunk has no timestamp segments, return full chunk transcription
        if chunk.transcription:
            chunk_duration = chunk.end_time - chunk.start_time
            return {
                'transcription': chunk.transcription,
                'translation': chunk.translation or '',
                'language': self.transcription_manager.source_language if self.transcription_manager else 'unknown',
                'duration': chunk_duration  # Use chunk duration for fallback
            }
        
        return {'transcription': '', 'translation': '', 'language': 'unknown', 'duration': 3.0}  # Default for empty
    
    def redo_section(self, start_time: float, end_time: float, config: Dict) -> Dict:
        """
        Re-transcribe and re-translate a specific section of the video.
        
        This method:
        1. Extracts audio for the specified time range
        2. Re-runs Whisper transcription with provided config
        3. Updates existing segments in the time range
        4. Saves updated captions to JSON/SRT files
        5. Emits WebSocket updates for real-time UI refresh
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            config: Updated configuration dict with keys:
                - temperature: Optional[float]
                - compression_ratio_threshold: float
                - silence_threshold_db: float
                - min_silence_duration: float
                
        Returns:
            dict: Result with 'success', 'segments_updated', and 'error' keys
        """
        logger.info(f"🔄 Redoing section {start_time:.2f}s - {end_time:.2f}s for session {self.session_id}")
        
        with self.state_lock:
            # Validate state
            if not self.is_initialized:
                return {'success': False, 'error': 'Session not initialized'}
            
            # Allow redo if processing is complete (all chunks done) even if thread is still running
            if self.is_processing and self.chunk_manager:
                progress = self.chunk_manager.get_progress()
                if progress['completed'] < progress['total_chunks']:
                    return {'success': False, 'error': 'Cannot redo section while processing is active'}
                # else: All chunks completed, allow redo even if background thread is cleaning up
            elif self.is_processing:
                return {'success': False, 'error': 'Cannot redo section while processing is active'}
            
            if not self.chunk_manager or not self.transcription_manager or not self.video_processor:
                return {'success': False, 'error': 'Required managers not initialized'}
        
        try:
            # Extract audio segment for this time range
            duration = end_time - start_time
            
            # Use vocals audio if available, otherwise full audio
            source_audio = self.vocals_audio_path if self.vocals_audio_path and os.path.exists(self.vocals_audio_path) else self.full_audio_path
            
            logger.info(f"  Extracting audio segment from {source_audio}...")
            segment_audio_path = self.video_processor.extract_audio_segment(
                start_time=start_time,
                duration=duration,
                source_audio=source_audio
            )
            
            # Create temporary transcription manager with updated config
            logger.info(f"  Creating temporary transcription manager with updated config...")
            temp_manager = VideoTranscriptionManager(
                model_source=config.get('model_source', self.config.get('model_source', 'fasterwhisper')),
                model_size=config.get('model_size', self.config.get('model_size', 'base')),
                device=config.get('device', self.config.get('device', 'auto')),
                compute_type=config.get('compute_type', self.config.get('compute_type', 'float16')),
                source_language=config.get('source_language', self.config.get('source_language', None)),
                target_language=config.get('target_language', self.config.get('target_language', 'en')),
                enable_translation=config.get('enable_translation', self.config.get('enable_translation', True)),
                enable_silence_detection=config.get('enable_silence_detection', self.config.get('enable_silence_detection', True)),
                silence_threshold_db=config.get('silence_threshold_db', self.config.get('silence_threshold_db', -35.0)),
                min_silence_duration=config.get('min_silence_duration', self.config.get('min_silence_duration', 0.5)),
                model_dir=self.config.get('model_dir', './models'),
                temperature=config.get('temperature'),
                compression_ratio_threshold=config.get('compression_ratio_threshold', self.config.get('compression_ratio_threshold', 2.4)),
                debug_mode=self.config.get('debug_mode', False)
            )
            
            # Process the segment
            logger.info(f"  Transcribing segment...")
            result = temp_manager.process_chunk(
                audio_path=segment_audio_path,
                chunk_id=-1,  # Temporary ID for redo
                start_time=start_time,
                end_time=end_time,
                on_segment_complete=None
            )
            
            if not result['success']:
                return {'success': False, 'error': result.get('error', 'Transcription failed')}
            
            # Remove old segments in this time range
            logger.info(f"  Removing old segments in range {start_time:.2f}s - {end_time:.2f}s...")
            removed_count = self._remove_segments_in_range(start_time, end_time)
            logger.info(f"  Removed {removed_count} old segments")
            
            # Add new segments
            logger.info(f"  Adding {len(result.get('timestamps', []))} new segments...")
            added_count = self._add_segments_from_result(result)
            logger.info(f"  Added {added_count} new segments")
            
            # Cleanup temporary audio file
            try:
                if os.path.exists(segment_audio_path):
                    os.remove(segment_audio_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary audio file: {e}")
            
            # Emit WebSocket update to notify frontend
            try:
                from flask_socketio import emit
                emit('section_updated', {
                    'start_time': start_time,
                    'end_time': end_time,
                    'segments_updated': added_count
                }, namespace='/video', room=self.session_id)
            except Exception as e:
                logger.warning(f"Could not emit WebSocket update: {e}")
            
            logger.info(f"✅ Section redo completed: {removed_count} removed, {added_count} added")
            
            return {
                'success': True,
                'segments_removed': removed_count,
                'segments_added': added_count,
                'language': result.get('language', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error redoing section: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _remove_segments_in_range(self, start_time: float, end_time: float) -> int:
        """
        Remove all segments that overlap with the given time range.
        
        Args:
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            int: Number of segments removed
        """
        removed_count = 0
        
        if not self.chunk_manager:
            return 0
        
        # Iterate through all chunks and remove overlapping segments
        for chunk in self.chunk_manager.chunks:
            if not chunk.timestamps:
                continue
            
            # Filter out segments that overlap with the time range
            original_count = len(chunk.timestamps)
            chunk.timestamps = [
                seg for seg in chunk.timestamps
                if not (seg['start'] < end_time and seg['end'] > start_time)
            ]
            removed_count += original_count - len(chunk.timestamps)
        
        return removed_count
    
    def _add_segments_from_result(self, result: Dict) -> int:
        """
        Add new segments from transcription result to appropriate chunks.
        
        Args:
            result: Transcription result dict with 'timestamps' list
            
        Returns:
            int: Number of segments added
        """
        added_count = 0
        
        if not self.chunk_manager or not result.get('timestamps'):
            return 0
        
        # Add each segment to the appropriate chunk
        for segment in result['timestamps']:
            start = segment['start']
            end = segment['end']
            
            # Find the chunk that contains this segment
            for chunk in self.chunk_manager.chunks:
                # Check if segment falls within this chunk's time range
                if chunk.start_time <= start < chunk.end_time:
                    if not chunk.timestamps:
                        chunk.timestamps = []
                    
                    chunk.timestamps.append(segment)
                    added_count += 1
                    break
        
        # Sort timestamps within each chunk
        for chunk in self.chunk_manager.chunks:
            if chunk.timestamps:
                chunk.timestamps.sort(key=lambda x: x['start'])
        
        return added_count
    
    def export_captions(self, format: str = 'srt', export_type: str = 'english') -> Optional[str]:
        """
        Export captions to SRT or VTT format.
        
        With silence detection, exports individual caption segments with accurate timing
        instead of chunk-level captions.
        """
        if not self.chunk_manager:
            return None
        
        # Collect all caption segments from all chunks
        caption_segments = []
        
        for chunk in self.chunk_manager.chunks:
            # Check for either transcription or translation (translation-only workflow)
            if not chunk.transcription and not chunk.translation:
                continue
            
            # If chunk has timestamp segments (from silence detection), use them
            if chunk.timestamps:
                for segment in chunk.timestamps:
                    caption_segments.append({
                        'start': segment.get('start', chunk.start_time),
                        'end': segment.get('end', chunk.end_time),
                        'text': segment.get('text', ''),
                        'translation': segment.get('translation', '')
                    })
            else:
                # Fallback: use chunk as single caption
                caption_segments.append({
                    'start': chunk.start_time,
                    'end': chunk.end_time,
                    'text': chunk.transcription or '',
                    'translation': chunk.translation or ''
                })
        
        # Sort by start time
        caption_segments.sort(key=lambda x: x['start'])
        
        if format.lower() == 'srt':
            return self._export_srt(caption_segments, export_type)
        elif format.lower() == 'vtt':
            return self._export_vtt(caption_segments, export_type)
        else:
            return None
    
    def _export_srt(self, segments: List[Dict], export_type: str = 'english') -> str:
        """Export caption segments as SRT format for a specific type."""
        srt_content = []
    
        for i, segment in enumerate(segments, 1):
            start_time = self._format_srt_time(segment['start'])
            end_time = self._format_srt_time(segment['end'])
    
            # Select text based on export type
            if export_type == 'original':
                text = segment.get('text', '')
            else:  # Default to english/translation
                text = segment.get('translation', '')
    
            if not text.strip():
                continue
    
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between entries
    
        return "\n".join(srt_content)
    
    def _export_vtt(self, segments: List[Dict], export_type: str = 'english') -> str:
        """Export caption segments as WebVTT format for a specific type."""
        vtt_content = ["WEBVTT\n"]
    
        for segment in segments:
            start_time = self._format_vtt_time(segment['start'])
            end_time = self._format_vtt_time(segment['end'])
    
            # Select text based on export type
            if export_type == 'original':
                text = segment.get('text', '')
            else:  # Default to english/translation
                text = segment.get('translation', '')
    
            if not text.strip():
                continue
    
            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(text)
            vtt_content.append("")
    
        return "\n".join(vtt_content)
    
    @staticmethod
    def _format_srt_time(seconds: float) -> str:
        """Format time for SRT (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format time for WebVTT (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def cleanup(self):
        """Cleanup temporary files and resources."""
        try:
            # Unload transcription model to free VRAM/RAM
            # NOTE: With subprocess isolation, models are automatically cleaned up after each transcription
            # This call is a no-op but kept for code clarity
            if self.transcription_manager:
                try:
                    logger.info(f"Ensuring transcription model cleanup for session {self.session_id}...")
                    self.transcription_manager.unload_model()
                    logger.info(f"Transcription model cleanup complete for session {self.session_id} (subprocess handles automatic VRAM release)")
                except Exception as e:
                    logger.error(f"Error during transcription model cleanup: {e}")
            
            if self.video_processor:
                self.video_processor.cleanup()
            
            # Clean up temp directory unless keep_temp flag is set
            keep_temp = self.config.get('keep_temp', False)
            if keep_temp:
                logger.info(f"Keeping temp files for session {self.session_id} as requested")
            else:
                temp_dir = UPLOAD_FOLDER / self.session_id
                if temp_dir.exists():
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {self.session_id}: {e}")
    
    def __del__(self):
        """
        Destructor to ensure cleanup when session is destroyed.
        
        NOTE: With subprocess isolation, models are automatically cleaned up after each transcription.
        This call is a no-op but kept for safety.
        """
        try:
            if hasattr(self, 'transcription_manager') and self.transcription_manager:
                self.transcription_manager.unload_model()
        except Exception:
            pass  # Ignore errors during destruction


# API Routes

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file and create a new session.
    Configuration will be set when user clicks Start Processing.
    
    Returns:
        JSON with session_id and video metadata
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if not file.filename or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Unsupported file format: {file_ext}'}), 400
    
    try:
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Save uploaded file
        filename = secure_filename(file.filename) if file.filename else 'video.mp4'
        session_dir = UPLOAD_FOLDER / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        video_path = session_dir / filename
        file.save(str(video_path))
        
        logger.info(f"📹 Video uploaded: {filename} -> Session: {session_id}")
        
        # Create session with empty config (will be set when processing starts)
        config = {}
        video_session = VideoSession(session_id, str(video_path), config)
        
        # Store session (not initialized yet)
        with session_lock:
            video_sessions[session_id] = video_session
        
        # Convert to MP4 immediately for browser playback (if not already MP4)
        # Note: At upload time, config is not yet set, so we use auto-detection
        # This will use CUDA if available for faster initial conversion
        logger.info(f"🎬 Preparing video for browser playback...")
        video_processor = VideoProcessor(str(video_path), temp_dir=str(session_dir), device='auto')
        
        # Convert to MP4 for browser compatibility (auto-detect CUDA for speed)
        mp4_path = video_processor.convert_to_mp4()
        video_session.mp4_path = mp4_path
        logger.info(f"✅ Video ready for playback: {mp4_path}")
        
        # Extract metadata from the original video
        metadata = video_processor.extract_metadata()
        
        logger.info(f"📋 Session created: {session_id} (awaiting configuration)")
        
        return jsonify({
            'session_id': session_id,
            'filename': filename,
            'metadata': metadata,
            'status': 'uploaded'
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading video: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/start', methods=['POST'])
def start_session(session_id):
    """Start processing for a video session with configuration."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Get configuration from request body
    config = request.get_json() or {}
    
    # Log the configuration received
    print(f"\n{'='*60}")
    print(f" START PROCESSING - Session: {session_id}")
    print(f" Configuration received:")
    print(f"   Model Source: {config.get('model_source', 'N/A')}")
    print(f"   Model Size: {config.get('model_size', 'N/A')}")
    print(f"   Device: {config.get('device', 'N/A')}")
    print(f"   Source Language: {config.get('source_language', 'N/A')}")
    print(f"   Target Language: {config.get('target_language', 'N/A')}")
    print(f"   Translation Enabled: {config.get('enable_translation', 'N/A')}")
    print(f"   Processing Mode: Continuous (all chunks)")
    print(f"{'='*60}\n")
    
    # Update session configuration
    video_session.update_config(config)
    
    if video_session.start_processing():
        return jsonify({'status': 'processing started'}), 200
    else:
        return jsonify({'error': 'Failed to start processing'}), 500


@video_bp.route('/session/<session_id>/pause', methods=['POST'])
def pause_session(session_id):
    """Pause processing for a video session."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    video_session.pause_processing()
    return jsonify({'status': 'paused'}), 200


@video_bp.route('/session/<session_id>/resume', methods=['POST'])
def resume_session(session_id):
    """Resume processing for a video session."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    video_session.resume_processing()
    return jsonify({'status': 'resumed'}), 200


@video_bp.route('/session/<session_id>/stop', methods=['POST'])
def stop_session(session_id):
    """Stop processing and cleanup session."""
    with session_lock:
        video_session = video_sessions.pop(session_id, None)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    video_session.stop()
    video_session.cleanup()
    
    return jsonify({'status': 'stopped'}), 200


@video_bp.route('/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get current status of a video session."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    status = video_session.get_status()
    return jsonify(status), 200


@video_bp.route('/session/<session_id>/captions', methods=['GET'])
def get_captions(session_id):
    """Get captions at a specific timestamp."""
    timestamp = float(request.args.get('timestamp', 0))
    
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    captions = video_session.get_captions_at_time(timestamp)
    return jsonify(captions), 200


@video_bp.route('/session/<session_id>/seek', methods=['POST'])
def seek_video(session_id):
    """Handle seek operation."""
    data = request.get_json()
    timestamp = float(data.get('timestamp', 0))
    
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    video_session.seek_to(timestamp)
    return jsonify({'status': 'seek complete', 'timestamp': timestamp}), 200


@video_bp.route('/session/<session_id>/export', methods=['GET'])
def export_captions(session_id):
    """Export captions as SRT or VTT file for either English or Original text."""
    format = request.args.get('format', 'srt').lower()
    export_type = request.args.get('type', 'english').lower()

    with session_lock:
        video_session = video_sessions.get(session_id)

    if not video_session:
        return jsonify({'error': 'Session not found'}), 404

    captions = video_session.export_captions(format, export_type)

    if not captions:
        return jsonify({'error': f'No captions available for type "{export_type}" or invalid format'}), 400

    # Generate a safe filename from the original video name
    safe_video_name = secure_filename(Path(video_session.video_path).stem)

    # Create temporary file
    export_filename = f"{safe_video_name}_{export_type}.{format}"
    export_path = UPLOAD_FOLDER / session_id / export_filename
    export_path.write_text(captions, encoding='utf-8')

    return send_file(
        str(export_path),
        as_attachment=True,
        download_name=export_filename,
        mimetype='text/plain'
    )

@video_bp.route('/session/<session_id>/transcribe_segment', methods=['POST'])
def transcribe_segment(session_id):
    """Re-transcribe a specific time section with the task set to 'transcribe'."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
        
    try:
        data = request.get_json()
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if start_time is None or end_time is None:
            return jsonify({'error': 'start_time and end_time are required'}), 400

        # Use a temporary transcription manager for this one-off task
        transcription_manager = VideoTranscriptionManager(
            model_source=data.get('model_source', video_session.config.get('model_source')),
            model_size=data.get('model_size', video_session.config.get('model_size')),
            device=data.get('device', video_session.config.get('device')),
            compute_type=video_session.config.get('compute_type', 'float16'),
            source_language=data.get('source_language'),
            target_language='en',
            enable_translation=False,
            enable_silence_detection=False,
            silence_threshold_db=-35.0,
            min_silence_duration=0.5,
            model_dir=video_session.config.get('model_dir', './models'),
            temperature=data.get('temperature'),
            compression_ratio_threshold=data.get('compression_ratio_threshold')
        )

        # Extract the specific audio segment
        source_audio = video_session.vocals_audio_path if video_session.vocals_audio_path and os.path.exists(video_session.vocals_audio_path) else video_session.full_audio_path
        segment_audio_path = video_session.video_processor.extract_audio_segment(
            start_time=start_time,
            duration=(end_time - start_time),
            source_audio=source_audio
        )

        # Perform transcription (not translation)
        result = transcription_manager.transcribe_chunk(
            audio_path=segment_audio_path,
            chunk_id=-1,  # Temporary ID
            language=data.get('source_language')
        )
        
        # Clean up the temporary segment file
        if os.path.exists(segment_audio_path):
            os.remove(segment_audio_path)

        if result['success']:
            # Find the corresponding segment and update it
            with video_session.state_lock:
                found = False
                for chunk in video_session.chunk_manager.chunks:
                    for seg in chunk.timestamps:
                        if abs(seg['start'] - start_time) < 0.1 and abs(seg['end'] - end_time) < 0.1:
                            seg['text'] = result['transcription']
                            found = True
                            break
                    if found:
                        break
            
            return jsonify({
                'success': True,
                'transcribed_text': result['transcription']
            })
        else:
            return jsonify({'error': result.get('error', 'Transcription failed')}), 500

    except Exception as e:
        logger.error(f"Error transcribing segment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/redo_section', methods=['POST'])
def redo_section(session_id):
    """
    Re-transcribe a specific time section of the video with updated settings.
    This allows users to fine-tune problematic sections after full processing.
    """
    try:
        data = request.get_json()
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time is None or end_time is None:
            return jsonify({'error': 'start_time and end_time are required'}), 400
        
        if start_time >= end_time:
            return jsonify({'error': 'start_time must be less than end_time'}), 400
        
        if end_time - start_time < 0.5:
            return jsonify({'error': 'Section must be at least 0.5 seconds'}), 400
        
        with session_lock:
            video_session = video_sessions.get(session_id)
        
        if not video_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Extract settings from request (allow user to change settings for this section)
        config = {
            'model_source': data.get('model_source', video_session.config.get('model_source', 'fasterwhisper')),
            'model_size': data.get('model_size', video_session.config.get('model_size', 'base')),
            'device': data.get('device', video_session.config.get('device', 'auto')),
            'source_language': data.get('source_language', video_session.config.get('source_language', 'auto')),
            'target_language': data.get('target_language', video_session.config.get('target_language', 'en')),
            'enable_silence_detection': data.get('enable_silence_detection', 
                                                video_session.config.get('enable_silence_detection', True)),
            'silence_threshold_db': data.get('silence_threshold_db', 
                                            video_session.config.get('silence_threshold_db', -35)),
            'min_silence_duration': data.get('min_silence_duration', 
                                            video_session.config.get('min_silence_duration', 0.5)),
            'min_speech_duration': data.get('min_speech_duration', 
                                           video_session.config.get('min_speech_duration', 0.1)),
            'enable_temperature': data.get('enable_temperature', 
                                         video_session.config.get('enable_temperature', False)),
            'temperature': data.get('temperature', video_session.config.get('temperature')),
            'compression_ratio_threshold': data.get('compression_ratio_threshold', 
                                                   video_session.config.get('compression_ratio_threshold', 2.4))
        }
        
        logger.info(f"Redoing section {start_time:.2f}s - {end_time:.2f}s for session {session_id}")
        logger.debug(f"Section redo config: {config}")
        
        # Call the session's redo_section method
        result = video_session.redo_section(start_time, end_time, config)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f'Section {start_time:.2f}s - {end_time:.2f}s redone successfully',
                'segments_removed': result.get('segments_removed', 0),
                'segments_added': result.get('segments_added', 0),
                'language': result.get('language', 'unknown'),
                'start_time': start_time,
                'end_time': end_time
            })
        else:
            return jsonify({'error': result.get('error', 'Failed to redo section')}), 500
            
    except Exception as e:
        logger.error(f"Error redoing section: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/segments', methods=['GET'])
def get_all_segments(session_id):
    """Get all caption segments for the editor."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        if not video_session.chunk_manager:
            return jsonify({
                'success': True,
                'segments': [],
                'total': 0
            }), 200
        
        with video_session.state_lock:
            segments = []
            # Collect all segments from all chunks
            for chunk in video_session.chunk_manager.chunks:
                if chunk.timestamps:
                    for seg in chunk.timestamps:
                        segments.append({
                            'start': seg.get('start', 0),
                            'end': seg.get('end', 0),
                            'text': seg.get('text', ''),
                            'translation': seg.get('translation', ''),
                            'words': seg.get('words', [])
                        })
            
            # Sort by start time
            segments.sort(key=lambda x: x['start'])
        
        logger.info(f"Retrieved {len(segments)} segments for session {session_id}")
        return jsonify({
            'success': True,
            'segments': segments,
            'total': len(segments)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting segments: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/segment/<int:segment_id>', methods=['PUT'])
def update_segment(session_id, segment_id):
    """Update a specific caption segment (text, translation, and timing)."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = request.get_json()
        new_text = data.get('text')
        new_translation = data.get('translation')
        new_start = data.get('start_time')
        new_end = data.get('end_time')
        
        if new_text is None and new_translation is None and new_start is None and new_end is None:
            return jsonify({'error': 'No update data provided'}), 400
        
        if not video_session.chunk_manager:
            return jsonify({'error': 'No chunks available'}), 404
        
        # Validate timing if provided
        if new_start is not None or new_end is not None:
            try:
                if new_start is not None:
                    new_start = float(new_start)
                    if new_start < 0:
                        return jsonify({'error': 'Start time must be non-negative'}), 400
                
                if new_end is not None:
                    new_end = float(new_end)
                    if new_end < 0:
                        return jsonify({'error': 'End time must be non-negative'}), 400
                
                # If both provided, ensure start < end and minimum duration
                if new_start is not None and new_end is not None:
                    if new_start >= new_end:
                        return jsonify({'error': 'Start time must be less than end time'}), 400
                    if (new_end - new_start) < 0.1:
                        return jsonify({'error': 'Segment duration must be at least 0.1 seconds'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid time format'}), 400
        
        with video_session.state_lock:
            # Collect all segments to find the target by index
            current_index = 0
            found = False
            target_chunk = None
            target_seg = None
            
            for chunk in video_session.chunk_manager.chunks:
                if not chunk.timestamps:
                    continue
                    
                for seg in chunk.timestamps:
                    if current_index == segment_id:
                        target_chunk = chunk
                        target_seg = seg
                        found = True
                        break
                    current_index += 1
                
                if found:
                    break
            
            if not found:
                return jsonify({'error': 'Invalid segment ID'}), 404
            
            # If only one timing value provided, use current value for the other
            if new_start is None and new_end is not None:
                new_start = target_seg.get('start', 0.0)
            if new_end is None and new_start is not None:
                new_end = target_seg.get('end', new_start + 1.0)
            
            # Final validation with actual values
            if new_start is not None and new_end is not None:
                if new_start >= new_end:
                    return jsonify({'error': 'Start time must be less than end time'}), 400
                if (new_end - new_start) < 0.1:
                    return jsonify({'error': 'Segment duration must be at least 0.1 seconds'}), 400
            
            # Update the segment
            if new_text is not None:
                target_seg['text'] = new_text
            if new_translation is not None:
                target_seg['translation'] = new_translation
            if new_start is not None:
                target_seg['start'] = new_start
            if new_end is not None:
                target_seg['end'] = new_end
            
            # Re-sort timestamps within chunk to maintain chronological order
            if new_start is not None or new_end is not None:
                target_chunk.timestamps.sort(key=lambda s: s.get('start', 0))
            
            logger.info(f"Updated segment {segment_id} in session {session_id}")
        
        return jsonify({
            'success': True,
            'message': 'Segment updated successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating segment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/segment/<int:segment_id>', methods=['DELETE'])
def delete_segment(session_id, segment_id):
    """Delete a specific caption segment."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        if not video_session.chunk_manager:
            return jsonify({'error': 'No chunks available'}), 404
        
        with video_session.state_lock:
            # Collect all segments to find the target by index
            current_index = 0
            found = False
            removed_segment = None
            
            for chunk in video_session.chunk_manager.chunks:
                if not chunk.timestamps:
                    continue
                
                for i, seg in enumerate(chunk.timestamps):
                    if current_index == segment_id:
                        # Remove this segment
                        removed_segment = chunk.timestamps.pop(i)
                        found = True
                        logger.info(f"Deleted segment {segment_id} from session {session_id}: "
                                  f"{removed_segment.get('start')}-{removed_segment.get('end')}")
                        break
                    current_index += 1
                
                if found:
                    break
            
            if not found:
                return jsonify({'error': 'Invalid segment ID'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Segment deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting segment: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/segments/batch-delete', methods=['POST'])
def batch_delete_segments(session_id):
    """Delete multiple caption segments in a single request."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        data = request.get_json()
        segment_ids = data.get('segment_ids', [])
        
        if not segment_ids:
            return jsonify({'error': 'No segment IDs provided'}), 400
        
        if not video_session.chunk_manager:
            return jsonify({'error': 'No chunks available'}), 404
        
        # Sort segment IDs in descending order to delete from end to start
        # This prevents index shifting issues during deletion
        segment_ids_sorted = sorted(segment_ids, reverse=True)
        
        with video_session.state_lock:
            deleted_count = 0
            
            for target_id in segment_ids_sorted:
                current_index = 0
                found = False
                
                for chunk in video_session.chunk_manager.chunks:
                    if not chunk.timestamps:
                        continue
                    
                    for i, seg in enumerate(chunk.timestamps):
                        if current_index == target_id:
                            # Remove this segment
                            removed_segment = chunk.timestamps.pop(i)
                            deleted_count += 1
                            found = True
                            logger.info(f"Deleted segment {target_id} from session {session_id}: "
                                      f"{removed_segment.get('start')}-{removed_segment.get('end')}")
                            break
                        current_index += 1
                    
                    if found:
                        break
            
            logger.info(f"Batch deleted {deleted_count} segments from session {session_id}")
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} segment(s) successfully',
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error batch deleting segments: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@video_bp.route('/session/<session_id>/video', methods=['GET'])
def serve_video(session_id):
    """Serve the video file for playback (MP4 format for browser compatibility)."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Use MP4 path if available (converted for browser compatibility)
    # Otherwise fall back to original video path
    video_path = Path(video_session.mp4_path) if video_session.mp4_path else Path(video_session.video_path)
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return jsonify({'error': 'Video file not found'}), 404
    
    logger.debug(f"Serving video: {video_path} ({video_path.stat().st_size / (1024*1024):.2f} MB)")
    
    return send_file(
        str(video_path),
        mimetype='video/mp4',
        as_attachment=False
    )


@video_bp.route('/session/<session_id>/audio-sources', methods=['GET'])
def check_audio_sources(session_id):
    """Check which audio sources are available (original and vocals)."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    # Debug logging
    logger.info(f"Checking audio sources for session {session_id}")
    logger.info(f"  vocals_audio_path: {getattr(video_session, 'vocals_audio_path', 'NOT SET')}")
    logger.info(f"  original_audio_path: {getattr(video_session, 'original_audio_path', 'NOT SET')}")
    
    # Check if vocals audio exists
    vocals_path = getattr(video_session, 'vocals_audio_path', None)
    vocals_available = False
    
    if vocals_path:
        vocals_file = Path(vocals_path)
        vocals_available = vocals_file.exists()
        logger.info(f"  Vocals file exists: {vocals_available} (path: {vocals_path})")
    else:
        logger.info(f"  Vocals path not set")
    
    # Check original audio
    original_path = getattr(video_session, 'original_audio_path', None)
    original_available = False
    
    if original_path:
        original_file = Path(original_path)
        original_available = original_file.exists()
        logger.info(f"  Original file exists: {original_available} (path: {original_path})")
    else:
        logger.info(f"  Original path not set")
    
    return jsonify({
        'success': True,
        'vocals_available': vocals_available,
        'original_available': original_available
    }), 200


@video_bp.route('/session/<session_id>/audio/<source>', methods=['GET'])
def serve_audio_source(session_id, source):
    """
    Serve audio file for the specified source.
    
    Args:
        source: 'original' or 'vocals'
    """
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    audio_path = None
    
    if source == 'original':
        if hasattr(video_session, 'original_audio_path') and video_session.original_audio_path:
            audio_path = Path(video_session.original_audio_path)
    
    elif source == 'vocals':
        if hasattr(video_session, 'vocals_audio_path') and video_session.vocals_audio_path:
            audio_path = Path(video_session.vocals_audio_path)
    
    if audio_path and audio_path.exists():
        return send_file(
            str(audio_path),
            mimetype='audio/wav',
            as_attachment=False
        )
    
    return jsonify({'error': f'Audio source "{source}" not found'}), 404


@video_bp.route('/session/<session_id>/waveform', methods=['GET'])
def serve_waveform_image(session_id):
    """
    Serve waveform visualization PNG image.
    
    Returns:
        PNG image file if available, 404 if not found
    """
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        logger.warning(f"Waveform request: Session {session_id} not found")
        return jsonify({'error': 'Session not found'}), 404
    
    # Check if waveform image exists
    waveform_path = getattr(video_session, 'waveform_image_path', None)
    
    logger.debug(f"Waveform request for session {session_id}: path={waveform_path}")
    
    if waveform_path:
        waveform_file = Path(waveform_path)
        if waveform_file.exists():
            logger.info(f"✅ Serving waveform image: {waveform_path} ({waveform_file.stat().st_size} bytes)")
            return send_file(
                str(waveform_file),
                mimetype='image/png',
                as_attachment=False
            )
        else:
            logger.warning(f"❌ Waveform file does not exist: {waveform_path}")
    else:
        logger.warning(f"❌ Waveform path is None for session {session_id}")
    
    return jsonify({'error': 'Waveform image not available'}), 404


@video_bp.route('/languages', methods=['GET'])
def get_available_languages():
    """Get list of all available languages for source/target selection."""
    from modules.languages import get_valid_languages
    
    all_languages = get_valid_languages()
    
    # Create a mapping of language codes to full names
    # Extract unique language codes (2-3 letter codes)
    language_codes = [lang for lang in all_languages if len(lang) <= 3]
    # Extract full language names
    language_names = [lang for lang in all_languages if len(lang) > 3]
    
    # Create a structured list for UI
    languages_list = []
    
    # Add Auto-detect option for source language
    languages_list.append({'code': 'auto', 'name': 'Auto-detect'})
    
    # Create mapping: code -> best matching name
    code_to_name = {}
    common_mappings = {
        'en': 'English', 'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese',
        'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian',
        'pt': 'Portuguese', 'ru': 'Russian', 'ar': 'Arabic', 'hi': 'Hindi',
        'bn': 'Bengali', 'pa': 'Punjabi', 'te': 'Telugu', 'mr': 'Marathi',
        'ta': 'Tamil', 'ur': 'Urdu', 'gu': 'Gujarati', 'kn': 'Kannada',
        'ml': 'Malayalam', 'th': 'Thai', 'vi': 'Vietnamese', 'tr': 'Turkish',
        'pl': 'Polish', 'uk': 'Ukrainian', 'ro': 'Romanian', 'nl': 'Dutch',
        'el': 'Greek', 'cs': 'Czech', 'sv': 'Swedish', 'hu': 'Hungarian',
        'fi': 'Finnish', 'no': 'Norwegian', 'da': 'Danish', 'id': 'Indonesian',
        'ms': 'Malay', 'he': 'Hebrew', 'fa': 'Persian', 'ca': 'Catalan'
    }
    
    # Add all language codes with proper names
    for code in sorted(language_codes):
        if code in common_mappings:
            name = common_mappings[code]
        else:
            name = code.upper()
        languages_list.append({'code': code, 'name': f"{name} ({code})"})
    
    return jsonify({
        'success': True,
        'languages': languages_list
    })


# WebSocket Events (to be used with Flask-SocketIO)

def init_video_socketio(app):
    """
    Initialize WebSocket events for video translation.
    
    Args:
        app: Flask application instance
        
    Returns:
        SocketIO instance
    """
    from flask_socketio import SocketIO, emit, join_room, leave_room
    
    # Use threading mode with simple-websocket for PyInstaller compatibility
    # Note: async_mode must be explicitly set for frozen applications
    socketio = None
    
    # Try different async modes in order of preference
    async_modes_to_try = ['threading', None]  # None = auto-detect
    
    for async_mode in async_modes_to_try:
        try:
            if async_mode:
                logger.info(f"Attempting to initialize Socket.IO with async_mode='{async_mode}'")
                socketio = SocketIO(app, cors_allowed_origins="*", async_mode=async_mode, 
                              logger=False, engineio_logger=False)
            else:
                logger.info("Attempting to initialize Socket.IO with auto-detect mode")
                socketio = SocketIO(app, cors_allowed_origins="*", 
                              logger=False, engineio_logger=False)
            
            logger.info(f"Socket.IO initialized successfully with async_mode={socketio.async_mode}")  # type: ignore[attr-defined]
            break  # Success, exit loop
            
        except ValueError as e:
            logger.warning(f"async_mode '{async_mode}' failed: {e}")
            if async_mode is None:
                # This was our last attempt
                logger.error("All Socket.IO initialization attempts failed!")
                raise
            continue  # Try next mode
        except Exception as e:
            logger.error(f"Unexpected error initializing Socket.IO: {e}")
            if async_mode is None:
                raise
            continue
    
    if socketio is None:
        raise RuntimeError("Failed to initialize Socket.IO - no compatible async mode found")
    
    # Store global reference for sessions
    global _socketio_instance
    _socketio_instance = socketio
    
    @socketio.on('join_video_session')
    def on_join_session(data):
        """Client joins a video session room."""
        session_id = data.get('session_id')
        
        with session_lock:
            if session_id not in video_sessions:
                emit('error', {'message': 'Session not found'})
                return
        
        join_room(session_id)
        emit('joined', {'session_id': session_id})
        logger.info(f"Client joined video session: {session_id}")
    
    @socketio.on('leave_video_session')
    def on_leave_session(data):
        """Client leaves a video session room."""
        session_id = data.get('session_id')
        leave_room(session_id)
        logger.info(f"Client left video session: {session_id}")
    
    @socketio.on('update_playback')
    def on_update_playback(data):
        """Update playback position from client."""
        session_id = data.get('session_id')
        timestamp = float(data.get('timestamp', 0))
        
        with session_lock:
            video_session = video_sessions.get(session_id)
        
        if video_session:
            video_session.update_playback_position(timestamp)
            
            # Get captions at this timestamp
            captions = video_session.get_captions_at_time(timestamp)
            
            # ALWAYS emit caption updates (including empty ones during silence)
            # This fixes the "stuck caption" issue by clearing captions during silence
            emit('caption_update', captions, to=session_id)
            
            # Log only when captions change
            if captions.get('transcription') or captions.get('translation'):
                logger.debug(f"Caption update sent for session {session_id} at {timestamp:.2f}s: "
                           f"transcription={bool(captions.get('transcription'))}, "
                           f"translation={bool(captions.get('translation'))}")
            else:
                logger.debug(f"Silence update sent for session {session_id} at {timestamp:.2f}s (clearing captions)")
    
    logger.info("Video WebSocket events initialized")
    
    return socketio


# Cleanup function for server shutdown

def cleanup_all_sessions():
    """Cleanup all active sessions on server shutdown."""
    logger.info("Cleaning up all video sessions...")
    
    with session_lock:
        for session_id, video_session in list(video_sessions.items()):
            try:
                video_session.stop()
                video_session.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up session {session_id}: {e}")
        
        video_sessions.clear()
    
    # Clean up entire video_uploads folder if no keep_temp flag is globally set
    # Check if any session had keep_temp enabled
    global _keep_temp_global
    if not _keep_temp_global and UPLOAD_FOLDER.exists():
        try:
            import shutil
            shutil.rmtree(UPLOAD_FOLDER)
            logger.info(f"Cleaned up video uploads folder: {UPLOAD_FOLDER}")
            # Recreate the folder for future use
            UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error cleaning up video uploads folder: {e}")
    
    logger.info("All video sessions cleaned up")

# Register cleanup on exit
import atexit
atexit.register(cleanup_all_sessions)
