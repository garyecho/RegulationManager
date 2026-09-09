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

    # PyQt5 插件路径（按优先级尝试多个位置）
    for subdir in ('PyQt5/Qt5/plugins', 'PyQt5/Qt/plugins'):
        qt_plugin_path = os.path.join(base_dir, subdir)
        if os.path.isdir(qt_plugin_path):
            os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
            break
