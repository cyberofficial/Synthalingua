call data_whisper\Scripts\activate.bat

pyinstaller set_up_env.spec --noconfirm
pyinstaller synthalingua.spec --noconfirm && xcopy "E:\Synthalingua\Synthalingua_Main\dist\release\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\1.2.6.rc10\" /E /H /Y /I




pause
goto :eof
pyinstaller remote_microphone.py --onefile --distpath dist --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico" --noconfirm


:: SET TORCHAUDIO_USE_BACKEND_DISPATCHER=1
:: SET TORIO_USE_FFMPEG=0

:eof