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
    'numpy', 'scipy', 'pandas', 'sklearn', 'pycountry',
    'certifi', 'tiktoken', 'onnx', 'onnxruntime', 'ctranslate2',
    'soundfile', 'av', 'huggingface_hub', 'transformers', 'datasets',
    # Vocal isolation (demucs) runs inside this executable via
    # --run-demucs-worker, so it must ship with its own data files.
    # demucs bundles cdn/remote model definitions that collect_data_files picks up.
    'demucs', 'dora', 'einops', 'julius', 'openunmix', 'diffq', 'torchaudio', 'yaml'
]
for pkg in packages_with_data:
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

# pywebview keeps its JavaScript bridge and the WebView2 assemblies as package
# data, not as importable modules. Its own hook does this too (pyinstaller40
# entry point webview.__pyinstaller:get_hook_dirs), repeated here so the frozen
# desktop UI works even if that hook is not picked up.
try:
    datas += collect_data_files('webview', subdir='js')
    if sys.platform == 'win32':
        datas += collect_data_files('webview', subdir='lib')
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
    'colorama', 'tqdm', 'yaml', 'regex',
    # Flask-SocketIO and dependencies (REQUIRED for video translation UI)
    'flask_socketio',
    'simple_websocket', 'wsproto', 'h11',
    # Desktop UI (pywebview over the existing web pages). modules/desktop_ui.py
    # imports this stack lazily inside main(), so PyInstaller cannot see it from
    # the entry point. pywebview also ships its own PyInstaller hook that
    # registers the entry point below; these entries are the explicit belt to
    # that suspenders. See python_ui_spike.md.
    'webview', 'webview.dom', 'webview.platforms.winforms',
    'webview.platforms.edgechromium', 'clr', 'clr_loader', 'pythonnet',
    'proxy_tools', 'bottle', 'typing_extensions',
]
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('optimum')
hiddenimports += collect_submodules('datasets')
hiddenimports += collect_submodules('flask_socketio')
hiddenimports += collect_submodules('socketio')
hiddenimports += collect_submodules('engineio')
hiddenimports += collect_submodules('nncf')

# Demucs vocal isolation, executed inside this frozen executable through the
# --run-demucs-worker dispatch in synthalingua.py. These packages are imported
# dynamically or optionally by demucs, so they need explicit collection.
hiddenimports += collect_submodules('demucs')
hiddenimports += collect_submodules('dora')
hiddenimports += collect_submodules('einops')
hiddenimports += collect_submodules('openunmix')
hiddenimports += collect_submodules('diffq')
hiddenimports += collect_submodules('torchaudio')
hiddenimports += ['julius', 'lameenc']

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
    excludes=['PyQt5', 'tkinter', 'notebook', 'Cython'],
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
