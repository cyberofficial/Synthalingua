"""
Video Transcription Manager Module

Manages the transcription and translation of video audio chunks.
Extends the existing sub_gen.py logic for video-specific processing.

Handles:
- Integration with existing Whisper models (BaseWhisper, FasterWhisper, OpenVINO)
- Chunk-based transcription for buffered processing
- Silence detection and speech region processing
- Translation pipeline integration
- SRT timestamp generation with accurate phrase-level timing
- Resource management for model loading
"""

import os
import logging
import threading
from typing import Optional, Dict, List, Tuple, Callable
from pathlib import Path
import time
import tempfile

# Import existing Synthalingua modules
from modules.BaseWhisper import BaseWhisperModel
from modules.FasterWhisper import FasterWhisperModel
from modules.OpenVINOWhisper import OpenVINOWhisperModel
from modules import parser_args
from modules.device_manager import setup_device
from modules.languages import get_valid_languages

# Import silence detection
from modules.video_translation_ui.silence_detector import SilenceDetector

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
                 enable_silence_detection: bool = True,
                 silence_threshold_db: float = -35.0,
                 min_silence_duration: float = 0.5,
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
            enable_silence_detection: Whether to detect and skip silence
            silence_threshold_db: dB threshold for silence detection
            min_silence_duration: Minimum silence duration in seconds
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
        self.enable_silence_detection = enable_silence_detection
        self.model_dir = model_dir
        
        logger.info(f"VideoTranscriptionManager initialized: model={model_source}/{model_size}, "
                   f"device={self.device}, source_lang={self.source_language}, target_lang={target_language}, "
                   f"silence_detection={enable_silence_detection}")
        
        # Silence detector
        if self.enable_silence_detection:
            self.silence_detector = SilenceDetector(
                silence_threshold_db=silence_threshold_db,
                min_silence_duration=min_silence_duration,
                min_speech_duration=0.1
            )
        else:
            self.silence_detector = None
        
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
                    condition_on_previous_text=False,
                    # Disable temperature fallback to speed up processing
                    # This prevents retries when compression ratio is high (repetitive/noisy audio)
                    temperature=0.0,  # Single temperature, no fallback
                    compression_ratio_threshold=None,  # Disable compression ratio check
                    log_prob_threshold=None,  # Disable log probability check
                    no_speech_threshold=0.6  # Keep reasonable no-speech detection
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
    
    def translate_text(self, text: str, source_lang: str, audio_path: Optional[str] = None) -> str:
        """
        Translate transcribed text to target language.
        
        For translation to English, uses Whisper's built-in translation capability
        which requires re-processing the audio with task="translate".
        
        Args:
            text: Text to translate (used if audio_path not provided)
            source_lang: Source language code
            audio_path: Optional path to audio file for Whisper translation
            
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
            # For translation to English, use Whisper's built-in translation
            if self.target_language == "en":
                with self.model_lock:
                    if not self.model:
                        raise RuntimeError("Model not loaded")
                    
                    # If audio path provided, use Whisper's translate task
                    if audio_path and os.path.exists(audio_path):
                        logger.debug(f"Using Whisper translate task on audio")
                        
                        # Use Whisper model directly with task="translate"
                        # Note: transcribe_chunk doesn't support task parameter,
                        # so we call the model directly
                        transcription = self.model.transcribe(
                            file_path=audio_path,
                            language=source_lang,
                            task="translate",  # Translate to English
                            condition_on_previous_text=False,
                            # Disable temperature fallback for faster processing
                            temperature=0.0,
                            compression_ratio_threshold=None,
                            log_prob_threshold=None,
                            no_speech_threshold=0.6
                        )
                        
                        if transcription and transcription.strip():
                            translated = transcription.strip()
                            logger.debug(f"Translation successful: '{translated[:80]}'")
                            return translated
                        else:
                            logger.warning(f"Translation task failed, returning original text")
                            return text
                    else:
                        # No audio available - cannot translate without re-processing
                        # This is a limitation of Whisper's translate feature
                        logger.warning(f"No audio path provided for translation, returning original text")
                        return text
            else:
                logger.warning(f"Translation to {self.target_language} not yet implemented")
                return text
                
        except Exception as e:
            logger.error(f"Translation failed: {e}", exc_info=True)
            return text  # Return original text on error
    
    def process_chunk(self,
                     audio_path: str,
                     chunk_id: int,
                     start_time: float,
                     end_time: float,
                     on_segment_complete: Optional[Callable] = None) -> Dict:
        """
        Process a complete chunk: transcribe and optionally translate.
        
        If silence detection is enabled, only processes speech regions within the chunk,
        providing accurate phrase-level timestamps instead of single chunk-level captions.
        
        Args:
            audio_path: Path to chunk audio file
            chunk_id: Chunk identifier
            start_time: Chunk start time in video
            end_time: Chunk end time in video
            on_segment_complete: Optional callback(timestamp_dict) called after each segment
            
        Returns:
            dict: Complete processing result with:
                - chunk_id: Chunk identifier
                - start_time: Chunk start in video
                - end_time: Chunk end in video
                - transcription: Full transcription text
                - translation: Full translation text (if enabled)
                - language: Detected/used language
                - success: Whether processing succeeded
                - error: Error message if failed
                - timestamps: List of caption segments with accurate timing:
                    [{'start': 10.5, 'end': 13.2, 'text': 'Hello world', 'translation': 'Hola mundo'}, ...]
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
            # Check if silence detection is enabled
            if self.enable_silence_detection and self.silence_detector:
                # Process with silence detection for accurate phrase-level timing
                logger.info(f"🔍 Detecting speech regions in chunk {chunk_id}...")
                result = self._process_chunk_with_silence_detection(
                    audio_path, chunk_id, start_time, end_time, on_segment_complete
                )
            else:
                # Process entire chunk as one caption (original behavior)
                logger.info(f"🎤 Transcribing entire chunk {chunk_id} (no silence detection)...")
                result = self._process_chunk_without_silence_detection(
                    audio_path, chunk_id, start_time, end_time
                )
            
            if result['success']:
                logger.info(f"✅ Chunk {chunk_id} processed successfully "
                          f"({len(result['timestamps'])} caption segments)")
            else:
                logger.error(f"❌ Chunk {chunk_id} processing failed: {result['error']}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to process chunk {chunk_id}: {e}", exc_info=True)
        
        return result
    
    def _process_chunk_without_silence_detection(self,
                                                 audio_path: str,
                                                 chunk_id: int,
                                                 start_time: float,
                                                 end_time: float) -> Dict:
        """
        Process chunk without silence detection (original behavior).
        Creates a single caption for the entire chunk.
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
        
        # Transcribe entire chunk
        transcription_result = self.transcribe_chunk(audio_path, chunk_id)
        
        if not transcription_result['success']:
            result['error'] = transcription_result['error']
            return result
        
        result['transcription'] = transcription_result['transcription']
        result['language'] = transcription_result['language']
        
        # Translate if enabled - pass audio path for Whisper translation
        if self.enable_translation and result['transcription']:
            translation = self.translate_text(
                result['transcription'],
                result['language'],
                audio_path=audio_path  # Pass audio for Whisper translate task
            )
            result['translation'] = translation
        
        # Generate basic timestamp (whole chunk as one caption)
        if result['transcription']:
            result['timestamps'] = [{
                'start': start_time,
                'end': end_time,
                'text': result['transcription'],
                'translation': result['translation']
            }]
        
        result['success'] = True
        return result
    
    def _process_chunk_with_silence_detection(self,
                                              audio_path: str,
                                              chunk_id: int,
                                              start_time: float,
                                              end_time: float,
                                              on_segment_complete: Optional[Callable] = None) -> Dict:
        """
        Process chunk with silence detection for accurate phrase-level timing.
        Only transcribes speech regions, skipping silence for efficiency.
        
        Args:
            on_segment_complete: Optional callback(timestamp_dict) called after each segment is processed
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
            # Detect speech regions in this chunk
            if not self.silence_detector:
                logger.error("Silence detector not initialized")
                result['error'] = "Silence detector not initialized"
                return result
            
            regions = self.silence_detector.detect_regions(audio_path)
            speech_regions = [r for r in regions if r['type'] == 'speech']
            
            if not speech_regions:
                logger.debug(f"No speech detected in chunk {chunk_id}")
                result['success'] = True
                result['language'] = self.source_language or 'unknown'
                return result
            
            logger.debug(f"Found {len(speech_regions)} speech regions in chunk {chunk_id}")
            
            # Process each speech region
            all_transcriptions = []
            all_translations = []
            detected_language = None
            
            for i, region in enumerate(speech_regions):
                region_start = region['start']
                region_end = region['end']
                
                # Create temporary file for this speech region
                region_audio_path = None
                try:
                    # Extract speech region to temporary file
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                        region_audio_path = tmp_file.name
                    
                    if not self.silence_detector:
                        logger.error("Silence detector not initialized")
                        continue
                    
                    success = self.silence_detector.extract_speech_region(
                        audio_path,
                        region_audio_path,
                        region_start,
                        region_end
                    )
                    
                    if not success:
                        logger.warning(f"Failed to extract speech region {i} from chunk {chunk_id}")
                        continue
                    
                    # Transcribe this speech region
                    # Note: Using chunk_id directly since transcribe_chunk expects int
                    # The region index is tracked separately in logs
                    transcription_result = self.transcribe_chunk(
                        region_audio_path,
                        chunk_id  # Use parent chunk_id for consistency
                    )
                    
                    if not transcription_result['success']:
                        logger.warning(f"Failed to transcribe speech region {i} in chunk {chunk_id}")
                        continue
                    
                    transcription_text = transcription_result['transcription'].strip()
                    if not transcription_text:
                        continue
                    
                    # Store detected language (use first detected language for consistency)
                    if detected_language is None:
                        detected_language = transcription_result['language']
                    
                    all_transcriptions.append(transcription_text)
                    
                    # Translate if enabled - pass audio path for Whisper translation
                    translation_text = ""
                    if self.enable_translation:
                        translation_text = self.translate_text(
                            transcription_text,
                            transcription_result['language'],
                            audio_path=region_audio_path  # Pass audio for Whisper translate task
                        )
                        all_translations.append(translation_text)
                        logger.debug(f"  Original ({transcription_result['language']}): '{transcription_text[:80]}'")
                        logger.debug(f"  Translated ({self.target_language}): '{translation_text[:80]}'")
                    
                    # Calculate absolute timestamps (relative to video start)
                    absolute_start = start_time + region_start
                    absolute_end = start_time + region_end
                    
                    # Add to timestamps
                    timestamp_dict = {
                        'start': absolute_start,
                        'end': absolute_end,
                        'text': transcription_text,
                        'translation': translation_text
                    }
                    result['timestamps'].append(timestamp_dict)
                    
                    # Call callback to update chunk incrementally (so captions show in real-time)
                    if on_segment_complete:
                        try:
                            # Pass segment number and total for progress tracking
                            on_segment_complete(timestamp_dict, i + 1, len(speech_regions))
                        except Exception as e:
                            logger.warning(f"Segment complete callback failed: {e}")
                    
                    logger.debug(f"Speech region {i+1}/{len(speech_regions)} in chunk {chunk_id}: "
                               f"{absolute_start:.2f}s - {absolute_end:.2f}s")
                    
                finally:
                    # Clean up temporary region file
                    if region_audio_path and os.path.exists(region_audio_path):
                        try:
                            os.remove(region_audio_path)
                        except:
                            pass
            
            # Combine all transcriptions and translations
            result['transcription'] = ' '.join(all_transcriptions)
            result['translation'] = ' '.join(all_translations) if all_translations else ''
            result['language'] = detected_language or self.source_language or 'unknown'
            result['success'] = True
            
            logger.info(f"Processed {len(result['timestamps'])} speech segments in chunk {chunk_id}")
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
            logger.error(f"Failed to process chunk {chunk_id} with silence detection: {e}", exc_info=True)
        
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
