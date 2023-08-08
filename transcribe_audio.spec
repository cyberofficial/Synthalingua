# -*- mode: python ; coding: utf-8 -*-
import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)
import os
import glob

block_cipher = None

# Get the list of all DLLs in the CUDA bin directory
cuda_dlls = glob.glob('C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.1\\bin\\*.dll')

# Convert the list of DLL paths to a list of tuples for PyInstaller
binaries = [(dll, '.') for dll in cuda_dlls]

a = Analysis(
    ['transcribe_audio.py'],
    pathex=['.', './modules', './html_data'],
    binaries=binaries,
    datas=[('data_whisper\\Lib\\site-packages\\whisper\\assets\\mel_filters.npz', 'whisper\\assets'),
       ('data_whisper\\Lib\\site-packages\\whisper\\assets\\multilingual.tiktoken', 'whisper\\assets'),
       ('data_whisper\\Lib\\site-packages\\whisper\\assets\\gpt2.tiktoken', 'whisper\\assets'),
       ('html_data\\static\\*', 'html_data\\static\\'),
       ('html_data\\*', 'html_data\\')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    exclude_binaries=False,
    name='transcribe_audio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    icon=None,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)