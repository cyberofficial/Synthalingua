call data_whisper\Scripts\activate.bat

set VERSION=1.2.6.rc16
pyinstaller synthalingua.spec --noconfirm --clean
pyinstaller set_up_env.spec --noconfirm
xcopy "E:\Synthalingua\Synthalingua_Main\dist\release\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\gui_dev\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\deps\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\_internal\deps" /E /H /Y /I
xcopy "E:\Synthalingua\Synthalingua_Main\dist\set_up_env.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y
xcopy "E:\Synthalingua\Synthalingua_Main\dist\remote_microphone.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y







pause
goto :eof
pyinstaller remote_microphone.py --onefile --distpath dist --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico" --noconfirm


:: SET TORCHAUDIO_USE_BACKEND_DISPATCHER=1
:: SET TORIO_USE_FFMPEG=0

:eof