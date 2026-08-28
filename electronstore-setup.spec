# -*- mode: python ; coding: utf-8 -*-

# PyInstaller build config for the online installer (ElectronStoreSetup.exe).
# Build on Windows with:
#     py -m PyInstaller electronstore-setup.spec --noconfirm
# Output: dist\ElectronStoreSetup.exe — the single file to hand to the shop.

a = Analysis(
    ["installer.py"],
    pathex=[],
    binaries=[],
    datas=[("icon.ico", ".")],
    hiddenimports=["paths"],
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
    name="ElectronStoreSetup",
    icon="icon.ico",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # no black console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)