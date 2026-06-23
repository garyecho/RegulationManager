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
        if not self.keyword or not text:
            return text
        import re
        escaped_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        escaped_kw = self.keyword.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        pattern = re.compile(re.escape(escaped_kw), re.IGNORECASE)
        return pattern.sub(
            f'<span style="background-color:#FFEB3B;color:#333;padding:1px 3px;border-radius:2px">{escaped_kw}</span>',
            escaped_text
        )

    def _setup_ui(self):
        from ui.settings_dialog import get_font_size
        cur_size = get_font_size()
        small_size = max(10, cur_size - 3)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        # 标题（支持高亮）
        title_html = f"<div style='font-size:{cur_size}px'>{self._highlight(self.doc.title)}</div>"
        title = QLabel()
        title.setTextFormat(Qt.RichText)
        title.setText(title_html)
        title.setObjectName("CardTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(36)
        layout.addWidget(title)

        # 搜索摘要（如果有）
        if self.doc.snippet:
            snippet_html = f"<div style='color:#666;font-size:{small_size}px'>{self._highlight(self.doc.snippet[:80])}</div>"
            snippet_label = QLabel()
            snippet_label.setTextFormat(Qt.RichText)
            snippet_label.setText(snippet_html)
            snippet_label.setWordWrap(True)
            snippet_label.setMaximumHeight(32)
            layout.addWidget(snippet_label)

        # 文号
        if self.doc.doc_no:
            doc_no = QLabel(self.doc.doc_no)
            doc_no.setObjectName("CardMeta")
            doc_no.setStyleSheet(f"color: #2d5aa0; font-size: {small_size}px; font-family: {_FONT};")
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
        status_label.setStyleSheet(f"color: {status_color}; font-size: {small_size}px; font-weight: bold; font-family: {_FONT};")
        bottom.addWidget(status_label)

        type_label = QLabel(f"  {self.doc.file_type.upper()}")
        type_label.setStyleSheet(f"color: #aaa; font-size: {small_size}px; font-family: {_FONT};")
        bottom.addWidget(type_label)

        layout.addLayout(bottom)

    def mousePressEvent(self, ev):
        self.clicked.emit(self.doc.id)

    def mouseDoubleClickEvent(self, ev):
        self.double_clicked.emit(self.doc.id)
