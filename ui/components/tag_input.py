"""
标签输入控件 — 输入+回车生成标签胶囊
"""
from typing import List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel
)


class TagCapsule(QLabel):
    """单个标签胶囊"""

    removed = pyqtSignal(str)

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.tag_text = text
        self.setObjectName("TagCapsule")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("点击移除标签")

    def mousePressEvent(self, event):
        self.removed.emit(self.tag_text)


class TagInput(QWidget):
    """标签输入控件"""

    tags_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tags: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._tags_container = QWidget()
        self._tags_layout = QHBoxLayout(self._tags_container)
        self._tags_layout.setContentsMargins(0, 0, 0, 0)
        self._tags_layout.setSpacing(4)
        self._tags_layout.setAlignment(Qt.AlignLeft)
        layout.addWidget(self._tags_container)

        self._input = QLineEdit()
        self._input.setPlaceholderText("输入标签后按回车添加...")
        self._input.returnPressed.connect(self._add_tag)
        layout.addWidget(self._input)

    def _add_tag(self):
        text = self._input.text().strip()
        if text and text not in self._tags:
            self._tags.append(text)
            capsule = TagCapsule(text, self._tags_container)
            capsule.removed.connect(self._remove_tag)
            self._tags_layout.addWidget(capsule)
            self._input.clear()
            self.tags_changed.emit(self._tags)

    def _remove_tag(self, tag: str):
        if tag in self._tags:
            self._tags.remove(tag)
            self._rebuild_capsules()
            self.tags_changed.emit(self._tags)

    def _rebuild_capsules(self):
        while self._tags_layout.count():
            item = self._tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for tag in self._tags:
            capsule = TagCapsule(tag, self._tags_container)
            capsule.removed.connect(self._remove_tag)
            self._tags_layout.addWidget(capsule)

    def get_tags(self) -> List[str]:
        return list(self._tags)

    def set_tags(self, tags: List[str]):
        self._tags = list(tags)
        self._rebuild_capsules()

    def clear(self):
        self._tags.clear()
        self._rebuild_capsules()
