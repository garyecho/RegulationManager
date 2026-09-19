# PyInstaller runtime hook for PyQt5
# 确保 Qt 插件路径正确（兼容 PyInstaller 5.x / 6.x，onedir 与 onefile）
import os
import sys

if getattr(sys, 'frozen', False):
    # PyInstaller 6.x onedir：资源在 _internal/；onefile：资源在 sys._MEIPASS
    internal_dir = os.path.join(os.path.dirname(sys.executable), '_internal')
    if os.path.isdir(internal_dir):
        base_dir = internal_dir
    else:
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))

    # PyQt5 平台插件路径（按优先级尝试多个位置）
    # QT_QPA_PLATFORM_PLUGIN_PATH 直接指向 platforms/ 目录
    for subdir in ('PyQt5/Qt5', 'PyQt5/Qt'):
        platforms_dir = os.path.join(base_dir, subdir, 'plugins', 'platforms')
        if os.path.isdir(platforms_dir):
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = platforms_dir
            break
