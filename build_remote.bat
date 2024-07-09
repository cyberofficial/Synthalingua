@echo off
call data_whisper\Scripts\activate.bat
pyinstaller --onefile --distpath dist\publish_remote_microphone remote_microphone.py 
pause