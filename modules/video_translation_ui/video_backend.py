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

def set_model_dir(model_dir: str):
    """Set the global model directory from parser_args."""
    global _global_model_dir
    _global_model_dir = model_dir
    logger.info(f"Video UI model directory set to: {model_dir}")

# Upload configuration
# Use absolute path from current working directory to avoid module-relative issues
import sys
WORKSPACE_ROOT = Path(os.getcwd())
UPLOAD_FOLDER = WORKSPACE_ROOT / 'temp' / 'video_uploads'
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v'}
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
            'model_dir': _global_model_dir  # Use global model_dir from parser_args
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
            # Initialize video processor
            self.video_processor = VideoProcessor(
                self.video_path,
                temp_dir=str(UPLOAD_FOLDER / self.session_id)
            )
            
            # Extract metadata
            self.metadata = self.video_processor.extract_metadata()
            
            # Extract full audio (with optional Demucs preprocessing)
            # This MUST happen before chunking so Demucs can process the entire audio
            enable_vocals = self.config.get('enable_vocal_isolation', False)
            if enable_vocals:
                logger.info(f"Extracting full audio for vocal isolation preprocessing...")
            
            full_audio_path = self.video_processor.extract_audio(
                isolate_vocals=enable_vocals,
                demucs_model=self.config.get('demucs_model', 'htdemucs'),
                demucs_jobs=self.config.get('demucs_jobs', 0)
            )
            
            # Store full audio path for chunk extraction
            self.full_audio_path = full_audio_path
            logger.info(f" Full audio ready: {full_audio_path}")
            
            # Initialize chunk manager
            # Process ENTIRE video as one chunk (no buffering/splitting)
            chunk_duration = self.metadata['duration']  # Use full video duration
            self.chunk_manager = ChunkManager(
                video_duration=self.metadata['duration'],
                chunk_duration=chunk_duration
            )
            
            # Initialize transcription manager
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
                model_dir=self.config.get('model_dir', './models')
            )
            
            # Initialize buffer manager
            self.buffer_manager = BufferManager(
                chunk_manager=self.chunk_manager,
                buffer_seconds=self.metadata['duration'],  # Buffer entire video
                max_concurrent=self.config.get('max_concurrent', 2),
                on_chunk_processed=self._on_chunk_processed
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
        
        # Get total chunk count for progress tracking
        total_chunks = len(self.chunk_manager.chunks) if self.chunk_manager else 0
        processed_count = 0
        start_time = time.time()
        
        logger.info(f" Starting video processing: {total_chunks} chunks to process")
        
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
                    
                    # Update chunk status
                    if result['success']:
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
            return {'transcription': '', 'translation': '', 'language': 'unknown'}
        
        chunk = self.chunk_manager.get_chunk_at_time(timestamp)
        
        if not chunk:
            logger.debug(f"No chunk found for timestamp {timestamp:.2f}s")
            return {'transcription': '', 'translation': '', 'language': 'unknown'}
        
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
                    
                    logger.debug(f"Found active caption segment at {timestamp:.2f}s: "
                               f"{segment_start:.2f}s - {segment_end:.2f}s")
                    logger.debug(f"  Transcription: '{transcription[:50]}...' (len={len(transcription)})")
                    logger.debug(f"  Translation: '{translation[:50]}...' (len={len(translation)})")
                    
                    return {
                        'transcription': transcription,
                        'translation': translation,
                        'language': self.transcription_manager.source_language if self.transcription_manager else 'unknown'
                    }
            
            # Timestamp is between caption segments (silence) - return empty
            logger.debug(f"Timestamp {timestamp:.2f}s is between caption segments (silence)")
            return {'transcription': '', 'translation': '', 'language': 'unknown'}
        
        # Fallback: chunk has no timestamp segments, return full chunk transcription
        if chunk.transcription:
            return {
                'transcription': chunk.transcription,
                'translation': chunk.translation or '',
                'language': self.transcription_manager.source_language if self.transcription_manager else 'unknown'
            }
        
        return {'transcription': '', 'translation': '', 'language': 'unknown'}
    
    def export_captions(self, format: str = 'srt') -> Optional[str]:
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
            if not chunk.transcription:
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
                    'text': chunk.transcription,
                    'translation': chunk.translation or ''
                })
        
        # Sort by start time
        caption_segments.sort(key=lambda x: x['start'])
        
        if format.lower() == 'srt':
            return self._export_srt(caption_segments)
        elif format.lower() == 'vtt':
            return self._export_vtt(caption_segments)
        else:
            return None
    
    def _export_srt(self, segments: List[Dict]) -> str:
        """Export caption segments as SRT format."""
        srt_content = []
        
        for i, segment in enumerate(segments, 1):
            start_time = self._format_srt_time(segment['start'])
            end_time = self._format_srt_time(segment['end'])
            
            # Use translation if available, otherwise transcription
            text = segment.get('translation') or segment.get('text', '')
            
            if not text.strip():
                continue
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(text)
            srt_content.append("")  # Empty line between entries
        
        return "\n".join(srt_content)
    
    def _export_vtt(self, segments: List[Dict]) -> str:
        """Export caption segments as WebVTT format."""
        vtt_content = ["WEBVTT\n"]
        
        for segment in segments:
            start_time = self._format_vtt_time(segment['start'])
            end_time = self._format_vtt_time(segment['end'])
            
            # Use translation if available, otherwise transcription
            text = segment.get('translation') or segment.get('text', '')
            
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
            if self.video_processor:
                self.video_processor.cleanup()
            
            # Clean up temp directory
            temp_dir = UPLOAD_FOLDER / self.session_id
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory for session {self.session_id}")
        except Exception as e:
            logger.error(f"Error cleaning up session {self.session_id}: {e}")


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
        
        # Extract basic metadata for display (without full initialization)
        video_processor = VideoProcessor(str(video_path))
        metadata = video_processor.extract_metadata()
        
        logger.info(f" Session created: {session_id} (not initialized - awaiting configuration)")
        
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
    """Export captions as SRT or VTT file."""
    format = request.args.get('format', 'srt').lower()
    
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    captions = video_session.export_captions(format)
    
    if not captions:
        return jsonify({'error': 'No captions available or invalid format'}), 400
    
    # Create temporary file
    export_path = UPLOAD_FOLDER / session_id / f"captions.{format}"
    export_path.write_text(captions, encoding='utf-8')
    
    return send_file(
        str(export_path),
        as_attachment=True,
        download_name=f"captions.{format}",
        mimetype='text/plain'
    )


@video_bp.route('/session/<session_id>/video', methods=['GET'])
def serve_video(session_id):
    """Serve the video file for playback."""
    with session_lock:
        video_session = video_sessions.get(session_id)
    
    if not video_session:
        return jsonify({'error': 'Session not found'}), 404
    
    video_path = Path(video_session.video_path)
    
    if not video_path.exists():
        return jsonify({'error': 'Video file not found'}), 404
    
    return send_file(
        str(video_path),
        mimetype='video/mp4',
        as_attachment=False
    )


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
    
    # Use threading mode to avoid eventlet/gevent dependencies
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
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
    
    logger.info("All video sessions cleaned up")
