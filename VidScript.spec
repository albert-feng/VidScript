# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = ['yt_dlp', 'customtkinter', 'openai', 'oss2', 'dashscope', 'yaml', 'dotenv']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('dashscope')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# 添加配置文件到打包输出目录
datas += [('.env', '.'), ('prompts.yaml', '.')]
# 尝试添加 ffmpeg (如果存在)
import os
if os.path.exists('bin/ffmpeg.exe'):
    datas += [('bin/ffmpeg.exe', 'bin')]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VidScript',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VidScript',
)

# Post-build: Move config files from _internal to root for easy user access
import shutil
import os

print("Executing post-build file operations...")
dist_root = os.path.join(os.getcwd(), 'dist', 'VidScript')
internal_dir = os.path.join(dist_root, '_internal')
files_to_move = ['.env', 'prompts.yaml']

if os.path.exists(internal_dir):
    for f in files_to_move:
        src = os.path.join(internal_dir, f)
        dst = os.path.join(dist_root, f)
        # Check if source exists (it should be in _internal because we added it to datas)
        if os.path.exists(src):
            print(f"Moving {f} from _internal to root...")
            if os.path.exists(dst):
                os.remove(dst)
            shutil.move(src, dst)
        else:
            print(f"Warning: {f} not found in {internal_dir}")
else:
    print(f"Warning: _internal directory not found at {internal_dir}")

