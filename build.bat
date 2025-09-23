@echo off
call data_whisper\Scripts\activate.bat
:: python -m pip install wheel git+https://github.com/Nuitka/Nuitka.git@factory pyinstaller


:: python -m nuitka --enable-plugin=torch --follow-imports --windows-console-mode=force --include-package-data=whisper --include-data-dir=./html_data=html_data --output-dir="E:\Synthalingua\Synthalingua_Main\dist\main_release" synthalingua.py
::pyinstaller synthalingua.spec

Echo Building Set Up Environment

pyinstaller set_up_env.spec 
:: --onefile ^
::     --distpath dist\exes ^
::     --icon="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" ^
::     --hidden-import=os ^
::     --hidden-import=platform ^
::     --hidden-import=requests ^
::     --hidden-import=subprocess ^
::     --hidden-import=sys ^
::     --hidden-import=zipfile ^
::     --hidden-import=shutil ^
::     --hidden-import=dataclasses ^
::     --hidden-import=pathlib ^
::     --hidden-import=typing ^
::     --hidden-import=tqdm

Echo Building Remote Microphone

pyinstaller remote_microphone.py --onefile --distpath dist\exes --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico"



:: pip install git+https://github.com/Nuitka/Nuitka.git@factory
:: Keep for later use
goto :eof

Echo Building Transcribe Audio

$env:CL = "/Zm5000 /bigobj"; python -m nuitka --standalone --windows-console-mode=force --output-dir="dist\main_release" --enable-plugin=torch --enable-plugin=numpy --plugin-enable=multiprocessing --include-package=whisper --include-package=openvino --include-package=librosa --include-package=optimum --include-package=optimum.intel.openvino --include-package=click --include-package=datasets --include-package=flask --include-package=fsspec --include-package=humanize --include-package=networkx --include-package=nuitka --include-package=numba --include-package=numpy --include-package=onnxruntime --include-package=onnxscript --include-package=pandas --include-package=pip --include-package=prettytable --include-package=pycountry --include-package=pygments --include-package=pyreadline3 --include-package=scipy --include-package=setuptools --include-package=sympy --include-package=torch --include-package=torchaudio --include-package=transformers --include-package=websockets --include-package=werkzeug --include-package=isympy --include-distribution-metadata=click --include-distribution-metadata=coloredlogs --include-distribution-metadata=datasets --include-distribution-metadata=flask --include-distribution-metadata=fsspec --include-distribution-metadata=humanize --include-distribution-metadata=librosa --include-distribution-metadata=networkx --include-distribution-metadata=nuitka --include-distribution-metadata=numba --include-distribution-metadata=numpy --include-distribution-metadata=onnx --include-distribution-metadata=onnxruntime --include-distribution-metadata=onnxscript --include-distribution-metadata=openvino --include-distribution-metadata=optimum --include-distribution-metadata=pandas --include-distribution-metadata=pip --include-distribution-metadata=prettytable --include-distribution-metadata=pycountry --include-distribution-metadata=pygments --include-distribution-metadata=pyreadline3 --include-distribution-metadata=scipy --include-distribution-metadata=setuptools --include-distribution-metadata=sympy --include-distribution-metadata=torch --include-distribution-metadata=torchaudio --include-distribution-metadata=transformers --include-distribution-metadata=websockets --include-distribution-metadata=werkzeug --include-module=modules.transcribe_worker --include-data-file="modules/transcribe_worker.py=modules/transcribe_worker.py" --include-data-dir="html_data=html_data" --include-data-dir="data_whisper\Lib\site-packages\faster_whisper=faster_whisper" --include-data-dir="data_whisper\Lib\site-packages\optimum=optimum" --follow-imports --nofollow-import-to=yt_dlp.lazy_extractors --windows-icon-from-ico="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" --file-version="1.1.1.7" --product-version="1.1.1.7" --company-name="Cyber's Apps" --product-name="Synthalingua Beta 7" --file-description="Real-time Audio Transcription and Translation" --mingw64 --clang --show-progress synthalingua.py

    --low-memory ^
goto :eof
:: run: python: find_metadata_packages_mkfile.py

$env:CL = "/Zm5000 /bigobj"; python -m nuitka --standalone --windows-console-mode=force --output-dir="dist\main_release" --enable-plugin=torch --enable-plugin=numpy --plugin-enable=multiprocessing --include-package=whisper --include-package=openvino --include-package=librosa --include-package=optimum --include-package=optimum.intel.openvino $(Get-Content nuitka_metadata_args.txt) --include-module=modules.transcribe_worker --include-data-file="modules/transcribe_worker.py=modules/transcribe_worker.py" --include-data-dir="html_data=html_data" --include-data-dir="data_whisper\Lib\site-packages\faster_whisper=faster_whisper" --include-data-dir="data_whisper\Lib\site-packages\optimum=optimum" --follow-imports --nofollow-import-to=yt_dlp.lazy_extractors --windows-icon-from-ico="e:\Synthalingua\Synthalingua_Wrapper\syntha.ico" --file-version="1.1.1.7" --product-version="1.1.1.7" --company-name="Cyber's Apps" --product-name="Synthalingua Beta 7" --file-description="Real-time Audio Transcription and Translation" --mingw64 --clang --show-progress synthalingua.py


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