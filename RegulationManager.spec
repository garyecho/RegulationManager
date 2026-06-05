# -*- mode: python ; coding: utf-8 -*-
"""
RegulationManager PyInstaller Spec
Usage: pyinstaller RegulationManager.spec
"""
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# ── Hidden imports ──
hidden_imports = []
hidden_imports += collect_submodules('PyQt6')
hidden_imports += collect_submodules('whoosh')
hidden_imports += collect_submodules('jieba')
hidden_imports += collect_submodules('fitz')
hidden_imports += collect_submodules('docx')
hidden_imports += collect_submodules('sqlalchemy')

hidden_imports += [
    'PyQt6.sip',
    'sqlite3',
    'encodings',
    'codecs',
]

# ── Data files ──
datas = []
# jieba dict
jieba_datas = collect_data_files('jieba')
datas += jieba_datas

# resources folder
if os.path.exists('resources'):
    datas.append(('resources', 'resources'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'tkinter', 'PyQt5', 'PIL', 'cv2',
        'IPython', 'jupyter', 'notebook',
        'setuptools', 'pip', 'wheel',
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RegulationManager',
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
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RegulationManager',
)
