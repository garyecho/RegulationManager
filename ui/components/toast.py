"""
Toast 弹出提示组件 — 深色主题适配
"""
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QWidget

from ui.styles import _FONT


class Toast(QLabel):
    """右下角弹出式 Toast 提示"""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"

    _COLORS = {
        SUCCESS: ("rgba(52,211,153,0.15)", "#34d399", "rgba(52,211,153,0.3)"),
        WARNING: ("rgba(251,191,36,0.15)", "#fbbf24", "rgba(251,191,36,0.3)"),
        ERROR:   ("rgba(248,113,113,0.15)", "#f87171", "rgba(248,113,113,0.3)"),
        INFO:    ("rgba(96,165,250,0.15)", "#60a5fa", "rgba(96,165,250,0.3)"),
    }

    _ICONS = {
        SUCCESS: "✓",
        WARNING: "⚠",
        ERROR:   "✗",
        INFO:    "ℹ",
    }

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setFixedWidth(320)
        self.setWordWrap(True)

    def show_message(self, message: str, msg_type: str = INFO, duration: int = 3000):
        bg, fg, border = self._COLORS.get(msg_type, self._COLORS[self.INFO])
        icon = self._ICONS.get(msg_type, "")

        self.setText(f"  {icon}  {message}")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                font-weight: bold;
                font-family: {_FONT};
            }}
        """)

        self.adjustSize()
        self.setFixedWidth(320)

        if self.parent():
            pw = self.parent().width()
            ph = self.parent().height()
            x = pw - self.width() - 20
            y = ph - self.height() - 40
            self.move(x, y)

        self.show()
        self.raise_()
        QTimer.singleShot(duration, self.hide)

    @staticmethod
    def success(parent, message):
        Toast(parent).show_message(message, Toast.SUCCESS)

    @staticmethod
    def warning(parent, message):
        Toast(parent).show_message(message, Toast.WARNING)

    @staticmethod
    def error(parent, message):
        Toast(parent).show_message(message, Toast.ERROR)

    @staticmethod
    def info(parent, message):
        Toast(parent).show_message(message, Toast.INFO)
