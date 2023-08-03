from colorama import Fore, Back, Style, init
import argparse


def set_model_by_ram(ram, language):
    ram = ram.lower()
    
    if ram == "1gb":
        model = "tiny"
    elif ram == "2gb":
        model = "base"
    elif ram == "4gb":
        model = "small"
    elif ram == "6gb":
        model = "medium"
    elif ram == "12gb":
        model = "large"
        if language == "en":
            red_text = Fore.RED + Back.BLACK
            green_text = Fore.GREEN + Back.BLACK
            yellow_text = Fore.YELLOW + Back.BLACK
            reset_text = Style.RESET_ALL
            print(f"{red_text}WARNING{reset_text}: {yellow_text}12gb{reset_text} is overkill for English. Do you want to swap to {green_text}6gb{reset_text} model?")
            if input("y/n: ").lower() == "y":
                model = "medium"
            else:
                model = "large"
    else:
        raise ValueError("Invalid RAM setting provided")

    return model

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ram", default="4gb", help="Model to use", choices=["1gb", "2gb", "4gb", "6gb", "12gb"])
    parser.add_argument("--ramforce", action='store_true', help="Force the model to use the RAM setting provided. Warning: This may cause the model to crash.")
    parser.add_argument("--non_english", action='store_true', help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=100, help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=1, help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=1, help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    parser.add_argument("--no_log", action='store_true', help="Only show the last line of the transcription.")
    parser.add_argument("--translate", action='store_true', help="Translate the transcriptions to English.")
    parser.add_argument("--transcribe", action='store_true', help="transcribe the text into the desired language.")
    parser.add_argument("--language", help="Language to translate from.", type=str,
                        choices=["af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"])
    parser.add_argument("--target_language", help="Language to translate to.", type=str,
                        choices=["af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy", "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru", "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh", "Afrikaans", "Albanian", "Amharic", "Arabic", "Armenian", "Assamese", "Azerbaijani", "Bashkir", "Basque", "Belarusian", "Bengali", "Bosnian", "Breton", "Bulgarian", "Burmese", "Castilian", "Catalan", "Chinese", "Croatian", "Czech", "Danish", "Dutch", "English", "Estonian", "Faroese", "Finnish", "Flemish", "French", "Galician", "Georgian", "German", "Greek", "Gujarati", "Haitian", "Haitian Creole", "Hausa", "Hawaiian", "Hebrew", "Hindi", "Hungarian", "Icelandic", "Indonesian", "Italian", "Japanese", "Javanese", "Kannada", "Kazakh", "Khmer", "Korean", "Lao", "Latin", "Latvian", "Letzeburgesch", "Lingala", "Lithuanian", "Luxembourgish", "Macedonian", "Malagasy", "Malay", "Malayalam", "Maltese", "Maori", "Marathi", "Moldavian", "Moldovan", "Mongolian", "Myanmar", "Nepali", "Norwegian", "Nynorsk", "Occitan", "Panjabi", "Pashto", "Persian", "Polish", "Portuguese", "Punjabi", "Pushto", "Romanian", "Russian", "Sanskrit", "Serbian", "Shona", "Sindhi", "Sinhala", "Sinhalese", "Slovak", "Slovenian", "Somali", "Spanish", "Sundanese", "Swahili", "Swedish", "Tagalog", "Tajik", "Tamil", "Tatar", "Telugu", "Thai", "Tibetan", "Turkish", "Turkmen", "Ukrainian", "Urdu", "Uzbek", "Valencian", "Vietnamese", "Welsh", "Yiddish", "Yoruba"])
    parser.add_argument("--auto_model_swap", action='store_true', help="Automatically swap model based on detected language.")
    parser.add_argument("--device", default="cuda", help="Device to use for model. If not specified, will use CUDA if available. Available options: cpu, cuda")
    parser.add_argument("--cuda_device", default=0, help="CUDA device to use for model. If not specified, will use CUDA device 0.", type=int)
    parser.add_argument("--discord_webhook", default=None, help="Discord webhook to send transcription to.", type=str)
    parser.add_argument("--list_microphones", action='store_true', help="List available microphones and exit.")
    parser.add_argument("--set_microphone", default=None, help="Set default microphone to use.", type=str)
    parser.add_argument("--auto_language_lock", action='store_true', help="Automatically locks the language based on the detected language after set ammount of transcriptions.")
    parser.add_argument("--retry", action='store_true', help="Retries the transcription if it fails. May increase output time.")
    parser.add_argument("--use_finetune", action='store_true', help="Use finetuned model.")
    parser.add_argument("--updatebranch", default="master", help="Check which branch from the repo to check for updates. Default is master, choices are master and dev-testing. To turn off update checks use disable.", choices=["master", "dev-testing", "disable"])
    parser.add_argument("--keep_temp", action='store_true', help="Keep temporary audio files.")
    parser.add_argument("--about", action='store_true', help="About the project.")
    args = parser.parse_args()
    return args


print("Args Module Loaded")