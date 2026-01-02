# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import glob
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

sys.setrecursionlimit(5000)

# --- Data and Binary Collection ---
datas = []
datas += [('html_data', 'html_data')]

# Add entire video translation UI module (REQUIRED for frozen executable)
# This includes all Python files, worker scripts, and any future additions
datas += [
    ('modules/video_translation_ui', 'modules/video_translation_ui')
]

packages_with_data = [
    'whisper', 'librosa', 'openvino', 'optimum', 'faster_whisper', 'torch',
    'torchio', 'torchcodec', 'numpy', 'scipy', 'pandas', 'sklearn', 'pycountry',
    'certifi', 'tiktoken', 'onnx', 'onnxruntime', 'ctranslate2',
    'soundfile', 'pydub', 'av', 'huggingface_hub', 'transformers', 'datasets'
]
for pkg in packages_with_data:
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

# --- Collect CUDA Binaries ---
binaries = []
CUDA_PATH = 'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.9'
cuda_bin = os.path.join(CUDA_PATH, 'bin')
if os.path.exists(cuda_bin):
    cuda_dlls = glob.glob(os.path.join(cuda_bin, '*.dll'))
    binaries.extend((dll, '.') for dll in cuda_dlls)

# --- Hidden Imports ---
hiddenimports = [
    'sounddevice', 'speech_recognition', 'pyaudio', 'flask', 'werkzeug',
    'jinja2', 'socketio', 'engineio', 'eventlet', 'pycountry', 'psutil',
    'colorama', 'tqdm', 'yaml', 'regex', 'Cryptodome', 'humanize',
    # Flask-SocketIO and dependencies (REQUIRED for video translation UI)
    'flask_socketio', 'python_socketio', 'python_engineio',
    'simple_websocket', 'wsproto', 'h11',
    # Additional WebSocket support
    'websocket', 'websockets',
]
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('optimum')
hiddenimports += collect_submodules('datasets')
hiddenimports += collect_submodules('flask_socketio')
hiddenimports += collect_submodules('socketio')
hiddenimports += collect_submodules('engineio')
hiddenimports += collect_submodules('nncf')

# --- The Main Analysis Block ---
a = Analysis(
    ['synthalingua.py'],
    pathex=['.', './modules'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    # *** THIS IS THE CRITICAL FIX ***
    # This tells PyInstaller to embed and run our patch script before the main app.
    runtime_hooks=['rthook.py'],
    excludes=['PyQt5', 'tkinter', 'notebook'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [], [], [],
    name='synthalingua',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    icon=r'E:\Synthalingua\Synthalingua_Wrapper\assets\Synthalingua-chan-logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='release'
)