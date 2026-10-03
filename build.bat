call data_whisper\Scripts\activate.bat

set VERSION=1.2.6.steam.10
:: set steam var to true
set STEAM=true

Echo building version %VERSION% 

Echo Fetching bundled FFmpeg and yt-dlp (downloads fresh when upstream changed)...
python fetch_bundled_tools.py
if errorlevel 1 (
    echo WARNING: Fetching bundled tools failed. The build continues with whatever is staged.
)

pyinstaller set_up_env.spec --noconfirm
echo Moving files to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\set_up_env.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

echo building main app...
pyinstaller synthalingua.spec --noconfirm --clean
echo Moving files to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\release\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
Echo moving dep files...
xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\deps\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\_internal\deps" /E /H /Y /I


:: Copy appropriate GUI files based on STEAM variable
if "%STEAM%"=="true" (
    echo Moving GUI steam files to portable patch folder...
    xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\gui_dev-steam\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
) else (
    echo Moving GUI dev files to portable patch folder...
    xcopy "E:\Synthalingua\Synthalingua_Main\dist-portable\gui_dev\*" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /E /H /Y /I
)

Echo building remote microphone tool...
pyinstaller remote_microphone.py --onefile --distpath dist --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico" --noconfirm
echo Moving remote microphone tool to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\dist\remote_microphone.exe" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

:: Ship the demo audio used by the guided first run and functional testing.
echo Copying demo audio file to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\DemoTTS.mp3" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

:: Ship the bundled FFmpeg and yt-dlp tools. The packaged set_up_env.exe only
:: configures paths for these, it never downloads.
echo Copying bundled FFmpeg to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\downloaded_assets\ffmpeg" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\downloaded_assets\ffmpeg\" /E /H /Y /I
echo Copying bundled yt-dlp to portable patch folder...
xcopy "E:\Synthalingua\Synthalingua_Main\downloaded_assets\yt-dlp_win" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\downloaded_assets\yt-dlp_win\" /E /H /Y /I
echo Copying third party license file...
xcopy "E:\Synthalingua\Synthalingua_Main\THIRD_PARTY_LICENSES.txt" "E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\" /Y

:: Junction the shared models folder into this patch folder. A junction makes the
:: real models appear here with no extra disk use and nothing to maintain.
::
:: WARNING: the models path in the patch folder is a junction, not a real folder.
:: Never delete recursively inside it and never run rmdir /s on the patch folder,
:: because a recursive delete can follow the junction and remove the real models
:: in Synthalingua_Main\models. Nothing here is ever deleted or overwritten.
echo Junctioning the models folder into the patch folder...
set "MODEL_SOURCE=E:\Synthalingua\Synthalingua_Main\models"
set "MODEL_TARGET=E:\Synthalingua\Synthalingua_Main\dist-portable\patches\%VERSION%\models"

if not exist "%MODEL_SOURCE%\" (
    echo WARNING: Models folder not found at "%MODEL_SOURCE%", skipping model junction.
    goto :models_linked
)
if exist "%MODEL_TARGET%\" (
    echo Models already present at "%MODEL_TARGET%", leaving it untouched.
    goto :models_linked
)
mklink /J "%MODEL_TARGET%" "%MODEL_SOURCE%"
if errorlevel 1 (
    echo WARNING: Could not create the models junction, the patch folder may be missing models.
) else (
    echo Models junction created: "%MODEL_TARGET%" -^> "%MODEL_SOURCE%"
)

:models_linked
pause
goto :eof



:: SET TORCHAUDIO_USE_BACKEND_DISPATCHER=1
:: SET TORIO_USE_FFMPEG=0

:eof
