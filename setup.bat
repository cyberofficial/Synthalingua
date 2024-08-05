@echo off
setlocal enabledelayedexpansion
Title Realtime Whisper Translation App Setup

:prechecks
Echo Checking for Python 3.10.x
Running command: python -V
python -V
Echo Does this show python 3.10.x? If not, close this window and make sure python 3.10 is installed and set to path
Echo. If it does show 3.10 press enter to move on.
pause > nul


:check_python
echo Checking for Python installation...
where python >nul 2>&1
if !errorlevel! neq 0 (
    echo Python is not installed or not in the PATH. Please install Python before continuing.
    exit /b
)

:prepare_environment
cls
if exist "data_whisper" (
    set /p reinstall="Python environment 'data_whisper' already exists. Reinstall it? [Y/N]: "
    if /i "!reinstall!"=="Y" (
        echo Deleting existing environment...
        rmdir /s /q data_whisper
    ) else (
        echo Operation cancelled by user.
        pause
        exit /b
    )
)

echo Creating a new Python virtual environment...
python -m venv data_whisper

echo Activating the environment...
call data_whisper\Scripts\activate.bat

:install_dependencies
echo Upgrading pip to the latest version...
python.exe -m pip install --upgrade pip

echo Installing wheel and setuptools-rust...
pip install wheel
pip install setuptools-rust

echo Checking for 'requirements.txt'...
if not exist "requirements.txt" (
    echo 'requirements.txt' not found. Please ensure it is in the current directory.
    exit /b
)

echo Installing requirements from 'requirements.txt'...
pip install -r requirements.txt

:cuda_patch
echo Applying CUDA patch to install GPU versions of PyTorch packages...
pip uninstall --yes torch torchvision torchaudio
pip cache purge
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo Whisper translation environment setup completed!

:create_shortcut
echo Creating a shortcut batch file for the translation app...
(
    echo @echo off
    echo cls
    echo call "data_whisper\Scripts\activate.bat"
    echo python "transcribe_audio.py" --ram 4gb --non_english --translate
    echo pause
) > "livetranslation.bat"

echo Shortcut 'livetranslation.bat' created in the current directory.
echo You can edit this file with notepad if necessary.

pause
exit /b
