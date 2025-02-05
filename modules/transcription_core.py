import io
import re
import shutil
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from time import sleep
import whisper
import torch
from colorama import Fore, Style

from modules.discord import send_to_discord_webhook
from modules.console_settings import set_window_title
from modules import api_backend
from modules.languages import get_valid_languages

class TranscriptionCore:
    def __init__(self, args, device, audio_model, blacklist):
        self.args = args
        self.device = device
        self.audio_model = audio_model
        self.blacklist = blacklist
        self.transcription = ['']
        self.phrase_time = None
        self.last_sample = bytes()
        self.detected_language = None
        self.original_text = None
        self.translated_text = None
        self.transcribed_text = None

    def process_audio(self, data_queue, source, temp_file):
        """Process audio data from the queue."""
        try:
            now = datetime.utcnow()
            if not data_queue.empty():
                if not self.args.no_log:
                    print("\nAudio stream detected...")
                
                phrase_complete = self._handle_phrase_timeout(now)
                self._collect_audio_data(data_queue)
                self._process_audio_file(source, temp_file)
                
                if phrase_complete:
                    self.transcription.append((self.original_text, 
                                            self.translated_text if self.args.translate else None,
                                            self.transcribed_text if self.args.transcribe else None,
                                            self.detected_language))
                else:
                    self.transcription[-1] = (self.original_text,
                                           self.translated_text if self.args.translate else None,
                                           self.transcribed_text if self.args.transcribe else None,
                                           self.detected_language)
                
                self._update_api_headers()
                self._display_results()

            sleep(0.5)
            return True
            
        except Exception as e:
            print(f"Error in process_audio: {str(e)}")
            return False

    def _handle_phrase_timeout(self, now):
        """Handle phrase timeout logic."""
        if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.args.phrase_timeout):
            self.last_sample = bytes()
            return True
        self.phrase_time = now
        return False

    def _collect_audio_data(self, data_queue):
        """Collect audio data from the queue."""
        while not data_queue.empty():
            data = data_queue.get()
            self.last_sample += data

    def _process_audio_file(self, source, temp_file):
        """Process the audio file and perform transcription."""
        audio_data = self._prepare_audio_data(source)
        self._save_audio_data(audio_data, temp_file)
        self._perform_transcription(temp_file)
        
        if self.args.translate:
            self._perform_translation(temp_file)
            
        if self.args.transcribe:
            self._perform_transcription_to_target(temp_file)

    def _prepare_audio_data(self, source):
        """Prepare audio data for processing."""
        return sr.AudioData(self.last_sample, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

    def _save_audio_data(self, audio_data, temp_file):
        """Save audio data to temporary file."""
        wav_data = io.BytesIO(audio_data.get_wav_data())
        with open(temp_file, 'w+b') as f:
            f.write(wav_data.read())

    def _perform_transcription(self, temp_file):
        """Perform initial transcription."""
        audio = whisper.load_audio(temp_file)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(
            audio, 
            n_mels=128 if self.args.ram == "12gb-v3" else 80
        ).to(self.device)

        self._detect_language(mel)
        
        result = self._transcribe_audio(temp_file)
        self.original_text = result['text'].strip()

    def _detect_language(self, mel):
        """Detect the language of the audio."""
        if ".en" in self.args.model:
            self.detected_language = "English"
        elif self.args.stream_language:
            print(f"Language Set: {self.args.stream_language}\n")
            self.detected_language = self.args.stream_language
        elif self.args.language:
            self.detected_language = self.args.language
        else:
            if not self.args.no_log:
                print(f"Detecting Language\n")
            _, language_probs = self.audio_model.detect_language(mel)
            self.detected_language = max(language_probs, key=language_probs.get)
            self._update_language_confidence(language_probs)

    def _update_language_confidence(self, language_probs):
        """Update and display language confidence."""
        try:
            confidence = language_probs[self.detected_language] * 100
            confidence_color = (Fore.GREEN if confidence > 75 
                              else (Fore.YELLOW if confidence > 50 else Fore.RED))
            set_window_title(self.detected_language, confidence)
            if not self.args.no_log:
                print(f"Detected language: {self.detected_language} "
                      f"{confidence_color}({confidence:.2f}% Accuracy){Style.RESET_ALL}")
        except:
            pass

    def _transcribe_audio(self, temp_file):
        """Transcribe audio file."""
        kwargs = {
            'language': self.detected_language,
            'condition_on_previous_text': self.args.condition_on_previous_text
        }
        if self.device.type == "cuda":
            kwargs['fp16'] = self.args.fp16
            
        result = self.audio_model.transcribe(temp_file, **kwargs)
        
        if not self.args.no_log:
            print(f"Detected Speech: {result['text']}")
            
        if result['text'] == "" and self.args.retry:
            if not self.args.no_log:
                print("Transcription failed, trying again...")
            result = self.audio_model.transcribe(temp_file, **kwargs)
            if not self.args.no_log:
                print(f"Detected Speech: {result['text']}")
                
        return result

    def _perform_translation(self, temp_file):
        """Perform translation if needed."""
        self.translated_text = ""
        if self.detected_language != 'en':
            if not self.args.no_log:
                print("Translating...")
            kwargs = {
                'task': 'translate',
                'language': self.detected_language,
                'condition_on_previous_text': self.args.condition_on_previous_text
            }
            if self.device.type == "cuda":
                kwargs['fp16'] = self.args.fp16
                
            translated_result = self.audio_model.transcribe(temp_file, **kwargs)
            self.translated_text = translated_result['text'].strip()
            
            if self.translated_text == "" and self.args.retry:
                if not self.args.no_log:
                    print("Translation failed, trying again...")
                translated_result = self.audio_model.transcribe(temp_file, **kwargs)
                self.translated_text = translated_result['text'].strip()

    def _perform_transcription_to_target(self, temp_file):
        """Perform transcription to target language if needed."""
        if not self.args.no_log:
            print(f"Transcribing to {self.args.target_language}...")
            
        kwargs = {
            'task': 'transcribe',
            'language': self.args.target_language,
            'condition_on_previous_text': self.args.condition_on_previous_text
        }
        if self.device.type == "cuda":
            kwargs['fp16'] = self.args.fp16
            
        transcribed_result = self.audio_model.transcribe(temp_file, **kwargs)
        self.transcribed_text = transcribed_result['text'].strip()
        
        if self.transcribed_text == "" and self.args.retry:
            if not self.args.no_log:
                print("Transcribe failed, trying again...")
            transcribed_result = self.audio_model.transcribe(temp_file, **kwargs)
            self.transcribed_text = transcribed_result['text'].strip()

    def _update_api_headers(self):
        """Update API headers if port number is specified."""
        if self.args.portnumber:
            self._update_filtered_headers()

    def _update_filtered_headers(self):
        """Update filtered headers for the API."""
        try:
            filtered_header_text = self._filter_text(self.original_text)
            api_backend.update_header(filtered_header_text)
            
            if self.translated_text:
                filtered_translated_text = self._filter_text(self.translated_text)
                api_backend.update_translated_header(filtered_translated_text)
                
            if self.transcribed_text:
                filtered_transcribed_text = self._filter_text(self.transcribed_text)
                api_backend.update_transcribed_header(filtered_transcribed_text)
        except:
            pass

    def _filter_text(self, text):
        """Filter text based on blacklist."""
        filtered_text = text.lower()
        for phrase in self.blacklist:
            filtered_text = re.sub(rf"\b{phrase.lower()}\b", "", filtered_text).strip()
        return filtered_text

    def _display_results(self):
        """Display the transcription results."""
        filtered_text = self._filter_text(self.original_text)
        
        if filtered_text:
            if not self.args.no_log:
                self._display_full_results(filtered_text)
            else:
                self._display_simple_results(filtered_text)

    def _display_full_results(self, filtered_text):
        """Display full results with formatting."""
        print("=" * shutil.get_terminal_size().columns)
        print(f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)} "
              f"What was Heard -> {self.detected_language} "
              f"{' ' * int((shutil.get_terminal_size().columns - 15) / 2)}")
        print(filtered_text)

        if self.args.translate and self.translated_text:
            filtered_translated = self._filter_text(self.translated_text)
            print(f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)} "
                  f"EN Translation "
                  f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)}")
            print(f"{filtered_translated}\n")

        if self.args.transcribe and self.transcribed_text:
            filtered_transcribed = self._filter_text(self.transcribed_text)
            print(f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)} "
                  f"{self.detected_language} -> {self.args.target_language} "
                  f"{'-' * int((shutil.get_terminal_size().columns - 15) / 2)}")
            print(f"{filtered_transcribed}\n")

    def _display_simple_results(self, filtered_text):
        """Display simple one-line results."""
        print(f"[Input ({self.detected_language})]: {filtered_text}\n")
        
        if self.args.transcribe and self.transcribed_text:
            filtered_transcribed = self._filter_text(self.transcribed_text)
            print(f"[Transcription ({self.detected_language} -> "
                  f"{self.args.target_language})]: {filtered_transcribed}\n")
            
        if self.args.translate and self.translated_text:
            filtered_translated = self._filter_text(self.translated_text)
            print(f"[Translation (EN)]: {filtered_translated}\n")