# -*- mode: python ; coding: utf-8 -*-

# PyInstaller build config for ElectronStore POS.
# Build on Windows with:
#     py -m PyInstaller electronstore.spec --noconfirm
# Output: dist\ElectronStore.exe

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# matplotlib ships data/config files that must be bundled.
try:
    d, b, h = collect_all("matplotlib")
    datas += d
    binaries += b
    hiddenimports += h
except Exception:
    pass

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        "db", "paths", "backup", "export", "operations",
    ],
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
    name="ElectronStore",
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
