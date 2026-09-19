"""
制度汇编管理系统 — 入口文件
"""
# --- FTS5 兼容性：优先使用 pysqlite3-binary 自带的新版 SQLite（含 FTS5） ---
# 银河麒麟 v10 SP1 等系统的自带 Python/SQLite 较旧，未编译 FTS5 扩展。
# pysqlite3-binary 打包了最新 SQLite 的预编译二进制，开箱即用。
try:
    __import__('pysqlite3')
    import sys as _sys
    _sys.modules['sqlite3'] = _sys.modules.pop('pysqlite3')
except ImportError:
    pass
# --- END FTS5 兼容性 ---

import sys
import logging
from pathlib import Path

# 添加项目根目录到 sys.path
APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontDatabase

import config


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ]
    )


def main():
    # 日志配置
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"启动 {config.APP_NAME} v{config.APP_VERSION}")

    # 抑制 Qt 剪贴板警告（WSL 环境下常见）
    import os
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.mime=false"

    # Wayland 会话下 Qt5 默认选 xcb（XWayland），部分机器会段错误(退出码139)；
    # 未手动指定平台时切到 wayland 后端（X11 / 无该环境变量时不受影响）。
    # 打包模式下强制 xcb（打包的 Qt5 不含 wayland 插件）。
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
        if getattr(sys, 'frozen', False):
            os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
        else:
            os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

    # 初始化数据库
    from database.migrations import init_database
    init_database()

    # 高 DPI 支持 (必须在 QApplication 创建之前设置)
    import PyQt5.QtCore as QtCore
    try:
        QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass  # Qt 5.14+ 默认启用

    # 定位 Qt 平台插件
    # 开发模式：手动加入 PyQt5 wheel 的插件目录
    # 打包模式：在 QApplication 创建之前显式设置 QT_QPA_PLATFORM_PLUGIN_PATH
    if getattr(sys, 'frozen', False):
        _internal = Path(sys.executable).parent / "_internal"
        for subdir in ('PyQt5/Qt5', 'PyQt5/Qt'):
            _platforms = _internal / subdir / 'plugins' / 'platforms'
            if _platforms.is_dir():
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(_platforms)
                break
    else:
        import PyQt5
        _plugins_dir = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
        if _plugins_dir.exists():
            QtCore.QCoreApplication.addLibraryPath(str(_plugins_dir))

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("RegulationManager")

    # 设置应用图标（任务栏/窗口标题栏/桌面图标）
    from PyQt5.QtGui import QIcon
    _icon_dir = APP_DIR / "resources" / "icons"
    if getattr(sys, 'frozen', False):
        _internal = Path(sys.executable).parent / "_internal"
        _icon_path = _internal / "resources" / "icons" / "app_icon.ico"
        if not _icon_path.exists():
            _icon_path = _internal / "resources" / "icons" / "regulation_manager.png"
        if not _icon_path.exists():
            _icon_path = Path(sys.executable).parent / "resources" / "icons" / "app_icon.ico"
        if not _icon_path.exists():
            _icon_path = _icon_dir / "regulation_manager.png"
    else:
        _icon_path = _icon_dir / "regulation_manager.png"
    if _icon_path.exists():
        app.setWindowIcon(QIcon(str(_icon_path)))

    # 设置全局中文字体（按优先级检测可用字体）
    available = QFontDatabase().families()
    preferred_fonts = ["Microsoft YaHei", "Microsoft YaHei UI", "SimHei",
                       "DengXian", "Arial Unicode MS", "Noto Sans CJK SC",
                       "WenQuanYi Micro Hei", "PingFang SC"]
    chosen = "Microsoft YaHei"  # 最终兜底
    for f in preferred_fonts:
        if f in available:
            chosen = f
            break

    font = QFont(chosen)
    font.setPointSize(16)
    font.setHintingPreference(QFont.PreferFullHinting)
    font.setStyleStrategy(
        QFont.PreferAntialias | QFont.PreferQuality
    )
    app.setFont(font)

    # 应用用户保存的字体大小设置
    from ui.settings_dialog import get_font_size, get_theme, load_qss_content
    saved_size = get_font_size()
    font.setPointSize(saved_size)
    app.setFont(font)

    # 创建主窗口
    from ui.main_window import MainWindow
    window = MainWindow()

    # 对主窗口集中加载 QSS（根据主题 + 字体大小）
    current_theme = get_theme()
    qss_content = load_qss_content(current_theme, saved_size)
    if qss_content:
        window.setStyleSheet(qss_content)

    window.show()

    logger.info("主窗口已显示")

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
