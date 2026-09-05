# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Pac-Man.
#
# Build with:  python3 -m PyInstaller pacman.spec --noconfirm
# Output:      dist/pacman/ (standalone, includes Python, pygame and the
#              A-Maze-ing mazegenerator package).

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("mazegenerator")

a = Analysis(
    ["pac-man.py"],
    pathex=[],
    binaries=[],
    datas=[("packaging/INSTRUCTIONS.txt", "packaging")],
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name="pacman",
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pacman",
)