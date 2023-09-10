@echo off
setlocal enabledelayedexpansion
Title Realtime Whipser Translation App
cls

if exist "data_whisper" (
    set /p reinstall="Python environment already exists. Do you want to reinstall? [y/n]: "
    if /i "!reinstall!"=="y" (
        echo Deleting existing environment...
        REM call data_whisper\Scripts\deactivate.bat :: Not Needed for now
        rmdir /s /q data_whisper
    ) else (
        echo Exiting...
        pause
        exit /b
    )
)

Echo Creating python environment...
python -m venv data_whisper

Echo Created Env...

call data_whisper\Scripts\activate.bat
Echo Installing Whisper
Echo Updating pip
python.exe -m pip install --upgrade pip

Echo Installing Requirements...
pip install wheel
pip install setuptools-rust
pip install -r requirements_static.txt

:cuda-patch
Echo Fixing CUDA Since Whisper installs non gpu version.
pip uninstall --yes torch torchvision torchaudio
pip cache purge
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Echo. Setup Completed!


:creating shortcut
Echo Creating example shortcut in %cd%
Echo You can edit with notepad anytime.
Echo.
Echo @echo off > livetranslation.bat
Echo cls >> livetranslation.bat
Echo call "data_whisper\Scripts\activate.bat" >> livetranslation.bat
Echo python "transcribe_audio.py" --ram 4gb --non_english --translate >> livetranslation.bat
Echo pause >> livetranslation.bat
pause

:eof
