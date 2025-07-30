import os
import pycountry
from optimum.intel import OVModelForSpeechSeq2Seq, OVWeightQuantizationConfig
from transformers import pipeline, AutoProcessor, GenerationConfig


class OpenVINOWhisperModel:
    def __init__(self, model: str, device, download_root: str, compute_type: str):
        download_root = os.path.join(download_root, "OpenVINO")

        if model == "turbo":
            model = "large-v3-turbo"
        model = f"openai/whisper-{model}"

        download_root = os.path.join(download_root, model)

        if not os.path.exists(download_root):
            audio_model = OVModelForSpeechSeq2Seq.from_pretrained(model, compile=False, export=True)
            audio_model.save_pretrained(download_root)

        # Get digits from "compute_type" (ex. int8 -> 8)
        compute_number = ''.join(i for i in compute_type if i.isdigit())

        # Quantization only supports 4 or 8 bits.
        # More info: https://huggingface.co/docs/optimum/main/en/intel/openvino/optimization#weight-only-quantization.
        if compute_number == "4" or compute_number == "8":
            quantization_config = OVWeightQuantizationConfig(bits=int(compute_number))
            audio_model = OVModelForSpeechSeq2Seq.from_pretrained(download_root, quantization_config=quantization_config, compile=False)
        else:
            audio_model = OVModelForSpeechSeq2Seq.from_pretrained(download_root, compile=False)

        processor = AutoProcessor.from_pretrained(model)
        generation_config = GenerationConfig.from_pretrained(model)

        audio_model.generation_config = generation_config

        audio_model.to(device)
        audio_model.compile()

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=audio_model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
        )


    def detect_language(self, file_path: str) -> dict:
        """
        Detects language from audio content

        Args:
            file_path (str): Path to the audio file

        Returns:
            dict[str, float]: List of languages with their percentage likelihood of being the language of the audio

        Note:
            Method used only returns most likely language instead of list with probabilities
            Warning: Pipeline is currently bugged only returning "None" as language (https://github.com/huggingface/transformers/issues/39404) possible implementation below when fixed:

            outputs = self.pipe(file_path, return_language=True)
            language = str(outputs.get("chunks")[0].get("language"))
            if language == "None":
                return {"na": 1.000000000000000}
            # Pycountry library used to convert language to the required format (English -> en)
            language = pycountry.languages.get(name=language).alpha_2
            return {language: 1.000000000000000}
        """
        raise NotImplementedError("Language detection is currently broken for OpenVINO. Please pick another --model_source")

    def transcribe(self, file_path: str, **kwargs) -> str:
        """
        Transcribe an audio file

        Args:
            file_path (str): Path to the audio file to transcribe

            kwargs:
                language (str): Language code for transcription
                task (str): Perform X->X speech recognition ('transcribe') or X->English translation ('translate')

        Returns:
            str: string of the transcription
        """
        language = kwargs.get("language")
        task = kwargs.get("task")
        # Pycountry library used to convert language to the required format (English -> en)
        language = pycountry.languages.get(language).alpha_2
        language = f"<|{language}|>"

        generate_kwargs = {
            "language": language,
            "task": task,
        }

        outputs = self.pipe(file_path, generate_kwargs=generate_kwargs)

        result = ""
        for output in outputs.values():
            result += output
        return result