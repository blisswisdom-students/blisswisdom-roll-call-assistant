# -*- mode: python ; coding: utf-8 -*-

import os
import pathlib
import platform
import sys

import tomli

sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None
qt_plugins_path = (os.path.join('.venv', 'Lib', 'site-packages', 'PySide6', 'plugins'), os.path.join('PySide6', 'plugins')) if os.name == 'nt' \
    else (str(list(pathlib.Path().glob('.venv/lib/python*/site-packages/PySide6/Qt/plugins'))[-1]), os.path.join('PySide6', 'Qt', 'plugins'))

a = Analysis(
    [os.path.join('.venv', ('Scripts' if os.name == 'nt' else 'bin'), 'blisswisdom-roll-call-assistant-desktop')],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=[
        qt_plugins_path,
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'main_window.ui'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui')),
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'banner.png'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui')),
        (os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.icns'), os.path.join('blisswisdom_roll_call_assistant_desktop', 'ui')),
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
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'福智學員平臺點名助手-{platform.system()}-v{tomli.load(f)["tool"]["poetry"]["version"]}{".exe" if platform.system() == "Windows" else ""}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='universal2' if platform.system() == 'Darwin' else None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.ico'))
f.close()
if platform.system() == 'Darwin':
    f = open('pyproject.toml', 'rb')
    app = BUNDLE(
        exe,
        name=f'福智學員平臺點名助手-{platform.system()}-v{tomli.load(f)["tool"]["poetry"]["version"]}.app',
        icon=os.path.join('packages', 'blisswisdom_roll_call_assistant_desktop', 'ui', 'icon.icns'),
        bundle_identifier='com.blisswisdom',
        info_plist={
           'NSPrincipalClass': 'NSApplication',
           'NSAppleScriptEnabled': False,
           'CFBundleDocumentTypes': [],
        })
    f.close()
