"""
制度汇编管理系统 — 入口文件
"""
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
    if os.environ.get("XDG_SESSION_TYPE") == "wayland":
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

    # 定位 Qt 平台插件：uv 托管 Python 下 Qt 默认按解释器目录找插件，
    # 显式加入 PyQt5 wheel 自带的插件目录（打包模式由 pyi_rth_qt5.py 处理）。
    import PyQt5
    _plugins_dir = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
    if _plugins_dir.exists():
        QtCore.QCoreApplication.addLibraryPath(str(_plugins_dir))

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)
    app.setApplicationVersion(config.APP_VERSION)
    app.setOrganizationName("RegulationManager")

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
    from ui.settings_dialog import get_font_size
    saved_size = get_font_size()
    font.setPointSize(saved_size)
    app.setFont(font)

    # 创建主窗口
    from ui.main_window import MainWindow
    window = MainWindow()

    # 对主窗口集中加载 QSS（动态替换字体大小）
    qss_path = config.RESOURCES_DIR / "styles" / "light.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            qss_content = f.read()
        # 替换 QSS 中的字体大小为用户设置值
        qss_content = qss_content.replace("16px", f"{saved_size}px")
        window.setStyleSheet(qss_content)

    window.show()

    logger.info("主窗口已显示")

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
