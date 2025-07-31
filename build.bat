@echo off
call data_whisper\Scripts\activate.bat
python -m pip install wheel git+https://github.com/Nuitka/Nuitka.git@factory pyinstaller


:: python -m nuitka --enable-plugin=torch --follow-imports --windows-console-mode=force --include-package-data=whisper --include-data-dir=./html_data=html_data --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" transcribe_audio.py
::pyinstaller transcribe_audio.spec

Echo Building Set Up Environment

pyinstaller set_up_env.py --onefile ^
    --distpath dist\exes ^
    --icon="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" ^
    --hidden-import=os ^
    --hidden-import=platform ^
    --hidden-import=requests ^
    --hidden-import=subprocess ^
    --hidden-import=sys ^
    --hidden-import=zipfile ^
    --hidden-import=shutil ^
    --hidden-import=dataclasses ^
    --hidden-import=pathlib ^
    --hidden-import=typing ^
    --hidden-import=tqdm

Echo Building Remote Microphone

pyinstaller remote_microphone.py --onefile ^
    --distpath dist\exes ^
    --icon="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico"



:: pip install git+https://github.com/Nuitka/Nuitka.git@factory
:: Keep for later use

Echo Building Transcribe Audio

:: Will Build for Windows
set CL=/Zm2000 /bigobj
python -m nuitka --standalone ^
    --windows-console-mode=force ^
    --include-package=whisper ^
    --include-package-data=whisper ^
    --include-package=openvino ^
    --include-package-data=openvino ^
    --include-package=librosa ^
    --include-package-data=librosa ^
    --include-module=modules.transcribe_worker ^
    --include-data-file=modules/transcribe_worker.py=modules/transcribe_worker.py ^
    --include-data-dir=html_data=html_data ^
    --enable-plugin=torch ^
    --enable-plugin=numpy ^
    --plugin-enable=multiprocessing ^
    --follow-imports ^
    --windows-icon-from-ico="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" ^
    --file-version="1.1.1.7" ^
    --product-version="1.1.1.7" ^
    --company-name="Cyber's Apps" ^
    --product-name="Synthalingua Beta 7" ^
    --file-description="Real-time Audio Transcription and Translation" ^
    --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" ^
    --include-data-dir="E:\Synthalingua\Synthalingua_Main\data_whisper\Lib\site-packages\faster_whisper"=faster_whisper ^
    --include-data-dir="E:\Synthalingua\Synthalingua_Main\data_whisper\Lib\site-packages\optimum"=optimum ^
    transcribe_audio.py

::    --include-package=demucs ^
::    --include-package-data=demucs ^

pause