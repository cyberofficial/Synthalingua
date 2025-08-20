@echo off
setlocal enabledelayedexpansion
Title Realtime Whisper Translation App Setup

:prechecks

if NOT exist synthalingua.py goto EoF_Error

Echo Checking for Python 3.12.x
echo Running command: python -V
python -V
echo.

rem Prompt user to verify the Python version
set /p user_check="Does this show Python 3.12.x? (Y/N): "
if /i "%user_check%" neq "Y" (
    echo It seems you do not have Python 3.12.x installed.
    echo Please download and install Python 3.12 from the following link:
    echo https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
    echo.
    set /p filepath="If you have Python 3.12.x installed but not in PATH, enter the path to the file python.exe for 3.12.x (e.g., C:\path\to\python\python.exe): "

    echo Using this for python: !filepath!
    set "python=!filepath!"
) else (
    rem Set default python if user confirms Python 3.12.x is installed
    set "python=python"
)

pause

goto :prepare_environment

:prepare_environment
cls
set "reuse_env="
if exist "data_whisper" (
    set /p reuse_env="Python environment 'data_whisper' already exists. Reuse it? [Y/N]: "
    if /i "!reuse_env!"=="Y" (
        echo Reusing existing environment...
        goto :install_dependencies
    ) else (
        set /p reinstall="Reinstall the environment (this will delete and recreate it)? [Y/N]: "
        if /i "!reinstall!"=="Y" (
            echo Deleting existing environment...
            rmdir /s /q data_whisper
        ) else (
            echo Operation cancelled by user.
            pause
            exit /b
        )
    )
)

echo Creating a new Python virtual environment...
!python! -m venv data_whisper

:install_dependencies
echo Activating the environment...
call data_whisper\Scripts\activate.bat

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
set /p has_cuda_gpu="Do you have an Nvidia GPU with CUDA cores? [Y/N]: "
if /i "!has_cuda_gpu!"=="Y" (
    set /p use_cuda="Do you want to use your Nvidia GPU for acceleration? [Y/N]: "
    if /i "!use_cuda!"=="Y" (
        echo Applying CUDA patch to install GPU versions of PyTorch packages...
        pip uninstall --yes torch 
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
        echo CUDA patch applied for Nvidia GPU support.
    ) else (
        echo Skipping CUDA patch. Using default CPU versions of torch, torchvision, and torchaudio.
    )
) else (
    echo Not using Nvidia GPU. Keeping default CPU versions of torch, torchvision, and torchaudio.
)

rem === Ask about vocal isolation (demucs) ===
set /p install_demucs="Do you plan to use the vocal isolation feature (requires demucs, ~1GB download)? [Y/N]: "
if /i "!install_demucs!"=="Y" (
    echo Installing demucs for vocal isolation support...
    pip install demucs
    if %errorlevel% neq 0 (
        echo Failed to install demucs. Please install manually if needed.
    )
    echo Demucs installation complete.
)

echo Whisper translation environment setup completed!

:create_shortcut
echo Creating a shortcut batch file for the translation app...
(
    echo @echo off
    echo cls
    echo call "data_whisper\Scripts\activate.bat"
    echo call ffmpeg_path.bat
            echo rem Example: Generate English captions for a video file
            echo python "synthalingua.py" --ram 3gb --makecaptions --file_input "C:\path\to\your\video.mp4" --file_output "C:\path\to\output\folder" --file_output_name "output_captions" --language Japanese --device cuda
            echo rem Edit the above paths and options as needed
    echo pause
) > "livetranslation.bat"

echo Shortcut 'livetranslation.bat' created in the current directory.
echo You can edit this file with notepad if necessary.
pause

:setup_env
Echo Setting up Environment Stuff.
call data_whisper\Scripts\activate.bat
python set_up_env.py --reinstall

exit /b

:EoF_Error
Echo can not fnd synthalingua.py
Echo Did you run as admin? If so DO NOT run as admin!
Echo. Please make sure you run setup in the same location as the source code.
Echo. If you are using powershell, Do not. Use command prompt instead.
pause
exit /b
