# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Chess.app (macOS)
Usage: pyinstaller chess.spec
"""

block_cipher = None

a = Analysis(
    ['chess_game.py'],
    pathex=[],
    binaries=[],
    datas=[('chess_engine.py', '.')],
    hiddenimports=['tkinter', 'tkinter.messagebox', 'chess_engine'],
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
    name='Chess',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Chess',
)

app = BUNDLE(
    coll,
    name='Chess.app',
    icon=None,           # set to 'chess.icns' if you have an icon file
    bundle_identifier='com.chess.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1',
        'CFBundleName': 'Chess',
        'CFBundleDisplayName': 'Chess',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHumanReadableCopyright': '© 2024 Chess App',
    },
)
