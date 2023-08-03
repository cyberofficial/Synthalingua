from modules.imports import *

# from the main file we passed ScriptCreator
def contributors(ScriptCreator, GitHubRepo):
    print(f"\033[4m{Fore.GREEN}About the project:{Style.RESET_ALL}\033[0m")
    print(f"This project was created by \033[4m{Fore.GREEN}{ScriptCreator}{Style.RESET_ALL}\033[0m and is licensed under the \033[4m{Fore.GREEN}GPLv3{Style.RESET_ALL}\033[0m license.\n\nYou can find the source code at \033[4m{Fore.GREEN}{GitHubRepo}{Style.RESET_ALL}\033[0m.\nBased on Whisper from OpenAI at \033[4m{Fore.GREEN}https://github.com/openai/whisper{Style.RESET_ALL}\033[0m.\n\n\n\n")
    # contributors #
    print(f"\033[4m{Fore.GREEN}Contributors:{Style.RESET_ALL}\033[0m")
    print("@DaniruKun from https://watsonindustries.live")
    print("[Expletive Deleted] https://evitelpxe.neocities.org")
    exit()


print("About Module Loaded")