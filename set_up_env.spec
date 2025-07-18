# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['set_up_env.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['os', 'platform', 'requests', 'subprocess', 'sys', 'zipfile', 'shutil', 'dataclasses', 'pathlib', 'typing', 'tqdm'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
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
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['e:\\Synthalingua\\Synthalingua_Wrapper\\syntha.ico'],
)
