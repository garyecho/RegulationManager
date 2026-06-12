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
    """应用主入口"""
    # 日志
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"启动 {config.APP_NAME} v{config.APP_VERSION}")

    # 初始化数据库
    from database.migrations import init_database
    init_database()

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

    # 高 DPI 支持 (Qt5 通过属性启用)
    try:
        app.setAttribute(Qt.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    except AttributeError:
        pass  # Qt 5.14+ 默认启用

    # 创建主窗口
    from ui.main_window import MainWindow
    window = MainWindow()

    # 对主窗口集中加载 QSS（不通过 app.setStyleSheet，避免与 widget 样式冲突）
    qss_path = config.RESOURCES_DIR / "styles" / "light.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            window.setStyleSheet(f.read())

    window.show()

    logger.info("主窗口已显示")

    # 运行事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
