from modules.imports import *  # or wherever args is defined

def fine_tune_model_dl(model_dir):
    print(f"Downloading fine-tuned model... [Via OneDrive (Public)] to '{model_dir}'")
    url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21456432&authkey=AIRKZih0go6iUTs"
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        with open(f"{model_dir}/fine_tuned_model-v2.pt", "wb") as f:
            # in red text say downloading "Downloading fine-tuned model..."
            print("\033[91mDownloading fine-tuned model...\033[0m", end=" ")
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
    print("Fine-tuned model downloaded.")

def fine_tune_model_dl_compressed(model_dir):
    print(f"Downloading fine-tuned compressed model... [Via OneDrive (Public)] to '{model_dir}'")
    url = "https://onedrive.live.com/download?cid=22FB8D582DCFA12B&resid=22FB8D582DCFA12B%21456433&authkey=AOTrQ949dOFhdxQ"
    r = requests.get(url, stream=True)
    total_length = int(r.headers.get('content-length'))
    with tqdm(total=total_length, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
        with open(f"{model_dir}/fine_tuned_model_compressed_v2.pt", "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(1024)
    print("Fine-tuned model (compressed) downloaded.")

print("Model Downloader Module Loaded")