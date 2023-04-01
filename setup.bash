#!/bin/bash

# Debian-based Linux setup script

echo "Realtime Whisper Translation App"

echo "Creating python environment..."
python -m venv data_whisper

echo "Created Env..."

source data_whisper/bin/activate
echo "Installing Whisper"
echo "Updating pip"
python -m pip install --upgrade pip

echo "Checking Portaudio Requirement..."
if [[ "$(cat /etc/os-release)" == *"debian"* ]]; then
    # Check if portaudio19-dev is installed
    if ! dpkg -s portaudio19-dev > /dev/null 2>&1; then
        # Try to install portaudio19-dev
        echo "Installing portaudio19-dev..."
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev
    fi
else
    echo "This script is only compatible with Debian Linux."
    exit 1
fi

echo "Installing Requirements..."
pip install -r requirements.txt --require-virtualenv

# Check if CUDA patch is required
if python -c "import torch; print(torch.version.cuda is None)" | grep "True" > /dev/null; then
    echo "Fixing CUDA Since Whisper installs non gpu version."
    pip uninstall --yes torch torchvision torchaudio
    pip cache purge
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
fi

echo "Setup Completed!"

# Create a shortcut
echo "Creating example shortcut in $(pwd)"
echo "You can edit with any text editor anytime."
echo ""
echo '#!/bin/bash' > livetranslation.sh
echo 'source "$(pwd)/data_whisper/bin/activate"' >> livetranslation.sh
echo 'python "$(pwd)/transcribe_audio.py" --ram 4gb --non_english --translate' >> livetranslation.sh
chmod +x livetranslation.sh

echo "Done!"
