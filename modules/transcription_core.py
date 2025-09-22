from __future__ import annotations
import io
import re
import shutil
import threading
import os
from datetime import datetime, timedelta
from queue import Queue, Empty
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Optional, Dict, List, Tuple, Any
import traceback # Keep this for error logging

import whisper
import torch
import speech_recognition as sr
from colorama import Fore, Style

from modules.console_settings import set_window_title
from modules import api_backend
from modules.languages import get_valid_languages
from collections import deque
from modules.similarity_utils import is_similar
try:
    from modules.stream_transcription_module import add_phrase_to_blocklist, is_phrase_in_blocklist
except ImportError:
    def add_phrase_to_blocklist(phrase, blocklist_path) -> bool:
        return False
    def is_phrase_in_blocklist(phrase, blocklist_path) -> bool:
        return False

class TranscriptionCore:
    def __init__(self, args: Any, device, audio_model, blacklist: List[str], temp_dir: str) -> None:
        self.args = args
        self.device = device
        self.audio_model = audio_model
        self.blacklist = blacklist
        self.temp_dir = temp_dir
        self.transcription: List[Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]] = []
        self.phrase_time: Optional[datetime] = None
        self.last_sample: bytes = bytes()
        self.detected_language: Optional[str] = None
        self.original_text: Optional[str] = None
        self.translated_text: Optional[str] = None
        self.transcribed_text: Optional[str] = None
        self._blocked_phrase_history = {
            'original': deque(maxlen=10),
            'translation': deque(maxlen=10),
            'target': deque(maxlen=10),
        }
        self._last_output = {
            'original': None,
            'translation': None,
            'target': None,
        }
        self._DEBUG_BLOCK_SIMILAR = True # Keep this for blocking debugs if desired
        self._ENABLE_SIMILAR_PROTECTION = getattr(self.args, 'condition_on_previous_text', False)
        self._AUTO_BLOCKLIST_ENABLED = getattr(self.args, 'auto_blocklist', False)
        self._BLOCKLIST_PATH = getattr(self.args, 'ignorelist', None)
        
        self._audio_file_queue = Queue()
        self._processing_thread = None
        self._stop_processing = threading.Event()
        self._queue_active = False
        
        # Padded audio support for microphone
        self._padded_audio_count = getattr(self.args, 'paddedaudio', 0)
        self._mic_chunk_size = getattr(self.args, 'mic_chunk_size', 1)  # Default to 1 if not set
        self._accumulated_audio_files = []
        self._previous_batch_files = []

    def start_queue_processing(self):
        if not self._queue_active:
            self._queue_active = True
            self._stop_processing.clear()
            self._processing_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._processing_thread.start()
            if not self.args.no_log:
                print(" Audio processing queue started")

    def stop_queue_processing(self):
        if self._queue_active:
            self._queue_active = False
            self._stop_processing.set()
            if self._processing_thread and self._processing_thread.is_alive():
                try:
                    self._audio_file_queue.put(None, timeout=0.1) 
                except Exception:
                    pass
                self._processing_thread.join(timeout=5)
            
            while not self._audio_file_queue.empty():
                try:
                    temp_file = self._audio_file_queue.get_nowait()
                    if temp_file and os.path.exists(temp_file):
                        os.remove(temp_file)
                except Empty:
                    break
                except Exception as e:
                    if not self.args.no_log:
                        print(f" Warning: Error clearing queue item: {e}")
            if not self.args.no_log:
                print(" Audio processing queue stopped")

    def _process_queue(self):
        while not self._stop_processing.is_set():
            try:
                temp_file = self._audio_file_queue.get(timeout=1.0)
                
                if temp_file is None:
                    break

                if os.path.exists(temp_file):
                    # Add file to accumulated batch
                    self._accumulated_audio_files.append(temp_file)
                    
                    # Check if we should process the batch
                    if self._should_process_batch():
                        self._process_audio_batch()
                        
                self._audio_file_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                if not self.args.no_log:
                    print(f" Queue processing error: {e}")
                    traceback.print_exc()

    def _should_process_batch(self) -> bool:
        """Check if we have enough audio files to process a batch"""
        if self._padded_audio_count > 0:
            # With padded audio, wait for mic_chunk_size files
            return len(self._accumulated_audio_files) >= self._mic_chunk_size
        else:
            # Without padded audio, process each file immediately
            return len(self._accumulated_audio_files) >= 1

    def _process_audio_batch(self):
        """Process a batch of audio files with optional padding"""
        try:
            if not self._accumulated_audio_files:
                return

            if not self.args.no_log:
                queue_size = self._audio_file_queue.qsize()
                if self._padded_audio_count > 0:
                    print(f" Processing audio batch: {len(self._accumulated_audio_files)} files + {len(self._previous_batch_files)} padded (Queue: {queue_size} pending)")
                else:
                    print(f" Processing audio file (Queue: {queue_size} pending)")

            # Prepare files for combination including padding
            files_to_combine = []
            files_to_keep = []
            
            # Add previous batch files for padding if enabled
            if self._padded_audio_count > 0 and self._previous_batch_files:
                padding_files = self._previous_batch_files[-self._padded_audio_count:]
                files_to_combine.extend(padding_files)
                files_to_keep.extend(padding_files)  # Keep padding files for reuse
                if self.args.debug:
                    print(f" [DEBUG] Adding {len(padding_files)} padded audio files from previous batch")

            # Store current batch for next iteration's padding BEFORE combining/deleting
            if self._padded_audio_count > 0:
                self._previous_batch_files = self._accumulated_audio_files.copy()
                # Also keep the last few files from current batch for next iteration
                padding_files_to_keep = self._accumulated_audio_files[-self._padded_audio_count:]
                files_to_keep.extend(padding_files_to_keep)

            # Add current batch files
            files_to_combine.extend(self._accumulated_audio_files)
            
            # Combine audio files if needed
            if len(files_to_combine) > 1:
                combined_file = self._combine_audio_files(files_to_combine, files_to_keep)
                if combined_file:
                    self._process_single_file(combined_file)
                    # Clean up combined file
                    if os.path.exists(combined_file):
                        os.remove(combined_file)
                else:
                    # Fallback to processing first file if combination fails
                    self._process_single_file(files_to_combine[0])
            else:
                # Process single file
                self._process_single_file(files_to_combine[0])
            
            # Clean up processed files (except those in keep list)
            for file_path in self._accumulated_audio_files:
                if file_path not in files_to_keep:
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        if not self.args.no_log:
                            print(f" Warning: Could not delete temp file {file_path}: {e}")

            # Clear accumulated files
            self._accumulated_audio_files = []
            
        except Exception as e:
            if not self.args.no_log:
                print(f" Error processing audio batch: {e}")
                traceback.print_exc()

    def _combine_audio_files(self, file_paths: List[str], keep_files: List[str]) -> Optional[str]:
        """Combine multiple audio files into a single file"""
        try:
            from tempfile import NamedTemporaryFile
            
            combined_file = NamedTemporaryFile(
                dir=self.temp_dir,
                delete=False,
                suffix=".wav",
                prefix="combined_"
            ).name
            
            # Use ffmpeg to concatenate the audio files
            import subprocess
            
            # Create a temporary file list for ffmpeg
            file_list_path = NamedTemporaryFile(mode='w', delete=False, suffix=".txt").name
            
            try:
                with open(file_list_path, 'w') as f:
                    for file_path in file_paths:
                        if os.path.exists(file_path):
                            f.write(f"file '{file_path}'\n")
                
                # Combine files using ffmpeg
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", file_list_path,
                    "-c", "copy", combined_file
                ]
                
                subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
                
                if os.path.exists(combined_file):
                    return combined_file
                    
            finally:
                # Clean up temporary file list
                if os.path.exists(file_list_path):
                    os.remove(file_list_path)
                    
        except Exception as e:
            if not self.args.no_log:
                print(f" Error combining audio files: {e}")
            
        return None

    def _process_single_file(self, temp_file: str):
        """Process a single audio file"""
        try:
            self.original_text = None
            self.translated_text = None
            self.transcribed_text = None
            self.detected_language = None

            self._perform_transcription(temp_file)
            
            if self.args.translate and self.original_text:
                self._perform_translation(temp_file)
            if self.args.transcribe and self.original_text:
                self._perform_transcription_to_target(temp_file)
            
            self._display_results()
            self._update_api_headers()  # Update web server with transcription results
            
            self.transcription.append((
                self.original_text, 
                self.translated_text if self.args.translate else None,
                self.transcribed_text if self.args.transcribe else None,
                self.detected_language
            ))
            
        except Exception as e:
            if not self.args.no_log:
                print(f" Error processing audio file {temp_file}: {e}")
                traceback.print_exc()
    
    def process_audio(self, data_queue: Queue, source: Optional[sr.AudioSource]) -> bool:
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                if not self.args.no_log:
                    queue_size = self._audio_file_queue.qsize()
                    print(f"\n Audio stream detected... (Queue: {queue_size} pending)")
                
                self._handle_phrase_timeout(now)
                self._collect_audio_data(data_queue)
                
                temp_file = NamedTemporaryFile(
                    dir=self.temp_dir, 
                    delete=False,
                    suffix=".wav", 
                    prefix="rec_"
                ).name
                
                try:
                    if source is not None:
                        audio_data = self._prepare_audio_data(source)
                        self._save_audio_data(audio_data, temp_file)
                    else:
                        with open(temp_file, 'wb') as f:
                            f.write(self.last_sample)
                    
                    self._audio_file_queue.put(temp_file)
                    
                except Exception as e:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    if not self.args.no_log:
                        print(f" Error saving audio data: {e}")
                        traceback.print_exc()

            sleep(0.1)
            return True
            
        except Exception as e:
            if not self.args.no_log:
                print(f" Error in process_audio: {str(e)}")
                traceback.print_exc()
            return False

    def _handle_phrase_timeout(self, now: datetime) -> bool:
        if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.args.phrase_timeout):
            self.last_sample = bytes()
            return True
        self.phrase_time = now
        return False

    def _collect_audio_data(self, data_queue: Queue) -> None:
        while not data_queue.empty():
            data = data_queue.get()
            self.last_sample += data

    def _prepare_audio_data(self, source: sr.AudioSource) -> sr.AudioData:
        try:
            sample_rate = getattr(source, 'SAMPLE_RATE', 16000)
            sample_width = getattr(source, 'SAMPLE_WIDTH', 2)
            return sr.AudioData(self.last_sample, sample_rate, sample_width)
        except Exception as e:
            if not self.args.no_log:
                print(f"Error preparing audio data: {e}")
            return sr.AudioData(self.last_sample, 16000, 2)

    def _save_audio_data(self, audio_data: sr.AudioData, temp_file: str) -> None:
        with io.BytesIO(audio_data.get_wav_data()) as wav_data:
            with open(temp_file, 'w+b') as f:
                shutil.copyfileobj(wav_data, f)

    def _perform_transcription(self, temp_file: str) -> None:
        self._detect_language(temp_file)
        if self.args.language:
            self.detected_language = self.args.language
        
        result = self._transcribe_audio(temp_file)
        if result and 'text' in result:
            self.original_text = result['text'].strip()
        else:
            self.original_text = ""

    def _detect_language(self, temp_file: str) -> None:
        if ".en" in self.args.model:
            self.detected_language = "en"
        elif hasattr(self.args, 'stream_language') and self.args.stream_language:
            self.detected_language = self.args.stream_language
        elif self.args.language:
            self.detected_language = self.args.language
        else:
            if not self.args.no_log:
                print(f"Detecting Language...")
            try:
                language_probs = self.audio_model.detect_language(temp_file)
                if isinstance(language_probs, dict) and language_probs:
                    self.detected_language = max(language_probs.items(), key=lambda x: x[1])[0]
                    self._update_language_confidence(language_probs)
                else:
                    self.detected_language = None
            except Exception as e:
                if not self.args.no_log:
                    print(f"Error detecting language: {e}")
                self.detected_language = None

    def _update_language_confidence(self, language_probs: Dict[str, float]) -> None:
        try:
            if self.detected_language and self.detected_language in language_probs:
                confidence = language_probs[self.detected_language] * 100
                confidence_color = (Fore.GREEN if confidence > 75
                                   else (Fore.YELLOW if confidence > 50 else Fore.RED))
                if hasattr(self, 'args') and hasattr(self.args, 'model'):
                    set_window_title(self.detected_language, confidence, self.args.model)
                if not self.args.no_log:
                    print(f"Detected language: {self.detected_language} "
                          f"{confidence_color}({confidence:.2f}% Accuracy){Style.RESET_ALL}")
        except KeyError:
            if not self.args.no_log:
                print(f"Warning: Could not determine confidence for language {self.detected_language}")
        except Exception as e:
            if not self.args.no_log:
                print(f"Error updating language confidence: {str(e)}")

    def _transcribe_audio(self, temp_file: str) -> Dict[str, Any]:
        dtype = torch.float16 if self.args.fp16 else torch.float32
        # Conveniently ignores case if device is of type string, though a more explicit check might be better
        if self.device == torch.device("cpu"):
            if torch.cuda.is_available(): print("Warning: Performing inference on CPU when CUDA is available")
            if dtype == torch.float16:
                print("Warning: FP16 is not supported on CPU; using FP32 instead")
                dtype = torch.float32

        language_to_use = self.args.language if self.args.language else self.detected_language
        if not language_to_use:
            effective_language = None
        else:
            effective_language = language_to_use

        kwargs = {
            'language': effective_language,
            'condition_on_previous_text': self.args.condition_on_previous_text,
            'fp16': dtype == torch.float16,
            'task': 'transcribe'
        }
            
        result = self.audio_model.transcribe(temp_file, **kwargs)
        
        # Handle both string and dictionary return types from different model implementations
        if isinstance(result, str):
            # For models that return strings directly (FasterWhisper, OpenVINO, etc.)
            result_dict = {'text': result}
            text_content = result
        else:
            # For models that return dictionaries (BaseWhisper via whisper library)
            result_dict = result
            text_content = result.get('text', '')
        
        if not self.args.no_log:
            print(f"Detected Speech: {text_content}")
            
        if not text_content and self.args.retry:
            if not self.args.no_log: print("Transcription failed, trying again...")
            retry_result = self.audio_model.transcribe(temp_file, **kwargs)
            
            # Handle retry result type as well
            if isinstance(retry_result, str):
                result_dict = {'text': retry_result}
                text_content = retry_result
            else:
                result_dict = retry_result
                text_content = retry_result.get('text', '')
                
            if not self.args.no_log: print(f"Detected Speech (retry): {text_content}")
                
        return result_dict

    def _perform_translation(self, temp_file: str) -> None:
        self.translated_text = "" 
        source_lang_for_translate = self.detected_language
        
        if source_lang_for_translate and source_lang_for_translate.lower() == 'en':
            if not self.args.no_log:
                print(f"Skipping translation because detected source language is English ('{source_lang_for_translate}').")
            self.translated_text = self.original_text
            return

        if not self.args.no_log:
            print(f"Translating from {source_lang_for_translate or 'unknown'} to English...")
        
        dtype = torch.float16 if self.args.fp16 else torch.float32
        # Conveniently ignores case if device is of type string, though a more explicit check might be better
        if self.device == torch.device("cpu"):
            if torch.cuda.is_available(): print("Warning: Performing inference on CPU when CUDA is available")
            if dtype == torch.float16:
                print("Warning: FP16 is not supported on CPU; using FP32 instead"); dtype = torch.float32

        kwargs = {
            'task': 'translate',
            'language': "English", 
            'condition_on_previous_text': self.args.condition_on_previous_text,
            'fp16': dtype == torch.float16
        }
                
        try:
            translated_result = self.audio_model.transcribe(temp_file, **kwargs)

            # Handle both string and dictionary return types
            if isinstance(translated_result, str):
                self.translated_text = translated_result.strip()
            elif isinstance(translated_result, dict) and 'text' in translated_result:
                self.translated_text = str(translated_result['text']).strip()
            
            if not self.translated_text and self.args.retry:
                if not self.args.no_log: print("Translation failed or produced empty text, trying again...")
                translated_result_retry = self.audio_model.transcribe(temp_file, **kwargs) 
                
                # Handle retry result type as well
                if isinstance(translated_result_retry, str):
                    self.translated_text = translated_result_retry.strip()
                elif isinstance(translated_result_retry, dict) and 'text' in translated_result_retry:
                    self.translated_text = str(translated_result_retry['text']).strip()
                             
        except Exception as e:
            if not self.args.no_log:
                print(f" Error during translation model call: {e}")
                traceback.print_exc()

    def _perform_transcription_to_target(self, temp_file: str) -> None:
        self.transcribed_text = ""
        target_lang = self.args.target_language
        if not target_lang:
            return

        if not self.args.no_log:
            print(f"Transcribing to {target_lang}...")
            
        dtype = torch.float16 if self.args.fp16 else torch.float32
        # Conveniently ignores case if device is of type string, though a more explicit check might be better
        if self.device == torch.device("cpu"):
            if torch.cuda.is_available(): print("Warning: Performing inference on CPU when CUDA is available")
            if dtype == torch.float16:
                print("Warning: FP16 is not supported on CPU; using FP32 instead"); dtype = torch.float32

        try:
            kwargs = {
                'task': 'transcribe', 
                'language': target_lang,
                'condition_on_previous_text': self.args.condition_on_previous_text,
                'fp16': dtype == torch.float16
            }
                
            transcribed_result = self.audio_model.transcribe(temp_file, **kwargs)
            if isinstance(transcribed_result, dict) and 'text' in transcribed_result:
                self.transcribed_text = str(transcribed_result['text']).strip()
            
            if not self.transcribed_text and self.args.retry:
                if not self.args.no_log: print("Transcribe failed, trying again...")
                transcribed_result_retry = self.audio_model.transcribe(temp_file, **kwargs)
                if isinstance(transcribed_result_retry, dict) and 'text' in transcribed_result_retry:
                    self.transcribed_text = str(transcribed_result_retry['text']).strip()
        except Exception as e:
            if not self.args.no_log:
                print(f" Error in transcription: {e}")
                traceback.print_exc()

    def _update_api_headers(self) -> None:
        if self.args.portnumber:
            self._update_filtered_headers()

    def _update_filtered_headers(self) -> None:
        try:
            if self.original_text is not None:
                filtered_header_text = self._filter_text(self.original_text)
                api_backend.update_header(filtered_header_text)
            
            if self.translated_text is not None:
                filtered_translated_text = self._filter_text(self.translated_text)
                api_backend.update_translated_header(filtered_translated_text)
                
            if self.transcribed_text is not None:
                filtered_transcribed_text = self._filter_text(self.transcribed_text)
                api_backend.update_transcribed_header(filtered_transcribed_text)
        except Exception as e:
            if not self.args.no_log:
                print(f"Warning: Failed to update API headers: {str(e)}")

    def _filter_text(self, text: Optional[str]) -> str:
        if text is None:
            return ""
        text_to_filter = str(text)
        filtered_text = text_to_filter.lower()
        for phrase in self.blacklist:
            if phrase:
                filtered_text = re.sub(rf"\b{re.escape(phrase.lower())}\b", "", filtered_text).strip()
        return filtered_text

    def _display_results(self) -> None:
        if self.original_text is None or not self.original_text.strip():
            return

        filtered_text = self._filter_text(self.original_text)
        
        if filtered_text or (self.args.translate and self.translated_text) or \
           (self.args.transcribe and self.transcribed_text):
            if not self.args.no_log:
                self._display_full_results(filtered_text)
            else:
                self._display_simple_results(filtered_text)

    def _display_full_results(self, filtered_original_text: str) -> None:
        has_original = filtered_original_text and not self._should_block_output(filtered_original_text, 'original')
        
        has_translation = False
        filtered_translated = ""
        if self.args.translate and self.translated_text:
            filtered_translated = self._filter_text(self.translated_text)
            if filtered_translated and not self._should_block_output(filtered_translated, 'translation'):
                has_translation = True
        
        has_target_transcription = False
        filtered_transcribed = ""
        if self.args.transcribe and self.transcribed_text:
            filtered_transcribed = self._filter_text(self.transcribed_text)
            if filtered_transcribed and not self._should_block_output(filtered_transcribed, 'target'):
                has_target_transcription = True

        if not (has_original or has_translation or has_target_transcription):
            return

        print("=" * shutil.get_terminal_size().columns)
        
        if has_original:
            print(f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)} "
                  f"What was Heard -> {self.detected_language or 'N/A'} "
                  f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)}")
            print(filtered_original_text)
        elif not self.args.no_log:
             print(f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)} "
                  f"Original (Blocked/Empty) -> {self.detected_language or 'N/A'} "
                  f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)}")

        if has_translation:
            print(f"{'-' * int((shutil.get_terminal_size().columns - 20) / 2)} "
                  f"EN Translation "
                  f"{'-' * int((shutil.get_terminal_size().columns - 20) / 2)}")
            print(f"{filtered_translated}\n")

        if has_target_transcription:
            target_lang_display = self.args.target_language or 'N/A'
            source_lang_display = self.detected_language or 'N/A'
            header_text = f"{source_lang_display} -> {target_lang_display}"
            padding_chars = len(header_text) + 2
            print(f"{'-' * int((shutil.get_terminal_size().columns - padding_chars) / 2)} "
                  f"{header_text} "
                  f"{'-' * int((shutil.get_terminal_size().columns - padding_chars) / 2)}")
            print(f"{filtered_transcribed}\n")

    def _display_simple_results(self, filtered_original_text: str) -> None:
        if filtered_original_text and not self._should_block_output(filtered_original_text, 'original'):
            print(f"[Input ({self.detected_language or 'N/A'})]: {filtered_original_text}\n")
        
        if self.args.transcribe and self.transcribed_text:
            filtered_transcribed = self._filter_text(self.transcribed_text)
            if filtered_transcribed and not self._should_block_output(filtered_transcribed, 'target'):
                print(f"[Transcription ({self.detected_language or 'N/A'} -> "
                      f"{self.args.target_language or 'N/A'})]: {filtered_transcribed}\n")
                
        if self.args.translate and self.translated_text:
            filtered_translated = self._filter_text(self.translated_text)
            if filtered_translated and not self._should_block_output(filtered_translated, 'translation'):
                print(f"[Translation (EN)]: {filtered_translated}\n")

    def _should_block_output(self, text, key):
        if not text:
            return False 
        
        blocklist_path_valid = isinstance(self._BLOCKLIST_PATH, str) and (os.path.exists(self._BLOCKLIST_PATH) or self._AUTO_BLOCKLIST_ENABLED)

        if blocklist_path_valid and is_phrase_in_blocklist(text, self._BLOCKLIST_PATH):
            if not self.args.no_log and self._DEBUG_BLOCK_SIMILAR: print(f"[DEBUG] Blocked by blocklist: '{text}'")
            return True
        
        if self._ENABLE_SIMILAR_PROTECTION:
            last = self._last_output.get(key)
            if last and is_similar(text, last):
                if not self.args.no_log and self._DEBUG_BLOCK_SIMILAR: print(f"[DEBUG] Blocked by similarity: '{text}' (similar to '{last}')")
                self._handle_blocked_phrase(text, key)
                return True
                
        self._last_output[key] = text
        return False

    def _handle_blocked_phrase(self, text, key):
        if not text:
            return
        self._blocked_phrase_history[key].append(text)
        
        if self._AUTO_BLOCKLIST_ENABLED and isinstance(self._BLOCKLIST_PATH, str):
            if self._blocked_phrase_history[key].count(text) >= 3:
                if not is_phrase_in_blocklist(text, self._BLOCKLIST_PATH):
                    added = add_phrase_to_blocklist(text, self._BLOCKLIST_PATH)
                    if added and not self.args.no_log:
                        print(f"[INFO] Auto-added phrase to blocklist: {text}")
                    while text in self._blocked_phrase_history[key]:
                        self._blocked_phrase_history[key].remove(text)