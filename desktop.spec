# -*- mode: python ; coding: utf-8 -*-

import os
import platform
import sys

import tomli

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None
qt_plugins_path = (os.path.join('.venv', 'Lib', 'site-packages', 'PySide6', 'plugins'), os.path.join('PySide6', 'plugins')) if os.name == 'nt' \
    else (os.path.join('.venv', 'lib', 'python3.10', 'site-packages', 'PySide6', 'Qt', 'plugins'), os.path.join('PySide6', 'Qt', 'plugins'))

a = Analysis(
    [os.path.join('.venv', ('Scripts' if os.name == 'nt' else 'bin'), 'blisswisdom-roll-call-assistant-desktop')],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=[
        qt_plugins_path,
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'main_window.ui'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui')),
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'banner.png'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui')),
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.ico'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui'))],
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

f = open('pyproject.toml', 'rb')
if platform.system() == 'Windows':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='福智學員平臺點名助手',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.ico'),
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name=f'福智學員平臺點名助手-{platform.system()}-v{tomli.load(f)["tool"]["poetry"]["version"]}',
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=f'福智學員平臺點名助手-{platform.system()}-v{tomli.load(f)["tool"]["poetry"]["version"]}{".app" if platform.system() == "Darwin" else ""}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.ico'),
    )
f.close()
