@echo off
call data_whisper\Scripts\activate.bat
python -m pip install wheel git+https://github.com/Nuitka/Nuitka.git@factory pyinstaller


:: python -m nuitka --enable-plugin=torch --follow-imports --windows-console-mode=force --include-package-data=whisper --include-data-dir=./html_data=html_data --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" synthalingua.py
::pyinstaller synthalingua.spec

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
set CL=/Zm5000 /bigobj
REM All metadata args are injected via PowerShell below; no batch loop needed
REM Update list: python -m pip list --format=freeze | ForEach-Object { $_.Split('==')[0] } | ForEach-Object { "--include-distribution-metadata=$_" } | Set-Content nuitka_metadata_args.txt
REM Use PowerShell to avoid command line length limits and preserve argument quoting
PowerShell -Command "python -m nuitka --standalone --windows-console-mode=force --include-package=whisper --include-package-data=whisper --include-package=openvino --include-package-data=openvino --include-package=librosa --include-package-data=librosa --include-module=modules.transcribe_worker --include-data-file=modules/transcribe_worker.py=modules/transcribe_worker.py --include-data-dir=html_data=html_data --include-package=optimum --include-package=optimum.intel.openvino --enable-plugin=torch --enable-plugin=numpy --plugin-enable=multiprocessing --follow-imports --windows-icon-from-ico='e:\Synthalingua\Synthalingua_Wrapper\syntha.ico' --file-version='1.1.1.7' --product-version='1.1.1.7' --company-name='Cyber''s Apps' --product-name='Synthalingua Beta 7' --file-description='Real-time Audio Transcription and Translation' --output-dir='E:\Synthalingua\Synthalingua_Main\dist\main_release' --include-data-dir='E:\Synthalingua\Synthalingua_Main\data_whisper\Lib\site-packages\faster_whisper'=faster_whisper --include-data-dir='E:\Synthalingua\Synthalingua_Main\data_whisper\Lib\site-packages\optimum'=optimum --nofollow-import-to=yt_dlp.lazy_extractors --mingw64 --clang --show-progress $((Get-Content nuitka_metadata_args.txt) -join ' ') synthalingua.py"

    --low-memory ^
goto :eof
::     
:: python -m pip list --format=freeze | ForEach-Object { $_.Split('==')[0] } | ForEach-Object { "--include-distribution-metadata=$_" } | Set-Content nuitka_metadata_args.txt
::

::    --include-package=demucs ^
::    --include-package-data=demucs ^

:: notes section
echo Extra pause to prevent from running.
pause 
echo Extra pause to prevent from running.
pause 
echo Extra pause to prevent from running.
pause 
echo Extra pause to prevent from running.
pause 

export CL="/Zm5000 /bigobj"
export CC=gcc
python -m nuitka --standalone \
    --windows-console-mode=force \
    --include-package=whisper \
    --include-package-data=whisper \
    --include-package=openvino \
    --include-package-data=openvino \
    --include-package=librosa \
    --include-package-data=librosa \
    --include-module=modules.transcribe_worker \
    --include-data-file=modules/transcribe_worker.py=modules/transcribe_worker.py \
    --include-data-dir=html_data=html_data \
    --enable-plugin=torch \
    --enable-plugin=numpy \
    --plugin-enable=multiprocessing \
    --follow-imports \
    --windows-icon-from-ico="/e/Synthalingua/Synthalingua_Wrapper/syntha.ico" \
    --file-version="1.1.1.7" \
    --product-version="1.1.1.7" \
    --company-name="Cyber's Apps" \
    --product-name="Synthalingua Beta 7" \
    --file-description="Real-time Audio Transcription and Translation" \
    --output-dir="/e/Synthalingua/Synthalingua_Main/dist/main_release" \
    --include-data-dir="/e/Synthalingua/Synthalingua_Main/data_whisper/Lib/site-packages/faster_whisper"=faster_whisper \
    --include-data-dir="/e/Synthalingua/Synthalingua_Main/data_whisper/Lib/site-packages/optimum"=optimum \
    --low-memory \
    --nofollow-import-to=yt_dlp.lazy_extractors \
    --lto=no \
    --mingw64 \
    --clang \
    synthalingua.py
:: end of notes

:eof
pause