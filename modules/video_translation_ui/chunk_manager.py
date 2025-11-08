"""
Chunk Manager Module

Manages audio segment chunking for buffered video transcription.
Similar to HLS stream chunk logic but for local video files.

Handles:
- Dividing video audio into time-based chunks
- Tracking chunk processing status
- Managing chunk prioritization for seeks
- Coordinating with buffer manager
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ChunkStatus(Enum):
    """Status of a chunk in the processing pipeline."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PRIORITY = "priority"  # For seek operations


@dataclass
class AudioChunk:
    """
    Represents a chunk of audio from the video.
    
    Attributes:
        chunk_id: Unique identifier for the chunk
        start_time: Start time in seconds
        end_time: End time in seconds
        duration: Duration of the chunk in seconds
        audio_path: Path to extracted audio file (if extracted)
        status: Current processing status
        transcription: Transcribed text (if completed)
        translation: Translated text (if completed)
        timestamps: SRT-style timestamps for captions
        processed_until: How far into the chunk we've analyzed (including silence)
        priority: Priority level (higher = more important)
        created_at: Timestamp when chunk was created
        completed_at: Timestamp when processing completed
    """
    chunk_id: int
    start_time: float
    end_time: float
    duration: float
    audio_path: Optional[str] = None
    status: ChunkStatus = ChunkStatus.PENDING
    transcription: Optional[str] = None
    translation: Optional[str] = None
    timestamps: List[Dict] = field(default_factory=list)
    processed_until: float = 0.0  # How far we've analyzed (including silence)
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    
    def get_progress(self) -> float:
        """Calculate progress percentage of this chunk."""
        if self.status == ChunkStatus.COMPLETED:
            return 100.0
        elif self.status == ChunkStatus.PROCESSING:
            return 50.0
        elif self.status == ChunkStatus.FAILED:
            return 0.0
        else:
            return 0.0
    
    def to_dict(self) -> Dict:
        """Convert chunk to dictionary for serialization."""
        return {
            'chunk_id': self.chunk_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'status': self.status.value,
            'transcription': self.transcription,
            'translation': self.translation,
            'timestamps': self.timestamps,
            'priority': self.priority,
            'progress': self.get_progress(),
        }


class ChunkManager:
    """
    Manages chunking strategy and chunk tracking for video transcription.
    
    Handles dividing video into manageable chunks, tracking their status,
    and coordinating with the buffer manager for optimal processing.
    """
    
    def __init__(self, video_duration: float, chunk_duration: float = 30.0):
        """
        Initialize Chunk Manager.
        
        Args:
            video_duration: Total duration of video in seconds
            chunk_duration: Duration of each chunk in seconds (default: 30s)
        """
        self.video_duration = video_duration
        self.chunk_duration = chunk_duration
        self.chunks: List[AudioChunk] = []
        self.completed_chunks: Dict[int, AudioChunk] = {}
        self.failed_chunks: List[int] = []
        
        self._create_chunks()
        logger.info(f"ChunkManager initialized: {len(self.chunks)} chunks, "
                   f"duration={video_duration:.2f}s, chunk_size={chunk_duration}s")
    
    def _create_chunks(self):
        """Create chunk objects for the entire video duration."""
        chunk_id = 0
        current_time = 0.0
        
        while current_time < self.video_duration:
            # Calculate chunk end time (don't exceed video duration)
            end_time = min(current_time + self.chunk_duration, self.video_duration)
            duration = end_time - current_time
            
            chunk = AudioChunk(
                chunk_id=chunk_id,
                start_time=current_time,
                end_time=end_time,
                duration=duration
            )
            
            self.chunks.append(chunk)
            chunk_id += 1
            current_time = end_time
        
        logger.debug(f"Created {len(self.chunks)} chunks")
    
    def get_chunk(self, chunk_id: int) -> Optional[AudioChunk]:
        """
        Get chunk by ID.
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            AudioChunk or None if not found
        """
        if 0 <= chunk_id < len(self.chunks):
            return self.chunks[chunk_id]
        return None
    
    def get_chunk_at_time(self, timestamp: float) -> Optional[AudioChunk]:
        """
        Get chunk that contains the given timestamp.
        
        Args:
            timestamp: Time in seconds
            
        Returns:
            AudioChunk containing the timestamp, or None
        """
        for chunk in self.chunks:
            if chunk.start_time <= timestamp < chunk.end_time:
                return chunk
        return None
    
    def get_next_pending_chunk(self) -> Optional[AudioChunk]:
        """
        Get the next pending chunk to process.
        
        Priority order:
        1. PRIORITY status (from seeks)
        2. First PENDING chunk
        
        Returns:
            Next chunk to process, or None if all processed
        """
        # First check for priority chunks
        priority_chunks = [c for c in self.chunks if c.status == ChunkStatus.PRIORITY]
        if priority_chunks:
            # Sort by priority (highest first), then by chunk_id
            priority_chunks.sort(key=lambda x: (-x.priority, x.chunk_id))
            return priority_chunks[0]
        
        # Otherwise, get first pending chunk
        for chunk in self.chunks:
            if chunk.status == ChunkStatus.PENDING:
                return chunk
        
        return None
    
    def get_chunks_in_range(self, 
                           start_time: float, 
                           end_time: float) -> List[AudioChunk]:
        """
        Get all chunks within a time range.
        
        Args:
            start_time: Range start in seconds
            end_time: Range end in seconds
            
        Returns:
            List of chunks within the range
        """
        result = []
        for chunk in self.chunks:
            # Check if chunk overlaps with the range
            if chunk.start_time < end_time and chunk.end_time > start_time:
                result.append(chunk)
        return result
    
    def mark_chunk_processing(self, chunk_id: int) -> bool:
        """
        Mark a chunk as currently being processed.
        
        Args:
            chunk_id: Chunk identifier
            
        Returns:
            True if status was updated, False otherwise
        """
        chunk = self.get_chunk(chunk_id)
        if chunk and chunk.status in [ChunkStatus.PENDING, ChunkStatus.PRIORITY]:
            chunk.status = ChunkStatus.PROCESSING
            logger.debug(f"Chunk {chunk_id} marked as processing")
            return True
        return False
    
    def mark_chunk_completed(self, 
                            chunk_id: int,
                            transcription: str,
                            translation: Optional[str] = None,
                            timestamps: Optional[List[Dict]] = None,
                            language: Optional[str] = None) -> bool:
        """
        Mark a chunk as completed with results.
        
        Args:
            chunk_id: Chunk identifier
            transcription: Full transcription text for the chunk
            translation: Optional full translation text
            timestamps: List of caption segments with accurate timing:
                [{'start': 10.5, 'end': 13.2, 'text': 'Hello', 'translation': 'Hola'}, ...]
            language: Detected/used language
            
        Returns:
            True if status was updated, False otherwise
        """
        chunk = self.get_chunk(chunk_id)
        if chunk and chunk.status == ChunkStatus.PROCESSING:
            chunk.status = ChunkStatus.COMPLETED
            chunk.transcription = transcription
            chunk.translation = translation
            chunk.timestamps = timestamps or []
            chunk.completed_at = time.time()
            
            self.completed_chunks[chunk_id] = chunk
            logger.debug(f"Chunk {chunk_id} marked as completed with {len(chunk.timestamps)} caption segments")
            return True
        return False
    
    def mark_chunk_failed(self, chunk_id: int, error_message: str = "") -> bool:
        """
        Mark a chunk as failed.
        
        Args:
            chunk_id: Chunk identifier
            error_message: Optional error description
            
        Returns:
            True if status was updated, False otherwise
        """
        chunk = self.get_chunk(chunk_id)
        if chunk:
            chunk.status = ChunkStatus.FAILED
            chunk.error_message = error_message
            
            if chunk_id not in self.failed_chunks:
                self.failed_chunks.append(chunk_id)
            
            logger.warning(f"Chunk {chunk_id} marked as failed: {error_message}")
            return True
        return False
    
    def prioritize_chunk(self, chunk_id: int, priority: int = 100):
        """
        Set a chunk as high priority (e.g., for seek operations).
        
        Args:
            chunk_id: Chunk identifier
            priority: Priority level (higher = more important)
        """
        chunk = self.get_chunk(chunk_id)
        if chunk and chunk.status == ChunkStatus.PENDING:
            chunk.status = ChunkStatus.PRIORITY
            chunk.priority = priority
            logger.debug(f"Chunk {chunk_id} prioritized with level {priority}")
    
    def prioritize_range(self, start_time: float, end_time: float, priority: int = 100):
        """
        Prioritize all chunks in a time range (e.g., after a seek).
        
        Args:
            start_time: Range start in seconds
            end_time: Range end in seconds
            priority: Priority level
        """
        chunks_in_range = self.get_chunks_in_range(start_time, end_time)
        for chunk in chunks_in_range:
            if chunk.status == ChunkStatus.PENDING:
                self.prioritize_chunk(chunk.chunk_id, priority)
        
        logger.info(f"Prioritized {len(chunks_in_range)} chunks in range "
                   f"{start_time:.2f}s - {end_time:.2f}s")
    
    def get_progress(self) -> Dict:
        """
        Get overall processing progress.
        
        Returns:
            dict: Progress information including:
                - total_chunks: Total number of chunks
                - completed: Number of completed chunks
                - processing: Number of chunks being processed
                - pending: Number of pending chunks
                - failed: Number of failed chunks
                - progress_pct: Overall progress percentage
        """
        completed = sum(1 for c in self.chunks if c.status == ChunkStatus.COMPLETED)
        processing = sum(1 for c in self.chunks if c.status == ChunkStatus.PROCESSING)
        pending = sum(1 for c in self.chunks if c.status == ChunkStatus.PENDING)
        priority = sum(1 for c in self.chunks if c.status == ChunkStatus.PRIORITY)
        failed = len(self.failed_chunks)
        
        progress_pct = (completed / len(self.chunks)) * 100 if self.chunks else 0
        
        return {
            'total_chunks': len(self.chunks),
            'completed': completed,
            'processing': processing,
            'pending': pending,
            'priority': priority,
            'failed': failed,
            'progress_pct': round(progress_pct, 2),
        }
    
    def get_buffer_status(self, current_time: float, buffer_distance: float = 30.0) -> Dict:
        """
        Get buffer status relative to current playback position.
        
        Args:
            current_time: Current playback position in seconds
            buffer_distance: Desired buffer distance ahead in seconds
            
        Returns:
            dict: Buffer status information
        """
        # Find chunks in buffer range
        buffer_end = current_time + buffer_distance
        buffer_chunks = self.get_chunks_in_range(current_time, buffer_end)
        
        # Calculate how many are completed OR have timestamps (PROCESSING with incremental updates)
        # This fixes the "0s ahead" issue when chunks are PROCESSING but have usable timestamps
        completed_in_buffer = sum(
            1 for c in buffer_chunks 
            if c.status == ChunkStatus.COMPLETED or (c.status == ChunkStatus.PROCESSING and len(c.timestamps) > 0)
        )
        
        buffer_pct = (completed_in_buffer / len(buffer_chunks) * 100) if buffer_chunks else 0
        
        # Find the furthest point we've processed (including silence)
        # This is more accurate than just looking at last speech timestamp
        furthest_available = current_time
        for chunk in self.chunks:
            # For COMPLETED chunks, use end_time
            if chunk.status == ChunkStatus.COMPLETED:
                if chunk.end_time > furthest_available:
                    furthest_available = chunk.end_time
            # For PROCESSING chunks, use processed_until (accounts for speech + silence)
            elif chunk.status == ChunkStatus.PROCESSING:
                # Use processed_until if set, otherwise fall back to last timestamp
                if chunk.processed_until > 0:
                    processed_absolute = chunk.start_time + chunk.processed_until
                    if processed_absolute > furthest_available:
                        furthest_available = processed_absolute
                elif len(chunk.timestamps) > 0:
                    last_timestamp_end = chunk.timestamps[-1].get('end', chunk.start_time)
                    if last_timestamp_end > furthest_available:
                        furthest_available = last_timestamp_end
        
        seconds_buffered = max(0, furthest_available - current_time)
        
        return {
            'current_time': float(current_time),
            'buffer_distance': float(buffer_distance),
            'buffer_chunks': int(len(buffer_chunks)),
            'completed_in_buffer': int(completed_in_buffer),
            'buffer_pct': float(round(buffer_pct, 2)),
            'seconds_buffered': float(round(seconds_buffered, 2)),
            'is_ready': bool(seconds_buffered >= buffer_distance * 0.5),  # At least 50% buffered
        }
    
    def get_all_chunks_data(self) -> List[Dict]:
        """
        Get data for all chunks (for frontend display).
        
        Returns:
            List of chunk dictionaries
        """
        return [chunk.to_dict() for chunk in self.chunks]
    
    def retry_failed_chunks(self):
        """Reset all failed chunks to pending status for retry."""
        retry_count = 0
        for chunk_id in self.failed_chunks:
            chunk = self.get_chunk(chunk_id)
            if chunk:
                chunk.status = ChunkStatus.PENDING
                chunk.error_message = None
                retry_count += 1
        
        self.failed_chunks.clear()
        logger.info(f"Reset {retry_count} failed chunks for retry")
    
    def reset(self):
        """Reset all chunks to initial state."""
        for chunk in self.chunks:
            chunk.status = ChunkStatus.PENDING
            chunk.transcription = None
            chunk.translation = None
            chunk.timestamps = []
            chunk.audio_path = None
            chunk.priority = 0
            chunk.completed_at = None
            chunk.error_message = None
        
        self.completed_chunks.clear()
        self.failed_chunks.clear()
        logger.info("All chunks reset to initial state")
