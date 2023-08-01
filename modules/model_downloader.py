import requests
from tqdm import tqdm
import re

def fine_tune_model_dl():
    print("Downloading fine-tuned model... [Via OneDrive (Public)]")
    url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21456432&authkey=AIRKZih0go6iUTs"
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        with open("models/fine_tuned_model-v2.pt", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
    print("Fine-tuned model downloaded.")

def fine_tune_model_dl_compressed():
    print("Downloading fine-tuned compressed model... [Via OneDrive (Public)]")
    url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21456433&authkey=AOTrQ949dOFhdxQ"
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        with open("models/fine_tuned_model_compressed_v2.pt", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
    print("Fine-tuned model (compressed) downloaded.")