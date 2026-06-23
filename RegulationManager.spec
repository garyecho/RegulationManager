# -*- mode: python ; coding: utf-8 -*-
"""
RegulationManager PyInstaller Spec (PyQt5 + Win7 compatible)
"""
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, collect_dynamic_libs

block_cipher = None

# ── 架构感知命名 ──
BUILD_ARCH = os.environ.get("BUILD_ARCH", "")
OUTPUT_NAME = f"RegulationManager_{BUILD_ARCH}" if BUILD_ARCH else "RegulationManager"

# ── Hidden imports ──
hidden_imports = []
hidden_imports += collect_submodules('PyQt5')
hidden_imports += collect_submodules('jieba')
hidden_imports += collect_submodules('fitz')
hidden_imports += collect_submodules('docx')
hidden_imports += collect_submodules('sqlalchemy')

hidden_imports += [
    'PyQt5.sip',
    'PyQt5.QtWidgets',
    'PyQt5.QtGui',
    'PyQt5.QtCore',
    'PyQt5.Qt',
    'sqlite3',
    'encodings',
    'codecs',
]

# ── Data files + Qt 插件 ──
datas = []
datas += collect_data_files('jieba')

# 收集 Qt 插件（关键！包含 platforms、styles、imageformats 等）
datas += collect_data_files('PyQt5', include_py_files=False)

if os.path.exists('resources'):
    datas.append(('resources', 'resources'))

# ── Binaries（Qt 动态库）──
binaries = []
binaries += collect_dynamic_libs('PyQt5')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_qt5.py'],
    excludes=[
        'matplotlib', 'numpy', 'scipy', 'pandas',
        'tkinter', 'PyQt6', 'PIL', 'cv2',
        'IPython', 'jupyter', 'notebook',
        'setuptools', 'pip', 'wheel',
        # 排除不需要的 Qt 模块
        'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
        'PyQt5.Qt3D', 'PyQt5.QtBluetooth', 'PyQt5.QtMultimedia',
        'PyQt5.QtMultimediaWidgets', 'PyQt5.QtNfc', 'PyQt5.QtPositioning',
        'PyQt5.QtLocation', 'PyQt5.QtSensors', 'PyQt5.QtSerialPort',
        'PyQt5.QtWebChannel', 'PyQt5.QtWebEngine', 'PyQt5.QtWebEngineCore',
        'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebSockets',
        'PyQt5.QtHelp', 'PyQt5.QtTest', 'PyQt5.QtDesigner',
        'PyQt5.QtSvg', 'PyQt5.QtXml', 'PyQt5.QtXmlPatterns',
        'PyQt5.QtOpenGL', 'PyQt5.QtSql',
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
    name=OUTPUT_NAME,
)
