@echo off
call data_whisper\Scripts\activate.bat
python -m pip install nuitka pyinstaller
:: python -m nuitka --enable-plugin=torch --follow-imports --windows-console-mode=force --include-package-data=whisper --include-data-dir=./html_data=html_data --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" transcribe_audio.py
::pyinstaller transcribe_audio.spec

pyinstaller set_up_env.py --onefile

pyinstaller --onefile --distpath dist\publish_remote_microphone remote_microphone.py 


:: Will Build for Windows
set CL=/Zm2000 /bigobj
python -m nuitka --standalone ^
    --windows-console-mode=force ^
    --include-package=whisper ^
    --include-package-data=whisper ^
    --include-package=librosa ^
    --include-package-data=librosa ^
    --include-data-dir=./html_data=html_data ^
    --enable-plugin=torch ^
    --enable-plugin=numpy ^
    --plugin-enable=multiprocessing ^
    --follow-imports ^
    --windows-icon-from-ico="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" ^
    --file-version="1.1.1.0" ^
    --product-version="1.1.1.0" ^
    --company-name="Cyber's Apps" ^
    --product-name="Synthalingua" ^
    --file-description="Real-time Audio Transcription and Translation" ^
    --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" ^
    transcribe_audio.py

::    --include-package=demucs ^
::    --include-package-data=demucs ^

pause