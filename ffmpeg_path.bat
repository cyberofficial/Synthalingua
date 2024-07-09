@echo of

:: This is for portable build version

Echo. Setting FFMPEG Path to %cd%\ffmpeg\bin
set "FFMPEG_PATH=%cd%\ffmpeg\bin"
set "PATH=%FFMPEG_PATH%;%PATH%"