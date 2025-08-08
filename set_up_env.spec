# -*- mode: python ; coding: utf-8 -*-

"""
Optimized PyInstaller spec file for set_up_env.py
- Only add hiddenimports if PyInstaller misses a module (e.g., dynamic imports).
- Standard library modules (os, sys, subprocess, etc.) are detected automatically and should not be listed unless necessary.
- To add a hidden import, use: hiddenimports=['modulename']
"""

a = Analysis(
    ['set_up_env.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],  # Add only if you find missing modules at runtime
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchaudio', 'torchio', 'pytorch', 'pandas'],
    noarchive=False,
    optimize=1,  # Use bytecode optimization level 1 (removes asserts)
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='set_up_env',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Remove debug symbols from binaries
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['e:\Synthalingua\Synthalingua_Wrapper\syntha.ico'],
)
