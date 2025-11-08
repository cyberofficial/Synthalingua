"""
Video Transcription Manager Module

Manages the transcription and translation of video audio chunks.
Extends the existing sub_gen.py logic for video-specific processing.

Handles:
- Integration with existing Whisper models (BaseWhisper, FasterWhisper, OpenVINO)
- Chunk-based transcription for buffered processing
- Translation pipeline integration
- SRT timestamp generation
- Resource management for model loading
"""

import os
import logging
import threading
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import time

# Import existing Synthalingua modules
from modules.BaseWhisper import BaseWhisperModel
from modules.FasterWhisper import FasterWhisperModel
from modules.OpenVINOWhisper import OpenVINOWhisperModel
from modules import parser_args
from modules.device_manager import setup_device
from modules.languages import get_valid_languages

logger = logging.getLogger(__name__)


class VideoTranscriptionManager:
    """
    Manages transcription and translation for video chunks.
    
    Integrates with existing Synthalingua model infrastructure and provides
    chunk-based processing for buffered video transcription.
    """
    
    def __init__(self,
                 model_source: str = "fasterwhisper",
                 model_size: str = "base",
                 device: str = "auto",
                 compute_type: str = "float16",
                 source_language: Optional[str] = None,
                 target_language: str = "en",
                 enable_translation: bool = True,
                 model_dir: str = "./models"):
        """
        Initialize Video Transcription Manager.
        
        Args:
            model_source: Model source ("whisper", "fasterwhisper", "openvino")
            model_size: Model size ("tiny", "base", "small", "medium", "large-v2", "large-v3")
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Compute type for FasterWhisper/OpenVINO
            source_language: Source language code (None for auto-detect)
            target_language: Target language code for translation
            enable_translation: Whether to enable translation
            model_dir: Directory containing models
        """
        self.model_source = model_source.lower()
        self.model_size = model_size
        self.device = device if device != "auto" else self._auto_detect_device()
        self.compute_type = compute_type
        # Convert 'auto' to None for language auto-detection
        self.source_language = None if source_language in ('auto', '', None) else source_language
        self.target_language = target_language
        self.enable_translation = enable_translation
        self.model_dir = model_dir
        
        logger.info(f"VideoTranscriptionManager initialized: model={model_source}/{model_size}, "
                   f"device={self.device}, source_lang={self.source_language}, target_lang={target_language}")
        
        # Model instance
        self.model = None
        self.model_lock = threading.Lock()
        
        # Statistics
        self.chunks_processed = 0
        self.total_processing_time = 0.0
        
        # Initialize model
        self._load_model()
        
        logger.info(f"VideoTranscriptionManager initialized: "
                   f"source={model_source}, size={model_size}, device={self.device}")
    
    def _auto_detect_device(self) -> str:
        """Auto-detect best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except:
            pass
        return "cpu"
    
    def _load_model(self):
        """Load the Whisper model based on configuration."""
        try:
            with self.model_lock:
                logger.info(f"Loading {self.model_source} model: {self.model_size}")
                
                if self.model_source == "whisper":
                    self.model = BaseWhisperModel(
                        model=self.model_size,
                        device=self.device,
                        download_root=self.model_dir
                    )
                    logger.info("BaseWhisper model loaded successfully")
                    
                elif self.model_source == "fasterwhisper":
                    self.model = FasterWhisperModel(
                        model=self.model_size,
                        device=self.device,
                        download_root=self.model_dir,
                        compute_type=self.compute_type
                    )
                    logger.info("FasterWhisper model loaded successfully")
                    
                elif self.model_source == "openvino":
                    self.model = OpenVINOWhisperModel(
                        model=self.model_size,
                        device=self.device,
                        download_root=self.model_dir,
                        compute_type=self.compute_type
                    )
                    logger.info("OpenVINO model loaded successfully")
                    
                else:
                    raise ValueError(f"Unknown model source: {self.model_source}")
                    
        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise RuntimeError(f"Failed to load model: {e}")
    
    def detect_language(self, audio_path: str) -> Tuple[str, float]:
        """
        Detect language from audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            with self.model_lock:
                if not self.model:
                    raise RuntimeError("Model not loaded")
                
                language_probs = self.model.detect_language(audio_path)
                
                if not language_probs:
                    return ("unknown", 0.0)
                
                # Convert any tensor values to float (handles CUDA tensors)
                converted_probs = {}
                for lang, prob in language_probs.items():
                    # Handle tensor types (CUDA or CPU)
                    if hasattr(prob, 'cpu'):
                        prob = prob.cpu().item()  # Convert tensor to Python float
                    elif hasattr(prob, 'item'):
                        prob = prob.item()  # Convert numpy/tensor to Python float
                    converted_probs[lang] = float(prob)
                
                # Get language with highest probability
                best_lang = max(converted_probs.items(), key=lambda x: x[1])
                logger.debug(f"Language detection result: {best_lang[0]} ({best_lang[1]:.2%})")
                return best_lang
                
        except Exception as e:
            logger.error(f"Language detection failed: {e}", exc_info=True)
            return ("unknown", 0.0)
    
    def transcribe_chunk(self,
                        audio_path: str,
                        chunk_id: int,
                        language: Optional[str] = None) -> Dict:
        """
        Transcribe a single audio chunk.
        
        Args:
            audio_path: Path to audio file
            chunk_id: Chunk identifier
            language: Optional language code (will auto-detect if None)
            
        Returns:
            dict: Transcription result with:
                - chunk_id: Chunk identifier
                - transcription: Transcribed text
                - language: Detected/used language
                - language_confidence: Detection confidence
                - processing_time: Time taken in seconds
                - success: Whether transcription succeeded
                - error: Error message if failed
        """
        start_time = time.time()
        result = {
            'chunk_id': chunk_id,
            'transcription': '',
            'language': language or self.source_language or 'unknown',
            'language_confidence': 0.0,
            'processing_time': 0.0,
            'success': False,
            'error': None
        }
        
        try:
            # Detect language if not provided
            if not language and not self.source_language:
                detected_lang, confidence = self.detect_language(audio_path)
                # If detection failed, don't use 'unknown' - use None to trigger auto-detect in model
                if detected_lang != "unknown":
                    result['language'] = detected_lang
                    result['language_confidence'] = confidence
                    logger.debug(f"Detected language for chunk {chunk_id}: "
                               f"{detected_lang} ({confidence:.2%})")
                else:
                    # Detection failed, let the model auto-detect
                    result['language'] = None
                    logger.warning(f"Language detection failed for chunk {chunk_id}, using model auto-detect")
            else:
                result['language'] = language or self.source_language
                logger.debug(f"Using specified language for chunk {chunk_id}: {result['language']}")
            
            # Transcribe
            logger.info(f"🎤 Transcribing audio chunk {chunk_id} ({result['language']})...")
            with self.model_lock:
                if not self.model:
                    raise RuntimeError("Model not loaded")
                
                transcription = self.model.transcribe(
                    file_path=audio_path,
                    language=result['language'],
                    task="transcribe",
                    condition_on_previous_text=False
                )
            
            result['transcription'] = transcription.strip()
            result['success'] = True
            
            # Update statistics
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            self.chunks_processed += 1
            self.total_processing_time += processing_time
            
            logger.debug(f"Chunk {chunk_id} transcribed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to transcribe chunk {chunk_id}: {e}", exc_info=True)
        
        return result
    
    def translate_text(self, text: str, source_lang: str) -> str:
        """
        Translate transcribed text to target language.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            str: Translated text
        """
        if not self.enable_translation:
            return ""
        
        # If source and target are the same, no translation needed
        if source_lang == self.target_language:
            return text
        
        logger.info(f"🌐 Translating text from {source_lang} to {self.target_language}...")
        try:
            # For now, use Whisper's built-in translation (X -> English)
            # Future: integrate with external translation APIs for more languages
            if self.target_language == "en":
                with self.model_lock:
                    if not self.model:
                        raise RuntimeError("Model not loaded")
                    
                    # Whisper models have built-in translation to English
                    # This would require re-processing with task="translate"
                    # For efficiency, we might want to do this in one pass
                    logger.debug(f"Translation to English (built-in)")
                    return text  # Placeholder - need to implement proper translation
            else:
                logger.warning(f"Translation to {self.target_language} not yet implemented")
                return text
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return ""
    
    def process_chunk(self,
                     audio_path: str,
                     chunk_id: int,
                     start_time: float,
                     end_time: float) -> Dict:
        """
        Process a complete chunk: transcribe and optionally translate.
        
        Args:
            audio_path: Path to chunk audio file
            chunk_id: Chunk identifier
            start_time: Chunk start time in video
            end_time: Chunk end time in video
            
        Returns:
            dict: Complete processing result
        """
        result = {
            'chunk_id': chunk_id,
            'start_time': start_time,
            'end_time': end_time,
            'transcription': '',
            'translation': '',
            'language': 'unknown',
            'success': False,
            'error': None,
            'timestamps': []
        }
        
        try:
            # Transcribe
            transcription_result = self.transcribe_chunk(audio_path, chunk_id)
            
            if not transcription_result['success']:
                result['error'] = transcription_result['error']
                return result
            
            result['transcription'] = transcription_result['transcription']
            result['language'] = transcription_result['language']
            
            # Translate if enabled
            if self.enable_translation and result['transcription']:
                translation = self.translate_text(
                    result['transcription'],
                    result['language']
                )
                result['translation'] = translation
            
            # Generate basic timestamp (whole chunk as one caption)
            result['timestamps'] = [{
                'start': start_time,
                'end': end_time,
                'text': result['transcription']
            }]
            
            result['success'] = True
            logger.info(f"Chunk {chunk_id} processed successfully")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to process chunk {chunk_id}: {e}", exc_info=True)
        
        return result
    
    def get_statistics(self) -> Dict:
        """
        Get processing statistics.
        
        Returns:
            dict: Statistics including chunks processed, average time, etc.
        """
        avg_time = (self.total_processing_time / self.chunks_processed 
                   if self.chunks_processed > 0 else 0)
        
        return {
            'chunks_processed': self.chunks_processed,
            'total_processing_time': round(self.total_processing_time, 2),
            'average_processing_time': round(avg_time, 2),
            'model_source': self.model_source,
            'model_size': self.model_size,
            'device': self.device,
        }
    
    def change_model(self, 
                    model_source: Optional[str] = None,
                    model_size: Optional[str] = None):
        """
        Change the model configuration.
        
        Args:
            model_source: New model source (optional)
            model_size: New model size (optional)
        """
        if model_source:
            self.model_source = model_source.lower()
        if model_size:
            self.model_size = model_size
        
        logger.info(f"Changing model to: {self.model_source} / {self.model_size}")
        self._load_model()
    
    def unload_model(self):
        """Unload the model to free resources."""
        with self.model_lock:
            self.model = None
            logger.info("Model unloaded")
    
    def __del__(self):
        """Destructor to ensure model cleanup."""
        self.unload_model()
