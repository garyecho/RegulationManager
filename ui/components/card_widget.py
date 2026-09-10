"""
文档卡片组件 — 用于卡片视图
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from models import DocumentData
from config import DOC_STATUS_LABELS
from utils.text_utils import highlight_text


class DocumentCard(QWidget):
    """单个文档卡片"""

    clicked = pyqtSignal(int)
    double_clicked = pyqtSignal(int)

    def __init__(self, doc: DocumentData, keyword: str = "", parent=None):
        super().__init__(parent)
        self.doc = doc
        self.keyword = keyword
        self.setObjectName("DocumentCard")
        self.setFixedSize(280, 180)
        self.setCursor(Qt.PointingHandCursor)
        self._setup_ui()

    def _highlight(self, text: str) -> str:
        """关键词黄色背景高亮"""
        return highlight_text(text, self.keyword)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # 标题（支持高亮）
        title = QLabel()
        title.setTextFormat(Qt.RichText)
        title.setText(self._highlight(self.doc.title))
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(36)
        layout.addWidget(title)

        # 搜索摘要（如果有）
        if self.doc.snippet:
            snippet_label = QLabel()
            snippet_label.setTextFormat(Qt.RichText)
            snippet_label.setText(f"<span style='color:#666'>{self._highlight(self.doc.snippet[:80])}</span>")
            snippet_label.setObjectName("CardSnippet")
            snippet_label.setWordWrap(True)
            snippet_label.setMaximumHeight(32)
            layout.addWidget(snippet_label)

        # 文号
        if self.doc.doc_no:
            doc_no = QLabel(self.doc.doc_no)
            doc_no.setObjectName("CardDocNo")
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
        status_label.setObjectName("CardStatus")
        status_color = {
            "active": "#10b981", "archived": "#6c757d",
            "superseded": "#ef4444", "expired": "#f59e0b"
        }.get(self.doc.status, "#666")
        status_label.setStyleSheet(f"color: {status_color};")
        bottom.addWidget(status_label)

        type_label = QLabel(f"  {self.doc.file_type.upper()}")
        type_label.setObjectName("CardFileType")
        bottom.addWidget(type_label)

        layout.addLayout(bottom)

    def mousePressEvent(self, ev):
        self.clicked.emit(self.doc.id)

    def mouseDoubleClickEvent(self, ev):
        self.double_clicked.emit(self.doc.id)
