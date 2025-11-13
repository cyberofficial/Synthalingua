call data_whisper\Scripts\activate.bat

set VERSION=1.2.6.rc17
Echo building version %VERSION% 
pyinstaller set_up_env.spec --noconfirm
echo Moving files to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\set_up_env.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

echo building main app...
pyinstaller synthalingua.spec --noconfirm --clean
echo Moving files to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\release\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
Echo moving dep files...
xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\deps\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\_internal\deps" /E /H /Y /I


echo Moving GUI dev files to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\gui_dev\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I

Echo building remote microphone tool...
pyinstaller remote_microphone.py --onefile --distpath dist --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico" --noconfirm
echo Moving remote microphone tool to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\remote_microphone.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

pause
goto :eof



:: SET TORCHAUDIO_USE_BACKEND_DISPATCHER=1
:: SET TORIO_USE_FFMPEG=0

:eof