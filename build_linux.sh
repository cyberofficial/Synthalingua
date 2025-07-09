#!/bin/bash
set -e

# Experimental Linux build script, might not even work as expected, will try and use it later and try to fix any issues later. Hopefully...

# Activate Python environment
source data_whisper/bin/activate

# Install nuitka
python -m pip install nuitka

# Build for Linux with Nuitka
python -m nuitka --standalone \
    --include-package=whisper \
    --include-package-data=whisper \
    --include-package=librosa \
    --include-package-data=librosa \
    --include-data-dir=./html_data=html_data \
    --enable-plugin=torch \
    --enable-plugin=numpy \
    --plugin-enable=multiprocessing \
    --follow-imports \
    --file-version="1.1.1.0" \
    --product-version="1.1.1.0" \
    --company-name="Cyber's Apps" \
    --product-name="Synthalingua" \
    --file-description="Real-time Audio Transcription and Translation" \
    --output-dir="$(pwd)/dist/Main_Release_Linux" \
    transcribe_audio.py

echo "Linux build completed!"
echo "Binary location: $(pwd)/dist/Main_Release_Linux/transcribe_audio.dist/transcribe_audio"
