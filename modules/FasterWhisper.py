import os
import pycountry
import whisper
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio, pad_or_trim


class FasterWhisperModel:
    def __init__(self, model: str, device, download_root: str, compute_type: str) -> None:
        download_root = os.path.join(download_root, "FasterWhisper")

        self.model = model
        self.device = device
        self.audio_model = WhisperModel(model, device=device, download_root=download_root, compute_type=compute_type)

    def detect_language(self, file_path: str) -> dict:
        """
        Detects language from audio content

        Args:
            file_path (str): Path to the audio file to transcribe

        Returns:
            dict[str, float]: List of languages with their percentage likelihood of being the language of the audio
        """
        audio = decode_audio(file_path, split_stereo=False)
        
        # Ensure audio is a 1D numpy array with proper format for whisper
        if isinstance(audio, tuple):
            # If split_stereo returned a tuple, take the first channel
            audio = audio[0]
        
        # Ensure audio is properly formatted (1D float32 array)
        if audio.ndim > 1:
            audio = audio.flatten()
        
        audio = pad_or_trim(audio)

        # Could not find log_mel_spectrogram() method in faster_whisper library
        # Whisper library's implementation replacement
        # similarly to (if ram == "11gb-v3")
        n_mels = 128 if self.model in ["large-v3", "large"] else 80
        mel = whisper.log_mel_spectrogram(
            audio,
            n_mels=n_mels
        ).to(self.device)

        _, _, language_probs = self.audio_model.detect_language(features=mel.numpy())  # type: ignore
        return dict(language_probs)

    def transcribe(self, file_path: str, **kwargs) -> str:
        """
        Transcribe an audio file

        Args:
            file_path (str): Path to the audio file to transcribe

            kwargs:
                language (str): Language code for transcription
                fp16 (bool): Whether to use 16-bit precision
                condition_on_previous_text (bool): Provides the previous output of the model as a prompt for the next window
                task (str): Perform X->X speech recognition ('transcribe') or X->English translation ('translate')

        Returns:
            str: string of the transcription
        """
        language = kwargs.get("language")
        condition_on_previous_text = kwargs.get("condition_on_previous_text")
        task = kwargs.get("task")

        # Pycountry library used to convert language to the required format (English -> en)
        # Convert language name to ISO 639-1 code if needed
        if language and len(language) > 2:
            try:
                lang_obj = pycountry.languages.get(name=language)
                if lang_obj and hasattr(lang_obj, 'alpha_2'):
                    language = lang_obj.alpha_2
                else:
                    raise ValueError(f"Could not find ISO code for language: {language}")
            except Exception as e:
                raise ValueError(f"Language conversion error: {e}")
        # else, assume language is already a code
        # Ensure task and condition_on_previous_text have valid defaults
        if task is None:
            task = "transcribe"
        if condition_on_previous_text is None:
            condition_on_previous_text = False
        segments, _ = self.audio_model.transcribe(audio=file_path, task=task, condition_on_previous_text=condition_on_previous_text, language=language)

        result = ""
        for segment in segments:
            # Only append the transcribed text, not the full Segment object
            if hasattr(segment, 'text'):
                result += segment.text
            else:
                result += str(segment)  # fallback, but should not happen
        # First segment starts with a space (ex " text text text...") strip() used to remove it
        return result.strip()