"""
文档卡片组件 — 用于卡片视图
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from models import DocumentData
from config import DOC_STATUS_LABELS
from ui.styles import _FONT


class DocumentCard(QWidget):
    """单个文档卡片"""

    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)

    def __init__(self, doc: DocumentData, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setObjectName("DocumentCard")
        self.setFixedSize(280, 160)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        title = QLabel(self.doc.title)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(44)
        layout.addWidget(title)

        if self.doc.doc_no:
            doc_no = QLabel(self.doc.doc_no)
            doc_no.setObjectName("CardMeta")
            doc_no.setStyleSheet(f"color: #2d5aa0; font-size: 11px; font-family: {_FONT};")
            layout.addWidget(doc_no)

        layout.addStretch()

        bottom = QHBoxLayout()

        cat_label = QLabel(self.doc.category_name)
        cat_label.setObjectName("TagLabel")
        cat_label.setFixedHeight(20)
        bottom.addWidget(cat_label)

        bottom.addStretch()

        status_text = DOC_STATUS_LABELS.get(self.doc.status, self.doc.status)
        status_label = QLabel(status_text)
        status_color = {
            "active": "#28a745", "archived": "#6c757d",
            "superseded": "#dc3545", "expired": "#ffc107"
        }.get(self.doc.status, "#666")
        status_label.setStyleSheet(f"color: {status_color}; font-size: 11px; font-weight: bold; font-family: {_FONT};")
        bottom.addWidget(status_label)

        type_label = QLabel(f"  {self.doc.file_type.upper()}")
        type_label.setStyleSheet(f"color: #aaa; font-size: 11px; font-family: {_FONT};")
        bottom.addWidget(type_label)

        layout.addLayout(bottom)

    def mousePressEvent(self, ev):
        self.clicked.emit(self.doc.id)

    def mouseDoubleClickEvent(self, ev):
        self.double_clicked.emit(self.doc.id)
