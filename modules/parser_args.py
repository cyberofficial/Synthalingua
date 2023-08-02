from colorama import Fore, Back, Style, init


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


print("Ram Module Loaded")