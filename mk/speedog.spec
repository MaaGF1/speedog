# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# ---------------------------------------------------------
# 1. Path Configuration
# ---------------------------------------------------------
spec_dir = SPECPATH
src_path = os.path.abspath(os.path.join(spec_dir, '..', 'src'))
icon_path = os.path.join(spec_dir, 'speedog.ico')

print(f"Spec file location (SPECPATH): {spec_dir}")
print(f"Source path resolved to: {src_path}")

if not os.path.exists(icon_path):
    print(f"WARNING: Icon file not found at {icon_path}. Build will proceed with default icon.")
    icon_path = None

main_script = os.path.join(src_path, 'main.py')
if not os.path.exists(main_script):
    raise FileNotFoundError(f"Cannot find main.py at: {main_script}")

# ---------------------------------------------------------
# 2. Collect Dependencies (The Fix)
# ---------------------------------------------------------

# Initialize lists
my_datas = [
    (os.path.join(src_path, 'speedog.conf'), '.')
]
my_binaries = []
my_hiddenimports = []

# Collect all resources from xspeedhack
# This grabs the 'bin' folder, DLLs, and ensures importlib can find them.
tmp_ret = collect_all('xspeedhack')
my_datas += tmp_ret[0]
my_binaries += tmp_ret[1]
my_hiddenimports += tmp_ret[2]

# ---------------------------------------------------------
# 3. Analysis
# ---------------------------------------------------------
a = Analysis(
    [main_script],
    pathex=[src_path],
    binaries=my_binaries,      # Use collected binaries
    datas=my_datas,            # Use collected datas
    hiddenimports=my_hiddenimports, # Use collected hidden imports
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
    [],
    exclude_binaries=True,
    name='speedog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='speedog',
)