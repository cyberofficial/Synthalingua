call data_whisper\Scripts\activate.bat
pyinstaller remote_microphone.py --onefile --distpath dist --icon="E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico" --noconfirm

pyinstaller set_up_env.spec --noconfirm

pyinstaller synthalingua.spec --noconfirm

pause