#!/bin/bash
set -e

# Title
clear
echo "==============================="
echo " Realtime Whisper Translation App Setup (Linux)"
echo "==============================="

# Check for synthalingua.py
if [ ! -f synthalingua.py ]; then
    echo "Error: synthalingua.py not found. Please run this script from the project root."
    exit 1
fi

# Check Python version
PYTHON_BIN="python3"
PYTHON_VERSION=$($PYTHON_BIN -V 2>&1)
echo "Detected Python version: $PYTHON_VERSION"

if [[ $PYTHON_VERSION != *"3.10."* ]]; then
    echo "Python 3.10.x is required."
    read -p "Enter the path to your Python 3.10.x binary (e.g., /usr/bin/python3.10): " PYTHON_BIN
    PYTHON_VERSION=$($PYTHON_BIN -V 2>&1)
    echo "Using: $PYTHON_BIN ($PYTHON_VERSION)"
    if [[ $PYTHON_VERSION != *"3.10."* ]]; then
        echo "Still not Python 3.10.x. Exiting."
        exit 1
    fi
fi

# Prepare environment
echo ""
if [ -d "data_whisper" ]; then
    read -p "Python environment 'data_whisper' already exists. Reinstall it? [Y/N]: " reinstall
    if [[ $reinstall =~ ^[Yy]$ ]]; then
        echo "Deleting existing environment..."
        rm -rf data_whisper
    else
        echo "Operation cancelled by user."
        exit 0
    fi
fi

# Create venv
$PYTHON_BIN -m venv data_whisper
source data_whisper/bin/activate

# Upgrade pip and install build tools
python -m pip install --upgrade pip
pip install wheel setuptools-rust

# Check requirements.txt
if [ ! -f requirements.txt ]; then
    echo "requirements.txt not found. Please ensure it is in the current directory."
    exit 1
fi

# Install requirements
pip install -r requirements.txt



# GPU/ROCm/CUDA/CPU selection logic
OS_TYPE=$(uname)
if [[ "$OS_TYPE" == "Darwin" ]]; then
    echo "[WARNING] CUDA/ROCm support may not be available on macOS (Darwin)."
    read -p "Do you want to try to install CUDA GPU support anyway? [Y/N]: " try_cuda
    if [[ $try_cuda =~ ^[Yy]$ ]]; then
        echo "Attempting CUDA install (may fail on macOS)..."
        pip uninstall -y torch torchaudio || true
        if pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128; then
            echo "CUDA patch applied (if supported)."
        else
            echo "CUDA install failed. Reinstalling CPU versions of torch packages..."
            pip uninstall -y torch torchaudio || true
            pip install torch torchaudio
            echo "CPU versions of torch packages installed."
        fi
    else
        echo "Skipping CUDA patch. Using default CPU versions of torch and torchaudio."
    fi
else
    echo "Select your GPU type for PyTorch installation:"
    echo "  1) Nvidia (CUDA)"
    echo "  2) AMD (ROCm)"
    echo "  3) CPU only"
    read -p "Enter 1 for Nvidia, 2 for AMD, or 3 for CPU: " gpu_choice
    if [[ "$gpu_choice" == "1" ]]; then
        read -p "Do you want to use your Nvidia GPU for acceleration? [Y/N]: " use_cuda
        if [[ $use_cuda =~ ^[Yy]$ ]]; then
            echo "Applying CUDA patch to install GPU versions of PyTorch packages..."
            pip uninstall -y torch torchaudio || true
            if pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128; then
                echo "CUDA patch applied for Nvidia GPU support."
            else
                echo "CUDA install failed. Reinstalling CPU versions of torch packages..."
                pip uninstall -y torch torchaudio || true
                pip install torch torchaudio
                echo "CPU versions of torch packages installed."
            fi
        else
            echo "Skipping CUDA patch. Using default CPU versions of torch and torchaudio."
        fi
    elif [[ "$gpu_choice" == "2" ]]; then
        read -p "Do you want to use your AMD GPU (ROCm) for acceleration? [Y/N]: " use_rocm
        if [[ $use_rocm =~ ^[Yy]$ ]]; then
            echo "Applying ROCm patch to install AMD GPU versions of PyTorch packages..."
            pip uninstall -y torch torchaudio || true
            if pip install torch torchaudio --index-url https://download.pytorch.org/whl/rocm6.4; then
                echo "ROCm patch applied for AMD GPU support."
            else
                echo "ROCm install failed. Reinstalling CPU versions of torch packages..."
                pip uninstall -y torch torchaudio || true
                pip install torch torchaudio
                echo "CPU versions of torch packages installed."
            fi
        else
            echo "Skipping ROCm patch. Using default CPU versions of torch and torchaudio."
        fi
    else
    echo "No GPU acceleration selected. Using default CPU versions of torch and torchaudio."
    fi
fi

# Demucs for vocal isolation
read -p "Do you plan to use the vocal isolation feature (requires demucs, ~1GB download)? [Y/N]: " install_demucs
if [[ $install_demucs =~ ^[Yy]$ ]]; then
    echo "Installing demucs for vocal isolation support..."
    pip install demucs
    if [ $? -ne 0 ]; then
        echo "Failed to install demucs. Please install manually if needed."
    else
        echo "Demucs installation complete."
    fi
fi

echo "Whisper translation environment setup completed!"


# Create shortcut script with a practical example
cat << EOF > livetranslation.sh
#!/bin/bash
source "[36m$(pwd)/data_whisper/bin/activate[0m"
# Example: Generate English captions for a video file
python "$(pwd)/synthalingua.py" --ram 3gb --makecaptions --file_input "/path/to/your/video.mp4" --file_output "/path/to/output/folder" --file_output_name "output_captions" --language Japanese --device cuda
# Edit the above paths and options as needed
EOF
chmod +x livetranslation.sh
echo "Shortcut 'livetranslation.sh' created in the current directory. You can edit this file if necessary."

# Run environment setup script if present
if [ -f set_up_env.py ]; then
    $PYTHON_BIN set_up_env.py
fi

echo "Setup complete."
