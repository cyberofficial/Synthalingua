# Synthalingua Environment Setup Guide

This guide explains how to use the `set_up_env.exe` tool to set up and manage the Synthalingua environment. This tool is provided as a compiled executable for Windows users, so you do **not** need to run it with Python.

---

## What is `set_up_env.exe`?

`set_up_env.exe` is a one-stop setup utility for Synthalingua. It automates the download, installation, and configuration of all required tools:
- **FFmpeg** (audio/video processing)
- **yt-dlp** (video downloader)
- **7zr** (archive extractor)
- **Miniconda** (Python environment manager, for vocal isolation)
- **Demucs** (vocal isolation, optional)

It also creates a batch file (`ffmpeg_path.bat`) to set up your PATH and activate the correct environment for Synthalingua.

---

## How to Use `set_up_env.exe`

1. **Locate the Executable**
   - Find `set_up_env.exe` in your Synthalingua folder (usually in the main directory).

2. **DO NOT Run as Administrator (NOT Recommended)**
   - Click `set_up_env.exe` as is and just run.

3. **Follow the Prompts**
   - The tool is interactive. It will ask if you want to reuse existing tools, provide your own, or download fresh copies.
   - For a fresh install, just press Enter to accept defaults unless you have custom requirements.
   - **Miniconda Path Warning:**
     - It is strongly recommended to use the default Miniconda installation path.
     - If you must choose a custom location, make absolutely sure the path contains **NO SPACES**. Paths with spaces can cause installation and runtime errors with Miniconda and other tools.
     - The setup tool will warn you and prevent you from using a path with spaces.

---

## Command-Line Arguments

You can run `set_up_env.exe` from a terminal (PowerShell or Command Prompt) with the following options:

- `set_up_env.exe`  
  Basic setup (FFmpeg, yt-dlp, 7zr only)

- `set_up_env.exe --using_vocal_isolation`  
  Also installs Miniconda and Demucs for vocal isolation features

- `set_up_env.exe --reinstall`  
  Wipes tool folders/files and redownloads everything fresh

- `set_up_env.exe --reinstall --using_vocal_isolation`  
  Full reinstall, including vocal isolation tools

**Tip:** If you double-click the exe, it will prompt you interactively for these options.

---

## Keeping Your `data_whisper` Folder

The `data_whisper` folder contains your Miniconda environment and Demucs installation. To **preserve** your environment and avoid re-downloading large models or packages:

- **Do NOT use `--reinstall`** unless you want to wipe and start over.
- If prompted about removing `data_whisper` or Miniconda, choose **No** to keep your environment.
- You can safely update other tools (FFmpeg, yt-dlp, etc.) without affecting `data_whisper`.


### Example: Backing Up and Restoring Your Environment
#### Sample Interactive Session: Preserving Your Environment

When running `set_up_env.exe`, here's what you'll see and how to respond to preserve your environment:

**Fresh Install (First Time Running):**
```
🆕 Fresh installation detected!
For the best experience, we recommend setting up vocal isolation features.
Would you like to set up vocal isolation (demucs) along with the basic tools? (yes/no): yes

Miniconda will be installed to: C:\bin\Synthalingua\miniconda
Do you agree to install Miniconda to this path? (yes/no): yes

⚠️  It is strongly recommended to use the default installation path for Miniconda.
   Changing the location is not recommended unless absolutely necessary.
   If you must choose a custom location, make sure the path contains NO SPACES.
Please enter a custom path for Miniconda installation (NO SPACES, recommended to keep the default): D:\My Custom Folder\miniconda
❌ Path cannot contain spaces. Please try again with a path that has NO SPACES.
Please enter a custom path for Miniconda installation (NO SPACES, recommended to keep the default): D:\MinicondaNoSpaces
```

**Existing Installation (Updating Tools):**
```
Found existing 7zr.exe. Use it or download fresh? (use/download): use
Do you already have FFmpeg? (yes/no): no
FFmpeg folder already exists, skipping download.
Do you already have yt-dlp? (yes/no): no
yt-dlp folder already exists, skipping download.
```

**Vocal Isolation Setup (Preserving Environment):**
```
A data_whisper environment already exists at C:\bin\Synthalingua\miniconda\envs\data_whisper.
Would you like to (k)eep, (r)ecreate, or (s)pecify a different environment? (keep/recreate/specify): keep
Using data_whisper environment at C:\bin\Synthalingua\miniconda\envs\data_whisper.
```

**Device Selection (During Setup):**
```
Synthalingua supports both CPU and GPU (CUDA) processing.
This affects both transcription and vocal isolation (demucs) performance.
Which device do you typically want to use with Synthalingua? (cpu/cuda): cuda
```

**Important:** Always answer `keep` when asked about environment options, and `yes` when asked about reusing assets. This preserves your models and packages.

To back up your environment:

1. Close all Synthalingua programs.
2. Copy the following folders to a safe location (e.g., an external drive or backup folder):
   - `data_whisper` (in your Synthalingua directory)
   - Miniconda install directory (default: `C:\bin\Synthalingua\miniconda`)

To restore your environment on the same or a new PC:

1. Copy both folders back to their original locations.
2. Run `set_up_env.exe` (without `--reinstall`) to update tool paths if needed.
3. Run `ffmpeg_path.bat` to activate the environment.

This will preserve all installed packages, models, and settings. You can use this method to migrate or recover your setup easily.

---

## Complete Interactive Session Examples

### Scenario 1: Fresh Installation with Vocal Isolation

```
Version 0.0.41
🆕 Fresh installation detected!
For the best experience, we recommend setting up vocal isolation features.
Would you like to set up vocal isolation (demucs) along with the basic tools? (yes/no): yes

This script will download the following tools to 'downloaded_assets/' folder:
1. FFmpeg, 2. yt-dlp, 3. 7zr
4. Miniconda, 5. Demucs

All installers and tools will be saved locally for reuse.

Miniconda will be installed to: C:\bin\Synthalingua\miniconda
Do you agree to install Miniconda to this path? (yes/no): yes

Do you want to provide your own version of 7zr.exe? (yes/no): no
Do you already have FFmpeg? (yes/no): no
Do you already have yt-dlp? (yes/no): no

Setting up vocal isolation feature...
Miniconda not found. Downloading miniconda...
Creating data_whisper environment with Python 3.12...

Synthalingua supports both CPU and GPU (CUDA) processing.
This affects both transcription and vocal isolation (demucs) performance.
Which device do you typically want to use with Synthalingua? (cpu/cuda): cuda

Installing demucs and diffq in data_whisper environment...
Vocal isolation setup completed successfully!
```

### Scenario 2: Updating Existing Installation (Preserving Environment)

```
Version 0.0.41
Config file already exists. Use --reinstall to set up again, or --using_vocal_isolation to add vocal isolation.
```

**To update tools while keeping your environment, run:**
```
set_up_env.exe --reinstall
```

**Then you'll see:**
```
Detected existing FFmpeg at C:\Synthalingua\downloaded_assets\ffmpeg. Reuse this asset? (yes/no): yes
Detected existing yt-dlp at C:\Synthalingua\downloaded_assets\yt-dlp_win. Reuse this asset? (yes/no): yes
Detected existing 7zr.exe at C:\Synthalingua\downloaded_assets\7zr.exe. Reuse this asset? (yes/no): yes
Detected existing Miniconda installation at C:\bin\Synthalingua\miniconda. Reuse this asset? (yes/no): yes

Miniconda is already installed at C:\bin\Synthalingua\miniconda.
Do you want to (w)ipe and reinstall Miniconda, or (k)eep and reuse it? (wipe/keep): keep

A data_whisper environment already exists at C:\bin\Synthalingua\miniconda\envs\data_whisper.
Would you like to (k)eep, (r)ecreate, or (s)pecify a different environment? (keep/recreate/specify): keep
Using data_whisper environment at C:\bin\Synthalingua\miniconda\envs\data_whisper.
```

### Scenario 3: Using Your Own Tools

```
Do you want to provide your own version of 7zr.exe? (yes/no): yes
Please enter the path to your 7zr.exe file: C:\MyTools\7zr.exe

Do you already have FFmpeg? (yes/no): yes
Do you want to use the system default FFmpeg? (yes/no): no
Please enter the path to your FFmpeg bin folder: C:\MyTools\ffmpeg\bin

Do you already have yt-dlp? (yes/no): yes
Do you want to use the system default yt-dlp? (yes/no): yes
```

**Key Points:**
- Always answer `yes` when asked about reusing assets to preserve your environment
- Answer `keep` when asked about wiping/keeping Miniconda installation
- Answer `keep` when asked about environment options to preserve your models and packages
- The script remembers your choices and won't re-download unless you specifically request it
- Use `--reinstall` to update tools while preserving your environment by choosing the preserve options

---

## Script Details & Advanced Usage

- **Interactive Prompts:** The tool will ask if you want to reuse, download, or provide your own versions of each tool. This helps avoid unnecessary downloads and lets you use custom builds.
- **Batch File Creation:** After setup, a `ffmpeg_path.bat` file is created. Run this batch file to set up your PATH and activate the correct environment for Synthalingua.
- **Vocal Isolation:** If you enable vocal isolation, the tool installs Miniconda and Demucs, and sets up a `data_whisper` environment. You can choose CPU or CUDA (GPU) support during setup.
- **Safe Reinstallation:** The `--reinstall` flag lets you wipe and redownload tools. You will be prompted before deleting important folders like `data_whisper`.
- **Custom Paths:** You can specify a custom Miniconda install path if you do not want to use the default.

---

## Troubleshooting

- If you encounter errors, check the `troubleshooting.md` in the `information` folder.
- For advanced help, consult the [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues) page.

---

**For best results, always read the prompts carefully and back up your environment before making major changes!**
