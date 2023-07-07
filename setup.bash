#!/bin/bash

# Realtime Whisper Translation App setup script

echo "Realtime Whisper Translation App"

if [ -d "data_whisper" ]; then
    echo -n "Python environment already exists. Do you want to reinstall? [y/n]: "
    read reinstall
    if [ "$reinstall" == "y" ] || [ "$reinstall" == "Y" ]; then
        echo "Deleting existing environment..."
        source data_whisper/bin/deactivate
        rm -rf data_whisper
    else
        echo "Exiting..."
        exit 0
    fi
fi

echo "Creating python environment..."
python -m venv data_whisper

echo "Created Env..."

source data_whisper/bin/activate
echo "Installing Whisper"
echo "Updating pip"
python -m pip install --upgrade pip

echo "Installing Requirements..."
pip install wheel
pip install setuptools-rust
pip install -r requirements_static.txt

echo "Fixing CUDA Since Whisper installs non-gpu version."
pip uninstall --yes torch torchvision torchaudio
pip cache purge
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

echo "Setup Completed!"

echo "Creating example shortcut in $(pwd)"
echo "You can edit with any text editor anytime."
echo ""
echo '#!/bin/bash' > livetranslation.sh
echo "source \"$(pwd)/data_whisper/bin/activate\"" >> livetranslation.sh
echo "python \"$(pwd)/transcribe_audio.py\" --ram 4gb --non_english --translate" >> livetranslation.sh
# add a pause
echo "read -p \"Press enter to exit...\"" >> livetranslation.sh
chmod +x livetranslation.sh

echo "Done!"
