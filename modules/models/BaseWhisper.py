import os
import whisper


class BaseWhisperModel:
    def __init__(self, model: str, device, download_root: str) -> None:
        download_root = os.path.join(download_root, "Whisper")

        self.model = model
        self.device = device
        self.audio_model = whisper.load_model(model, device=device, download_root=download_root)

    def detect_language(self, file_path: str) -> dict:
        """
        Detects language from audio content

        Args:
            file_path (str): Path to the audio file

        Returns:
            dict[str, float]: List of languages with their percentage likelihood of being the language of the audio
        """
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio)

        # similarly to (if ram == "11gb-v3")
        n_mels = 128 if self.model in ["large-v3", "large"] else 80
        mel = whisper.log_mel_spectrogram(
            audio,
            n_mels=n_mels
        ).to(self.device)
        _, language_probs = self.audio_model.detect_language(mel)
        return language_probs

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
        fp16 = kwargs.get("fp16")
        condition_on_previous_text = kwargs.get("condition_on_previous_text")
        task = kwargs.get("task")

        result = self.audio_model.transcribe(audio=file_path, language=language, fp16=fp16, condition_on_previous_text=condition_on_previous_text, task=task)
        return result["text"]