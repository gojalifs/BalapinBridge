# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec BalapinBridge (onefile, console/CLI).

Build:  pyinstaller BalapinBridge.spec
Output: dist/BalapinBridge.exe
Data:   drivers/ViGEmBus/* dibundle agar --setup bisa install offline.
"""

# vgamepad memuat ViGEmClient.dll via ctypes dengan path relatif __file__
# (vigem_client.py), tak terdeteksi PyInstaller -> bundle manual.
# Tanpa ini EXE gagal: "Failed to load dynlib/dll ... ViGEmClient.dll".
try:
    import vgamepad as _vg
    import os as _os
    _vg_dir = _os.path.dirname(_vg.__file__)
except Exception:
    _vg_dir = None

a = Analysis(
    ['bridge_app.py'],
    pathex=[],
    binaries=[],
    datas=[('drivers/ViGEmBus/ViGEmBus_1.22.0_x64_x86_arm64.exe',
            'drivers/ViGEmBus')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
if _vg_dir:
    a.datas += Tree(_vg_dir, prefix='vgamepad', excludes=['__pycache__'])
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BalapinBridge',
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
)
