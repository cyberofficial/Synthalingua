import os
import whisper


class BaseWhisperModel:
    def __init__(self, model: str, device, download_root: str) -> None:
        # Ensure model files are in the correct folder before loading
        self._move_model_files_to_whisper_folder()
        
        download_root = os.path.join(download_root, "Whisper")
        self.model = model
        self.device = device
        self.audio_model = whisper.load_model(model, device=device, download_root=download_root)

    def _move_model_files_to_whisper_folder(self):
        """
        Detects specified model files in the models directory and moves them into models/Whisper.
        Will be removed in future update.
        """
        import shutil
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
        whisper_dir = os.path.join(base_dir, 'Whisper')
        os.makedirs(whisper_dir, exist_ok=True)
        model_files = [
            "base.en.pt", "base.pt", "large-v2.pt", "large-v3-turbo.pt", "large-v3.pt",
            "medium.en.pt", "medium.pt", "small.en.pt", "small.pt", "tiny.en.pt", "tiny.pt"
        ]
        for fname in model_files:
            src = os.path.join(base_dir, fname)
            dst = os.path.join(whisper_dir, fname)
            if os.path.isfile(src):
                print(f"Auto Migration of {fname} to {whisper_dir} in progress, please wait...")
                try:
                    shutil.move(src, dst)
                except Exception as e:
                    print(f"Failed to move {fname}: {e}")

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
        # Ensure return type is dict
        if isinstance(language_probs, dict):
            return language_probs
        elif isinstance(language_probs, list) and language_probs and isinstance(language_probs[0], dict):
            return language_probs[0]
        else:
            return {}

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
        if condition_on_previous_text is None:
            condition_on_previous_text = False
        task = kwargs.get("task")

        result = self.audio_model.transcribe(audio=file_path, language=language, fp16=fp16, condition_on_previous_text=condition_on_previous_text, task=task)
        text = result.get("text", "")
        if isinstance(text, str):
            return text
        elif isinstance(text, list):
            return " ".join(str(t) for t in text)
        else:
            return str(text)