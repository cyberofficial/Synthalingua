import os
import faster_whisper
import pycountry
import whisper
from faster_whisper import WhisperModel


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
        audio = faster_whisper.audio.decode_audio(file_path)
        audio = faster_whisper.audio.pad_or_trim(audio)

        # Could not find log_mel_spectrogram() method in faster_whisper library
        # Whisper library's implementation replacement
        # similarly to (if ram == "11gb-v3")
        n_mels = 128 if self.model in ["large-v3", "large"] else 80
        mel = whisper.log_mel_spectrogram(
            audio,
            n_mels=n_mels
        ).to(self.device)

        _, _, language_probs = self.audio_model.detect_language(features=mel)
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
        language = pycountry.languages.get(language).alpha_2
        segments, _ = self.audio_model.transcribe(audio=file_path, task=task, condition_on_previous_text=condition_on_previous_text, language=language)

        result = ""
        for segment in segments:
            result += segment
        # First segment starts with a space (ex " text text text...") strip() used to remove it
        return result.strip()