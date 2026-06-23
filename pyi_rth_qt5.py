# PyInstaller runtime hook for PyQt5
# 确保 Qt 插件路径正确
import os
import sys

if getattr(sys, 'frozen', False):
    # 打包模式：设置 Qt 插件路径
    base_dir = sys._MEIPASS
    
    # PyQt5 插件路径
    qt_plugin_path = os.path.join(base_dir, 'PyQt5', 'Qt5', 'plugins')
    if os.path.exists(qt_plugin_path):
        os.environ['QT_PLUGIN_PATH'] = qt_plugin_path
    
    # 备用路径
    qt_plugin_path2 = os.path.join(base_dir, 'PyQt5', 'Qt', 'plugins')
    if os.path.exists(qt_plugin_path2):
        os.environ['QT_PLUGIN_PATH'] = qt_plugin_path2
