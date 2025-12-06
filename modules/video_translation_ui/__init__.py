"""
Video Translation UI Module

This module provides real-time video translation and transcription capabilities
through a web-based interface. It extends Synthalingua's existing caption generation
into an interactive video playback experience.

Key Features:
- HTML5 video player with live caption overlay
- Support for multiple video formats (MP4, MKV, AVI, MOV, WebM)
- Real-time transcription and translation
- Buffered processing strategy (30s/60s/120s)
- Multiple Whisper model sources (BaseWhisper, FasterWhisper, OpenVINO)
- Customizable caption styling
- Export captions as SRT/VTT

Components:
- video_processor: Video/audio extraction and metadata handling
- chunk_manager: Audio segment management for buffered processing
- buffer_manager: Buffering strategy and processing queue
- video_transcription: Video-specific transcription extending sub_gen.py
- video_backend: Flask backend for video UI
- Caption overlay rendering and synchronization

Author: cyberofficial
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "cyberofficial"

from .video_processor import VideoProcessor
from .chunk_manager import ChunkManager
from .buffer_manager import BufferManager
from .video_transcription import VideoTranscriptionManager

__all__ = [
    "VideoProcessor",
    "ChunkManager",
    "BufferManager",
    "VideoTranscriptionManager",
]
