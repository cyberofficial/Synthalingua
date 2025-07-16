# This page was basically researched and some things may be inaccurate, as I'm not fully on Linux to know all commands. If you have trouble, please make a repo on the issues page and I'll try to help out.

# Synthalingua Linux Setup Guide

This guide will help you set up Synthalingua on Linux systems. Synthalingua is a self-hosted AI tool for real-time audio translation and transcription that supports multilingual input/output, streaming, microphone, and file modes.

## Table of Contents
- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Environment Setup](#environment-setup)
- [Vocal Isolation Setup (Optional)](#vocal-isolation-setup-optional)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
1. **Python 3.12** - Download from [python.org](https://www.python.org/downloads/release/python-31210/)
2. **Git** - Install via your package manager
3. **FFmpeg** - For audio/video processing
4. **Build tools** - For compiling Python packages

### Optional Software
- **CUDA Toolkit 12.8** - For GPU acceleration (NVIDIA cards only)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 6 cores (or 3c/3l hybrid), 2.0 GHz+ | 8+ cores, 3.5 GHz+ |
| **RAM** | 8 GB (minimum) | 16+ GB RAM (plus 16+ GB swap/virtual memory recommended) |
| **GPU** | None (CPU mode) | NVIDIA with 8+ GB VRAM |
| **Storage** | 20-30 GB free (recommended for full suite) | 20-30 GB free (recommended for full suite) |
| **GPU** | None (CPU mode) | CUDA compatible cards (8+ GB VRAM) |
| **OS** | Ubuntu 20.04+, Debian 11+, Fedora 35+, or equivalent |


## Installation Steps

### 1. Update System and Install Dependencies

#### Ubuntu/Debian:
```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip \
    git build-essential curl wget \
    ffmpeg portaudio19-dev python3-pyaudio \
    pkg-config libffi-dev libssl-dev

# Install additional multimedia libraries
sudo apt install -y libsndfile1-dev libportaudio2 libasound2-dev
```

#### Fedora/RHEL/CentOS:
```bash
# Update system
sudo dnf update -y

# Install essential packages
sudo dnf install -y python3.12 python3.12-devel python3-pip \
    git gcc gcc-c++ make curl wget \
    ffmpeg portaudio-devel \
    pkgconfig libffi-devel openssl-devel

# Install additional multimedia libraries
sudo dnf install -y libsndfile-devel alsa-lib-devel
```

#### Arch Linux:
```bash
# Update system
sudo pacman -Syu

# Install essential packages
sudo pacman -S python python-pip git base-devel curl wget \
    ffmpeg portaudio python-pyaudio \
    pkg-config libffi openssl

# Install additional multimedia libraries
sudo pacman -S libsndfile alsa-lib
```

### 2. Install CUDA (Optional - for GPU acceleration)


If you have an NVIDIA GPU and want GPU acceleration:

1. Go to the official [CUDA 12.8 Download Archive](https://developer.nvidia.com/cuda-12-8-0-download-archive) and select the installer for your Linux distribution.
2. Follow the instructions provided on the NVIDIA page for your specific OS (Ubuntu, Debian, Fedora, etc.).
3. After installation, add CUDA to your PATH (if not done automatically):

```bash
# Add CUDA to PATH (add to ~/.bashrc or ~/.zshrc)
echo 'export PATH=/usr/local/cuda-12.8/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.8/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### 3. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/cyberofficial/Synthalingua.git
cd Synthalingua

# Verify you have the main files
ls -la transcribe_audio.py set_up_env.py requirements.txt
```

---

## Environment Setup

### 4. Create Python Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv data_whisper

# Activate the environment
source data_whisper/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 5. Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# If you encounter issues with PyAudio, try:
pip install --upgrade pyaudio

# For CUDA support (if you have NVIDIA GPU):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128

# For CPU-only:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 6. Download Required Tools

#### FFmpeg (if not installed via package manager):
```bash
# Create tools directory
mkdir -p downloaded_assets

# FFmpeg should already be installed via package manager
# Verify installation:
ffmpeg -version
```

#### yt-dlp:
```bash
# Download yt-dlp
cd downloaded_assets
wget https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
chmod +x yt-dlp

# Add to PATH or create symlink
sudo ln -sf $(pwd)/yt-dlp /usr/local/bin/yt-dlp
cd ..
```

---


## Vocal Isolation Setup (Optional)

If you want to use vocal isolation features (removes background music/noise):

### Install Demucs for Vocal Isolation

```bash
# Make sure you're in your Python virtual environment (data_whisper)
source data_whisper/bin/activate

# For CUDA support:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128

# For CPU-only:
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install demucs and dependencies
pip install demucs diffq Cython

# Install additional audio libraries
pip install soundfile librosa

# Verify installation
python -c "import demucs; print('Demucs installed successfully!')"
```

---

## Configuration

### 9. Create Environment Activation Script

Create a script to easily activate your environment:

```bash
# Create activation script
cat > activate_synthalingua.sh << 'EOF'
#!/bin/bash
# Synthalingua Environment Activation Script

echo "🎤 Activating Synthalingua Environment..."

# Activate Python environment
source data_whisper/bin/activate

# Set up PATH for tools
export PATH="$(pwd)/downloaded_assets:$PATH"



echo "✅ Environment activated!"
echo "📝 You can now run: python transcribe_audio.py [options]"
echo "📚 For help, run: python transcribe_audio.py --help"
echo "🔧 For examples, see: LINUX_SETUP.md"
EOF

chmod +x activate_synthalingua.sh
```

### 10. Test Your Installation

```bash
# Activate environment
source activate_synthalingua.sh

# Test basic functionality
python transcribe_audio.py --about

# Test microphone listing
python transcribe_audio.py --list_microphones

# Test with a simple command (adjust model size based on your RAM)
python transcribe_audio.py --ram 2gb --language auto --help
```

---

## Usage Examples

### Basic Microphone Transcription
```bash
# Activate environment
source activate_synthalingua.sh

# Start microphone transcription
python transcribe_audio.py --ram 2gb --microphone_enabled --language auto
```

### File-based Caption Generation
```bash
# Generate captions for a video file
python transcribe_audio.py --makecaptions --file_input "video.mp4" --file_output "captions" --ram 3gb

# With vocal isolation (removes background music)
python transcribe_audio.py --makecaptions --file_input "video.mp4" --isolate_vocals --silent_detect --ram 6gb
```

### Stream Translation
```bash
# Translate a live stream from Japanese to English
python transcribe_audio.py --stream "https://example.com/stream.m3u8" --language ja --translate --ram 6gb
```

### Web Interface
```bash
# Start with web interface on port 8080
python transcribe_audio.py --ram 3gb --microphone_enabled --portnumber 8080

# Then open browser to: http://localhost:8080
```

---

## Troubleshooting

### Common Issues and Solutions

#### Python/Package Issues:
```bash
# If you get "command not found" for python3.12:
sudo apt install python3.12-full  # Ubuntu/Debian
# or
sudo dnf install python3.12       # Fedora

# If PyAudio installation fails:
sudo apt install portaudio19-dev python3-pyaudio  # Ubuntu/Debian
pip install --upgrade pyaudio

# If you get SSL/TLS errors:
pip install --upgrade certifi requests urllib3
```

#### Audio Issues:
```bash
# Test audio devices:
python transcribe_audio.py --list_microphones

# If no microphones detected:
sudo apt install alsa-utils pulseaudio-utils
arecord -l  # List recording devices

# Fix permission issues:
sudo usermod -a -G audio $USER
# Then log out and back in
```

#### CUDA Issues:
```bash
# Verify CUDA installation:
nvidia-smi
nvcc --version

# Test PyTorch CUDA:
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# If CUDA not detected, reinstall PyTorch:
pip uninstall torch torchaudio
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

#### Memory Issues:
```bash
# For low RAM systems, use smaller models:
python transcribe_audio.py --ram 1gb [other options]

# Monitor memory usage:
htop
# or
free -h
```

#### File Permission Issues:
```bash
# Fix file permissions:
chmod +x activate_synthalingua.sh
chmod -R 755 downloaded_assets/

# If you get permission denied for audio:
sudo usermod -a -G audio $USER
```

### Environment Troubleshooting

If you need to recreate your environment:

```bash
# Deactivate current environment
deactivate

# Remove old environment
rm -rf data_whisper

# Start fresh
python3.12 -m venv data_whisper
source data_whisper/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Getting Help

1. **Check the main README.md** for general information
2. **Visit the issues page**: [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues)
3. **Check system logs** for detailed error messages:
   ```bash
   journalctl --user -f  # Follow user logs
   dmesg | tail          # Check kernel messages
   ```

---

## Performance Tips

### Optimizing for Your System

1. **Model Selection by RAM**:
   - 4GB RAM: `--ram 1gb`
   - 8GB RAM: `--ram 2gb` or `--ram 3gb`
   - 16GB+ RAM: `--ram 6gb` or higher

2. **GPU Acceleration**:
   ```bash
   # Force CUDA usage (if available)
   python transcribe_audio.py --device cuda --ram 6gb [other options]
   
   # Force CPU usage
   python transcribe_audio.py --device cpu --ram 2gb [other options]
   ```

3. **Audio Quality Settings**:
   ```bash
   # Higher quality microphone settings
   python transcribe_audio.py --energy_threshold 300 --record_timeout 3 [other options]
   ```

4. **For Server/Headless Use**:
   ```bash
   # Run without GUI, output to file
   python transcribe_audio.py --save_transcript --save_folder ./transcripts [other options]
   ```

---

## Updating Synthalingua

```bash
# Update the code
git pull origin master

# Update Python dependencies
source data_whisper/bin/activate
pip install --upgrade -r requirements.txt

# Update yt-dlp
cd downloaded_assets
wget -O yt-dlp https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp
chmod +x yt-dlp
cd ..
```

---

## Additional Resources

- **Main Repository**: [https://github.com/cyberofficial/Synthalingua](https://github.com/cyberofficial/Synthalingua)
- **Documentation**: Check the `information/` folder for detailed guides
- **Examples**: See `information/examples.md` for real-world usage scenarios
- **Troubleshooting**: See `information/troubleshooting.md` for common issues

---

**Need more help?** Open an issue on the GitHub repository with:
- Your Linux distribution and version
- Error messages (full text)
- Steps you've already tried
- Hardware specifications (CPU, RAM, GPU)
