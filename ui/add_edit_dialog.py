"""
新增/编辑制度对话框
"""
from typing import Optional, List
from pathlib import Path

from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QWheelEvent
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QComboBox, QDateEdit,
    QPushButton, QLabel, QFileDialog, QGroupBox, QMessageBox,
    QScrollArea, QWidget
)

from models import DocumentData, CategoryData
from config import DOC_STATUS_LABELS
from ui.components.tag_input import TagInput
from ui.styles import _FONT
from utils.text_parser import extract_doc_no, extract_title_and_doc_no


# ── 自定义控件：只有点击获得焦点后才响应滚轮 ──

class ClickFocusComboBox(QComboBox):
    """分类/状态下拉框：鼠标悬停时滚轮无效，需先点击"""
    def wheelEvent(self, event: QWheelEvent):
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class ClickFocusDateEdit(QDateEdit):
    """日期选择器：鼠标悬停时滚轮无效，需先点击"""
    def wheelEvent(self, event: QWheelEvent):
        if not self.hasFocus():
            event.ignore()
            return
        super().wheelEvent(event)


class AddEditDialog(QDialog):
    """新增/编辑制度对话框"""

    def __init__(self, categories: List[CategoryData], doc: Optional[DocumentData] = None, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.categories = categories
        self.selected_file: Optional[str] = None
        self._auto_filled_doc_no = False
        self._title_timer = QTimer(self)
        self._title_timer.setSingleShot(True)
        self._title_timer.setInterval(800)
        self._title_timer.timeout.connect(self._on_title_delayed_extract)

        self.setWindowTitle("编辑制度" if doc else "新增制度")
        self.setMinimumWidth(650)
        self.setMinimumHeight(600)
        self.resize(700, 700)
        self._setup_ui()
        if doc:
            self._populate(doc)
            self._file_group.hide()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # ── 文件选择区 ──
        self._file_group = QGroupBox("文件")
        file_layout = QHBoxLayout(self._file_group)

        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("FileLabelDefault")
        file_layout.addWidget(self._file_label, 1)

        btn_browse = QPushButton("选择文件...")
        btn_browse.setObjectName("DialogBtnSecondary")
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(btn_browse)
        layout.addWidget(self._file_group)

        # ── 基本信息 ──
        info_group = QGroupBox("基本信息")
        form = QFormLayout(info_group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        # 标题
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("制度标题（必填）")
        self._title_edit.textChanged.connect(self._on_title_changed)
        form.addRow("标题 *", self._title_edit)

        # 文号 + 识别按钮
        docno_row = QWidget()
        docno_layout = QHBoxLayout(docno_row)
        docno_layout.setContentsMargins(0, 0, 0, 0)
        docno_layout.setSpacing(6)

        self._docno_edit = QLineEdit()
        self._docno_edit.setPlaceholderText("如：银监发〔2014〕40号")
        docno_layout.addWidget(self._docno_edit, 1)

        self._btn_re_extract = QPushButton("🔍 识别")
        self._btn_re_extract.setObjectName("ExtractBtn")
        self._btn_re_extract.setFixedHeight(30)
        self._btn_re_extract.clicked.connect(self._manual_extract)
        docno_layout.addWidget(self._btn_re_extract)

        self._extract_hint = QLabel("")
        self._extract_hint.setStyleSheet(f"color: #34d399; font-size: 11px; font-family: {_FONT};")
        docno_layout.addWidget(self._extract_hint)
        self._extract_hint.hide()

        form.addRow("文号", docno_row)

        # 版本号
        self._version_edit = QLineEdit("1")
        form.addRow("版本号", self._version_edit)

        # 分类 — 使用自定义下拉框
        self._category_combo = ClickFocusComboBox()
        for cat in self.categories:
            self._category_combo.addItem(cat.name, cat.id)
        self._category_combo.setFocusPolicy(Qt.ClickFocus)
        form.addRow("分类 *", self._category_combo)

        # 状态 — 使用自定义下拉框
        self._status_combo = ClickFocusComboBox()
        for value, label in DOC_STATUS_LABELS.items():
            self._status_combo.addItem(label, value)
        self._status_combo.setFocusPolicy(Qt.ClickFocus)
        form.addRow("状态", self._status_combo)
        layout.addWidget(info_group)

        # ── 详细信息 ──
        detail_group = QGroupBox("详细信息")
        detail_form = QFormLayout(detail_group)
        detail_form.setSpacing(10)
        detail_form.setLabelAlignment(Qt.AlignRight)

        self._org_edit = QLineEdit()
        self._org_edit.setPlaceholderText("如：国家金融监督管理总局")
        detail_form.addRow("发文机关", self._org_edit)

        self._dept_edit = QLineEdit()
        self._dept_edit.setPlaceholderText("如：风险管理部")
        detail_form.addRow("责任部门", self._dept_edit)

        # 生效日期 — 使用自定义日期控件
        self._eff_date = ClickFocusDateEdit()
        self._eff_date.setCalendarPopup(True)
        self._eff_date.setDate(QDate.currentDate())
        self._eff_date.setDisplayFormat("yyyy-MM-dd")
        self._eff_date.setFocusPolicy(Qt.ClickFocus)
        detail_form.addRow("生效日期", self._eff_date)

        # 废止日期 — 使用自定义日期控件
        self._exp_date = ClickFocusDateEdit()
        self._exp_date.setCalendarPopup(True)
        self._exp_date.setDisplayFormat("yyyy-MM-dd")
        self._exp_date.setFocusPolicy(Qt.ClickFocus)
        detail_form.addRow("废止日期", self._exp_date)

        self._tag_input = TagInput()
        detail_form.addRow("标签", self._tag_input)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("备注说明...")
        self._desc_edit.setMinimumHeight(60)
        self._desc_edit.setMaximumHeight(100)
        detail_form.addRow("备注", self._desc_edit)
        layout.addWidget(detail_group)

        # ── 按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("DialogBtnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._on_save)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        scroll.setWidget(scroll_content)
        outer_layout.addWidget(scroll)

    # ── 文号识别逻辑 ──

    def _on_title_changed(self, text: str):
        if text.strip():
            self._title_timer.start()
        else:
            self._title_timer.stop()
            self._hide_extract_hint()

    def _on_title_delayed_extract(self):
        title = self._title_edit.text().strip()
        if not title:
            return
        if self._docno_edit.text().strip() == "" or self._auto_filled_doc_no:
            self._do_extract(title, auto=True)

    def _manual_extract(self):
        title = self._title_edit.text().strip()
        if not title:
            self._show_extract_hint("请先输入标题", is_error=True)
            return
        self._do_extract(title, auto=False)

    def _do_extract(self, title: str, auto: bool):
        doc_no = extract_doc_no(title)
        if doc_no:
            self._docno_edit.setText(doc_no)
            self._auto_filled_doc_no = True
            self._show_extract_hint("✓ 已自动识别文号" if auto else "✓ 已识别")
        else:
            if not auto:
                self._show_extract_hint("未识别到文号", is_error=True)
                self._auto_filled_doc_no = False
            else:
                self._auto_filled_doc_no = False

    def _show_extract_hint(self, msg: str, is_error: bool = False):
        color = "#f87171" if is_error else "#34d399"
        self._extract_hint.setStyleSheet(f"color: {color}; font-size: 11px; font-family: {_FONT};")
        self._extract_hint.setText(msg)
        self._extract_hint.show()
        QTimer.singleShot(3000, self._hide_extract_hint)

    def _hide_extract_hint(self):
        self._extract_hint.hide()

    # ── 文件选择 ──

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择制度文件", "",
            "文档文件 (*.doc *.docx *.pdf);;所有文件 (*)"
        )
        if path:
            self.selected_file = path
            name = Path(path).name
            self._file_label.setText(name)
            self._file_label.setObjectName("FileLabelSelected")

            title_from_file, doc_no_from_file = extract_title_and_doc_no(Path(path).stem)
            if not self._title_edit.text().strip():
                self._title_edit.setText(title_from_file)
            if not self._docno_edit.text().strip() and doc_no_from_file:
                self._docno_edit.setText(doc_no_from_file)
                self._auto_filled_doc_no = True
                self._show_extract_hint("✓ 从文件名识别")

    # ── 编辑模式填充 ──

    def _populate(self, doc: DocumentData):
        self._title_edit.setText(doc.title)
        self._docno_edit.setText(doc.doc_no)
        self._version_edit.setText(doc.version_no)
        self._org_edit.setText(doc.issuing_org)
        self._dept_edit.setText(doc.department)
        self._desc_edit.setPlainText(doc.description)
        self._file_label.setText(doc.original_name)
        self._file_label.setObjectName("FileLabelSelected")

        for i in range(self._category_combo.count()):
            if self._category_combo.itemData(i) == doc.category_id:
                self._category_combo.setCurrentIndex(i)
                break
        for i in range(self._status_combo.count()):
            if self._status_combo.itemData(i) == doc.status:
                self._status_combo.setCurrentIndex(i)
                break
        if doc.tags:
            self._tag_input.set_tags(doc.tags)

    # ── 保存 ──

    def _on_save(self):
        if not self._title_edit.text().strip():
            QMessageBox.warning(self, "提示", "请输入制度标题")
            return
        if self._category_combo.currentData() is None:
            QMessageBox.warning(self, "提示", "请选择分类")
            return
        if not self.doc and not self.selected_file:
            QMessageBox.warning(self, "提示", "请选择文件")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "title": self._title_edit.text().strip(),
            "doc_no": self._docno_edit.text().strip(),
            "version_no": self._version_edit.text().strip() or "1",
            "category_id": self._category_combo.currentData(),
            "status": self._status_combo.currentData(),
            "issuing_org": self._org_edit.text().strip(),
            "department": self._dept_edit.text().strip(),
            "effective_date": self._eff_date.date().toString("yyyy-MM-dd"),
            "expiry_date": self._exp_date.date().toString("yyyy-MM-dd"),
            "tags": self._tag_input.get_tags(),
            "description": self._desc_edit.toPlainText().strip(),
            "file_path": self.selected_file,
        }
