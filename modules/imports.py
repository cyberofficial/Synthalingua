##### Primary Imports #####
try:
    import argparse
    import io
    import os
    import speech_recognition as sr
    import whisper
    import torch
    import math
    import sys
    import ctypes
    import shutil
    import numpy as np
    import requests
    import json
    import re
    import flask
    try:
        # if the os is not windows then skip this
        if os.name == 'nt':
            import sys, win32api
            win32api.SetDllDirectory(sys._MEIPASS)
    except:
        pass
    import pytz
    import pyaudio
    import humanize

    from datetime import datetime, timedelta
    from queue import Queue
    from tempfile import NamedTemporaryFile
    from time import sleep
    from sys import platform
    from colorama import Fore, Back, Style, init
    from tqdm import tqdm
    from numba import cuda
    from prettytable import PrettyTable
    from dateutil.tz import tzlocal
    from tzlocal import get_localzone

except Exception as e:
    print("Error Loading Primary Imports")
    print("Check to make sure you have all the required modules installed.")
    print("Error: " + str(e))
    sys.exit(1)



##### Extensions #####

print("Loading Extensions")
try:
    from modules.version_checker import check_for_updates
    from modules.model_downloader import fine_tune_model_dl, fine_tune_model_dl_compressed
    from modules.discord import send_to_discord_webhook
    from modules.console_settings import set_window_title
    from modules.warnings import print_warning
    from modules import parser_args
    from modules.languages import get_valid_languages
    from modules import api_backend
    #from modules import microphone_check
except Exception as e:
    print("Error Loading Extensions")
    print("Check the Modules folder and see if there are any missing or corrupted files.")
    print("You should make sure all these files are present:")
    print("version_checker.py, model_downloader.py, discord.py, console_settings.py, warnings.py, parser_args.py, languages.py")
    print("If you have git installed, you can use \"git reset --hard\" to reset the files to the latest version.")
    print("You could also just redownload the repository again.")
    print(e)
    sys.exit(1)
print("Extensions Loaded")
