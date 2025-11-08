"""
Buffer Manager Module

Manages the buffering strategy for video transcription.
Coordinates chunk processing to maintain a buffer ahead of playback.

Handles:
- Processing queue management
- Buffer distance maintenance
- Resource allocation based on RAM settings
- Priority processing for seeks
"""

import os
import logging
import threading
import queue
import time
from typing import Optional, Callable, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class BufferStrategy(Enum):
    """Buffering strategy options."""
    INITIAL = "initial"  # Pre-process initial buffer
    CONTINUOUS = "continuous"  # Continuously process ahead
    ON_DEMAND = "on_demand"  # Process only what's needed
    PRIORITY = "priority"  # Priority processing (seeks)


class BufferManager:
    """
    Manages buffering strategy and processing queue for video transcription.
    
    Coordinates with ChunkManager to maintain a buffer of processed chunks
    ahead of the current playback position.
    """
    
    def __init__(self, 
                 chunk_manager,
                 buffer_seconds: float = 60.0,
                 max_concurrent: int = 2,
                 on_chunk_processed: Optional[Callable] = None):
        """
        Initialize Buffer Manager.
        
        Args:
            chunk_manager: ChunkManager instance
            buffer_seconds: Desired buffer distance in seconds (30, 60, or 120)
            max_concurrent: Maximum concurrent chunk processing tasks
            on_chunk_processed: Optional callback when chunk is processed
        """
        self.chunk_manager = chunk_manager
        self.buffer_seconds = buffer_seconds
        self.max_concurrent = max_concurrent
        self.on_chunk_processed = on_chunk_processed
        
        # Processing state
        self.current_playback_time = 0.0
        self.is_processing = False
        self.is_paused = False
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # Processing queue
        self.processing_queue = queue.Queue()
        self.active_tasks = []
        self.task_lock = threading.Lock()
        
        # Strategy
        self.current_strategy = BufferStrategy.INITIAL
        
        logger.info(f"BufferManager initialized: buffer={buffer_seconds}s, "
                   f"max_concurrent={max_concurrent}")
    
    def start_processing(self):
        """Start the buffer processing thread."""
        if self.is_processing:
            logger.warning("Buffer processing already started")
            return
        
        self.is_processing = True
        self.stop_event.clear()
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True
        )
        self.processing_thread.start()
        logger.info("Buffer processing started")
    
    def stop_processing(self):
        """Stop the buffer processing thread."""
        if not self.is_processing:
            return
        
        logger.info("Stopping buffer processing...")
        self.is_processing = False
        self.stop_event.set()
        
        if self.processing_thread:
            self.processing_thread.join(timeout=5.0)
        
        logger.info("Buffer processing stopped")
    
    def pause_processing(self):
        """Pause buffer processing (but don't stop the thread)."""
        self.is_paused = True
        logger.info("Buffer processing paused")
    
    def resume_processing(self):
        """Resume buffer processing."""
        self.is_paused = False
        logger.info("Buffer processing resumed")
    
    def update_playback_position(self, timestamp: float):
        """
        Update current playback position.
        
        Args:
            timestamp: Current playback time in seconds
        """
        self.current_playback_time = timestamp
        
        # Check if we need to prioritize processing
        self._check_buffer_health()
    
    def seek_to(self, timestamp: float):
        """
        Handle seek operation by prioritizing chunks around the new position.
        
        Args:
            timestamp: New playback position in seconds
        """
        self.current_playback_time = timestamp
        
        # Prioritize chunks in the buffer range after seek
        end_time = timestamp + self.buffer_seconds
        self.chunk_manager.prioritize_range(
            timestamp,
            end_time,
            priority=100
        )
        
        # Switch to priority strategy temporarily
        self.current_strategy = BufferStrategy.PRIORITY
        
        logger.info(f"Seek to {timestamp:.2f}s - prioritizing buffer range")
    
    def _processing_loop(self):
        """Main processing loop that maintains the buffer."""
        logger.debug("Processing loop started")
        
        while not self.stop_event.is_set():
            try:
                # Skip if paused
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # Determine what to process next
                chunk_to_process = self._get_next_chunk_to_process()
                
                if chunk_to_process:
                    # Add to queue (actual processing happens elsewhere)
                    self.processing_queue.put(chunk_to_process)
                    
                    # Mark as processing
                    self.chunk_manager.mark_chunk_processing(chunk_to_process.chunk_id)
                    
                    # Show buffer status periodically
                    completed = len([c for c in self.chunk_manager.chunks if c.status.name == 'COMPLETED'])
                    total = len(self.chunk_manager.chunks)
                    if chunk_to_process.chunk_id % 5 == 0:  # Every 5th chunk
                        logger.info(f" Buffer status: {completed}/{total} chunks completed")
                    
                    logger.debug(f"Queued chunk {chunk_to_process.chunk_id} for processing")
                else:
                    # No chunks to process, wait a bit
                    time.sleep(1.0)
                
                # Small delay to prevent busy-waiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}", exc_info=True)
                time.sleep(1.0)
        
        logger.debug("Processing loop ended")
    
    def _get_next_chunk_to_process(self):
        """
        Determine the next chunk to process based on current strategy.
        
        Returns:
            AudioChunk or None
        """
        # Check how many chunks are currently being processed
        with self.task_lock:
            active_count = len(self.active_tasks)
        
        if active_count >= self.max_concurrent:
            return None
        
        # Strategy 1: Priority chunks first (from seeks)
        priority_chunk = self._get_priority_chunk()
        if priority_chunk:
            self.current_strategy = BufferStrategy.PRIORITY
            return priority_chunk
        
        # Strategy 2: Continuously process ALL chunks sequentially (like sub_gen.py)
        # No artificial buffer limits - just process the entire file
        self.current_strategy = BufferStrategy.CONTINUOUS
        return self._get_next_continuous_chunk()
    
    def _get_priority_chunk(self):
        """Get the next priority chunk (from seeks)."""
        for chunk in self.chunk_manager.chunks:
            if chunk.status.value == "priority":
                return chunk
        return None
    
    def _get_next_needed_chunk(self):
        """Get the next chunk needed for playback (closest to current position)."""
        # Find pending chunks within buffer range
        buffer_end = self.current_playback_time + self.buffer_seconds
        buffer_chunks = self.chunk_manager.get_chunks_in_range(
            self.current_playback_time,
            buffer_end
        )
        
        # Get first pending/priority chunk
        for chunk in buffer_chunks:
            if chunk.status.value in ["pending", "priority"]:
                return chunk
        
        return None
    
    def _get_next_continuous_chunk(self):
        """Get the next chunk for continuous processing."""
        # Simply get the next pending chunk sequentially
        return self.chunk_manager.get_next_pending_chunk()
    
    def _check_buffer_health(self):
        """Check buffer health and track status without artificial limits."""
        buffer_status = self.chunk_manager.get_buffer_status(
            self.current_playback_time,
            self.buffer_seconds
        )
        
        # Just track the buffer status - no warnings during continuous processing
        # The buffer_seconds value is used for display purposes only
        logger.debug(f"Buffer: {buffer_status['seconds_buffered']:.1f}s ahead of playback")
    
    def mark_task_complete(self, chunk_id: int):
        """
        Mark a processing task as complete.
        
        Args:
            chunk_id: Completed chunk identifier
        """
        with self.task_lock:
            if chunk_id in self.active_tasks:
                self.active_tasks.remove(chunk_id)
        
        # Trigger callback if provided
        if self.on_chunk_processed:
            chunk = self.chunk_manager.get_chunk(chunk_id)
            if chunk:
                self.on_chunk_processed(chunk)
    
    def get_processing_queue_size(self) -> int:
        """Get the current size of the processing queue."""
        return self.processing_queue.qsize()
    
    def get_status(self) -> Dict:
        """
        Get current buffer manager status.
        
        Returns:
            dict: Status information
        """
        buffer_status = self.chunk_manager.get_buffer_status(
            self.current_playback_time,
            self.buffer_seconds
        )
        
        with self.task_lock:
            active_count = len(self.active_tasks)
        
        return {
            'is_processing': self.is_processing,
            'is_paused': self.is_paused,
            'current_strategy': self.current_strategy.value,
            'playback_position': self.current_playback_time,
            'buffer_seconds': self.buffer_seconds,
            'active_tasks': active_count,
            'queue_size': self.get_processing_queue_size(),
            'buffer_status': buffer_status,
        }
    
    def set_buffer_distance(self, seconds: float):
        """
        Change the buffer distance.
        
        Args:
            seconds: New buffer distance in seconds
        """
        old_value = self.buffer_seconds
        self.buffer_seconds = seconds
        logger.info(f"Buffer distance changed: {old_value}s -> {seconds}s")
    
    def set_max_concurrent(self, max_concurrent: int):
        """
        Change maximum concurrent processing tasks.
        
        Args:
            max_concurrent: New maximum concurrent tasks
        """
        old_value = self.max_concurrent
        self.max_concurrent = max_concurrent
        logger.info(f"Max concurrent tasks changed: {old_value} -> {max_concurrent}")
    
    def reset(self):
        """Reset buffer manager state."""
        self.current_playback_time = 0.0
        self.current_strategy = BufferStrategy.INITIAL
        
        # Clear queue
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except queue.Empty:
                break
        
        with self.task_lock:
            self.active_tasks.clear()
        
        logger.info("Buffer manager reset")
    
    def __del__(self):
        """Destructor to ensure clean shutdown."""
        self.stop_processing()
