from modules.imports import *


def load_word_list(args):
    def load_blacklist(filename):
        if not filename.endswith(".txt"):
            raise ValueError("Blacklist file must be in .txt format.")

        blacklist = []
        try:
            with open(filename, "r", encoding="utf-8") as f:
                for line in f:
                    blacklist.append(line.strip())
        except FileNotFoundError:
            print(f"Warning: Blacklist file '{filename}' not found.")
        return blacklist

    if args.ignorelist:
        print(f"Loaded word filtering list from: {args.ignorelist}")
        blacklist = load_blacklist(args.ignorelist)

    else:
        blacklist = []
    # if blacklist.txt was found say loaded
    if len(blacklist) > 0:
        print(f"Loaded blacklist: {blacklist}")
    return blacklist

print("Word Block Module Loaded")