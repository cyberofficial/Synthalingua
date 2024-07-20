@echo off

:: Set FFMPEG Path
set "FFMPEG_ROOT_PATH=%cd%\ffmpeg"
set "FFMPEG_PATH="
Echo. Setting FFMPEG Root Path to %FFMPEG_ROOT_PATH%

:: Set yt-dlp path
set "YTDLP_PATH=%cd%\yt-dlp_win"
Echo. Setting yt-dlp path to %YTDLP_PATH%

:: Check for aria2c and download if not exists
if not exist "aria2c.exe" (
  Echo. aria2c.exe not found, downloading...
  powershell -Command "Invoke-WebRequest -Uri 'https://github.com/aria2/aria2/releases/download/release-1.36.0/aria2-1.36.0-win-64bit-build1.zip' -OutFile 'aria2.zip'"
  powershell -Command "Expand-Archive -Path 'aria2.zip' -DestinationPath '.'"
  del /Q "aria2.zip"
  move /Y "aria2-1.36.0-win-64bit-build1\aria2c.exe" "%cd%\aria2c.exe"
  rmdir /Q /S "aria2-1.36.0-win-64bit-build1"
  Echo. aria2c.exe downloaded successfully.
) else (
  Echo. aria2c.exe already exists.
)

:: --- Download and extract FFmpeg ---
set "FFMPEG_FOUND=0"
if exist "%FFMPEG_ROOT_PATH%\*" (
  for /d %%d in ("%FFMPEG_ROOT_PATH%\*") do (
    if exist "%%d\bin\ffmpeg.exe" (
      set "FFMPEG_PATH=%%d\bin"
      set "FFMPEG_FOUND=1"
      goto :ffmpegFound
    )
  )
)
:ffmpegFound

if "%FFMPEG_FOUND%" == "0" (
  Echo. ffmpeg.exe not found, downloading...
  aria2c.exe -x 16 -s 16 -d . -o ffmpeg.7z https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z

  :: Create ffmpeg folder if it doesn't exist
  if not exist "%FFMPEG_ROOT_PATH%" mkdir "%FFMPEG_ROOT_PATH%"

  :: Extract ffmpeg.7z to ffmpeg\bin folder (using 7zr.exe)
  if not exist "7zr.exe" (
    Echo. 7zr.exe not found, downloading...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.7-zip.org/a/7zr.exe' -OutFile '7zr.exe'"
  )
  7zr.exe x "ffmpeg.7z" -o"%FFMPEG_ROOT_PATH%\" 

  :: Delete ffmpeg.7z
  del /Q "ffmpeg.7z"

  Echo. FFmpeg downloaded and extracted successfully.

  :: Find dynamically named FFmpeg folder
  for /f "tokens=*" %%i in ('powershell -Command "Get-ChildItem -Path \"%FFMPEG_ROOT_PATH%\" -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName"') do set "FFMPEG_PATH=%%i\bin"
  echo. FFmpeg Path is %FFMPEG_PATH%
) else (
  Echo. ffmpeg.exe already exists in %FFMPEG_PATH%. Skipping download.
)

:: --- Download and extract yt-dlp ---
if not exist "%YTDLP_PATH%\yt-dlp.exe" (
  Echo. yt-dlp.exe not found, downloading...
  aria2c.exe -x 16 -s 16 -d . -o yt-dlp_win.zip https://github.com/yt-dlp/yt-dlp/releases/download/2024.07.16/yt-dlp_win.zip

  :: Create yt-dlp_win folder if it doesn't exist
  if not exist "%YTDLP_PATH%" mkdir "%YTDLP_PATH%"

  :: Extract yt-dlp_win.zip to yt-dlp_win folder 
  powershell -Command "Expand-Archive -Path 'yt-dlp_win.zip' -DestinationPath '%YTDLP_PATH%'"

  :: Delete yt-dlp_win.zip
  del /Q "yt-dlp_win.zip"

  Echo. yt-dlp downloaded and extracted successfully.
) else (
  Echo. yt-dlp.exe already exists. Skipping download.
)

:: Set Global Path Temporary
set "PATH=%FFMPEG_PATH%;%YTDLP_PATH%;%PATH%"
