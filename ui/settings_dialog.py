"""
系统设置对话框
"""
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QSlider, QPushButton, QFormLayout, QWidget
)


# 默认字体大小
DEFAULT_FONT_SIZE = 14


def get_settings() -> QSettings:
    """获取 QSettings 实例"""
    return QSettings("RegulationManager", "RegulationManager")


def get_font_size() -> int:
    """读取保存的字体大小"""
    settings = get_settings()
    return settings.value("ui/font_size", DEFAULT_FONT_SIZE, type=int)


def save_font_size(size: int):
    """保存字体大小"""
    settings = get_settings()
    settings.setValue("ui/font_size", size)


def apply_font_size(size: int, app=None):
    """应用字体大小到全局"""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtGui import QFont

    if app is None:
        app = QApplication.instance()
    if app:
        font = app.font()
        font.setPointSize(size)
        app.setFont(font)


class SettingsDialog(QDialog):
    """系统设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._main_window = parent  # 保存主窗口引用
        self.setWindowTitle("系统设置")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._current_size = get_font_size()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── 界面外观分组 ──
        appearance_group = QGroupBox("界面外观")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setSpacing(12)
        appearance_layout.setLabelAlignment(Qt.AlignRight)

        # 字体大小调节
        size_widget = QWidget()
        size_layout = QHBoxLayout(size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(12)

        self._size_slider = QSlider(Qt.Horizontal)
        self._size_slider.setRange(10, 18)
        self._size_slider.setTickPosition(QSlider.TicksBelow)
        self._size_slider.setTickInterval(1)
        self._size_slider.valueChanged.connect(self._on_size_changed)
        size_layout.addWidget(self._size_slider, 1)

        self._size_label = QLabel("14 px")
        self._size_label.setMinimumWidth(50)
        self._size_label.setStyleSheet("font-weight: bold;")
        size_layout.addWidget(self._size_label)

        appearance_layout.addRow("字体大小：", size_widget)

        # 快捷预设按钮
        preset_widget = QWidget()
        preset_layout = QHBoxLayout(preset_widget)
        preset_layout.setContentsMargins(0, 0, 0, 0)
        preset_layout.setSpacing(8)

        for label, size in [("小 (12)", 12), ("中 (14)", 14), ("大 (16)", 16)]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.clicked.connect(lambda _, s=size: self._set_size(s))
            preset_layout.addWidget(btn)

        preset_layout.addStretch()
        appearance_layout.addRow("快捷预设：", preset_widget)

        layout.addWidget(appearance_group)

        # ── 提示信息 ──
        tip_label = QLabel("提示：部分界面需重启后完全生效。")
        tip_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(tip_label)

        layout.addStretch()

        # ── 底部按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_reset = QPushButton("恢复默认")
        btn_reset.setFixedHeight(32)
        btn_reset.clicked.connect(self._reset_default)
        btn_layout.addWidget(btn_reset)

        btn_apply = QPushButton("应用")
        btn_apply.setFixedHeight(32)
        btn_apply.clicked.connect(self._apply_settings)
        btn_layout.addWidget(btn_apply)

        btn_save = QPushButton("保存")
        btn_save.setFixedHeight(32)
        btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _load_settings(self):
        """加载已保存的设置"""
        self._size_slider.setValue(self._current_size)

    def _on_size_changed(self, value: int):
        """字体大小变化时实时预览"""
        self._size_label.setText(f"{value} px")
        self._current_size = value
        # 实时预览：更新应用字体
        apply_font_size(value)
        # 动态更新 QSS
        self._update_qss(value)
        # 刷新表格行高
        self._refresh_table_row_height()

    def _refresh_table_row_height(self):
        """刷新主窗口表格行高"""
        if self._main_window and hasattr(self._main_window, '_doc_panel'):
            self._main_window._doc_panel.refresh_row_height()

    def _update_qss(self, font_size: int):
        """动态更新 QSS 中的字体大小"""
        import config
        import re

        if self._main_window:
            qss_path = config.RESOURCES_DIR / "styles" / "light.qss"
            if qss_path.exists():
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
                # 只替换 font-size 属性中的 16px，不影响 padding/margin 等
                qss_content = re.sub(
                    r'font-size:\s*16px',
                    f'font-size: {font_size}px',
                    qss_content
                )
                self._main_window.setStyleSheet(qss_content)

    def _set_size(self, size: int):
        """设置字体大小（快捷预设）"""
        self._size_slider.setValue(size)

    def _reset_default(self):
        """恢复默认值"""
        self._set_size(DEFAULT_FONT_SIZE)

    def _apply_settings(self):
        """应用设置"""
        save_font_size(self._current_size)
        apply_font_size(self._current_size)

    def _save_and_close(self):
        """保存并关闭"""
        self._apply_settings()
        self.accept()
