"""
打分卡条目编辑对话框 — 字段编辑 + 关联制度选择（含自动/人工区分）
"""
from typing import List, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QScrollArea, QWidget, QMessageBox,
)

from core import scorecard_service
from models import ScorecardCheckData


class DocumentPickerDialog(QDialog):
    """制度文档多选器：搜索 + 勾选"""

    def __init__(self, selected_ids: List[int], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择关联制度")
        self.setMinimumSize(560, 460)
        self._selected_ids = list(selected_ids)
        self._setup_ui()
        self._reload("")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("按标题或文号搜索…")
        self._search.returnPressed.connect(lambda: self._reload(self._search.text()))
        search_row.addWidget(self._search, 1)
        btn = QPushButton("搜索")
        btn.clicked.connect(lambda: self._reload(self._search.text()))
        search_row.addWidget(btn)
        layout.addLayout(search_row)

        layout.addWidget(QLabel("勾选需要关联的制度（可多选）："))
        self._list = QListWidget()
        layout.addWidget(self._list, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("DialogBtnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_ok = QPushButton("确定")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

    def _reload(self, keyword: str):
        """刷新列表，保留已勾选状态"""
        self._sync_selection()
        self._list.clear()
        for doc in scorecard_service.find_documents(keyword):
            text = doc.title if not doc.doc_no else f"{doc.title}（{doc.doc_no}）"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, doc.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if doc.id in self._selected_ids else Qt.Unchecked)
            self._list.addItem(item)

    def _sync_selection(self):
        """把当前列表的勾选状态合并进 _selected_ids"""
        for i in range(self._list.count()):
            item = self._list.item(i)
            doc_id = item.data(Qt.UserRole)
            checked = item.checkState() == Qt.Checked
            if checked and doc_id not in self._selected_ids:
                self._selected_ids.append(doc_id)
            elif not checked and doc_id in self._selected_ids:
                self._selected_ids.remove(doc_id)

    def get_selected_ids(self) -> List[int]:
        self._sync_selection()
        return list(self._selected_ids)


class ScorecardCheckDialog(QDialog):
    """检查项编辑：四个文本字段 + 关联制度（区分自动/人工）"""

    def __init__(self, check: ScorecardCheckData, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑打分卡条目")
        self.setMinimumSize(640, 620)
        self._check = check
        self._document_ids = [d.id for d in check.documents]
        self._auto_ids: Set[int] = {d.id for d in check.documents if d.is_auto}
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        form_group = QGroupBox("条目内容")
        form = QFormLayout(form_group)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self._content_edit = QLineEdit(self._check.content)
        self._content_edit.setPlaceholderText("评级内容（必填）")
        form.addRow("评级内容 *", self._content_edit)

        self._points_edit = QTextEdit(self._check.key_points)
        self._points_edit.setMinimumHeight(110)
        form.addRow("评分要点", self._points_edit)

        self._basis_edit = QTextEdit(self._check.regulation_basis)
        self._basis_edit.setMinimumHeight(110)
        form.addRow("监管依据", self._basis_edit)

        self._materials_edit = QTextEdit(self._check.review_materials)
        self._materials_edit.setMinimumHeight(80)
        form.addRow("需调阅材料", self._materials_edit)

        layout.addWidget(form_group)

        # 关联制度
        link_group = QGroupBox("关联制度")
        link_layout = QVBoxLayout(link_group)
        self._link_label = QLabel()
        self._link_label.setWordWrap(True)
        link_layout.addWidget(self._link_label)
        btn_pick = QPushButton("选择关联制度…")
        btn_pick.setFixedWidth(160)
        btn_pick.clicked.connect(self._pick_documents)
        link_layout.addWidget(btn_pick)

        if self._auto_ids:
            btn_clear_auto = QPushButton("清空自动关联（保留手动）")
            btn_clear_auto.setFixedWidth(180)
            btn_clear_auto.setObjectName("ClearAutoLinkBtn")
            btn_clear_auto.clicked.connect(self._clear_auto_links)
            link_layout.addWidget(btn_clear_auto)

        layout.addWidget(link_group)
        self._refresh_link_label()

        layout.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(20, 10, 20, 16)
        btn_row.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.setObjectName("DialogBtnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        outer.addLayout(btn_row)

    def _refresh_link_label(self):
        if not self._document_ids:
            self._link_label.setText("未关联任何制度")
            return
        titles = {d.id: d.title for d in scorecard_service.find_documents("", limit=500)}
        parts = []
        for doc_id in self._document_ids:
            name = titles.get(doc_id, f"#{doc_id}")
            if doc_id in self._auto_ids:
                parts.append(f"{name}【自动】")
            else:
                parts.append(name)
        self._link_label.setText("已关联 %d 份：%s" % (len(parts), "、".join(parts)))

    def _pick_documents(self):
        dlg = DocumentPickerDialog(self._document_ids, parent=self)
        if dlg.exec():
            self._document_ids = dlg.get_selected_ids()
            # 自动关联中被取消勾选的 → 从 _auto_ids 移除（标记为待忽略）
            self._auto_ids = self._auto_ids.intersection(self._document_ids)
            self._refresh_link_label()

    def _clear_auto_links(self):
        """一键移除全部自动关联（保留手动）"""
        self._document_ids = [d for d in self._document_ids if d not in self._auto_ids]
        self._auto_ids.clear()
        self._refresh_link_label()

    def _on_save(self):
        if not self._content_edit.text().strip():
            QMessageBox.warning(self, "提示", "评级内容不能为空")
            return
        self.accept()

    def get_data(self) -> dict:
        # 被移除的自动关联 doc_id（原始 auto_ids 减去当前 document_ids 中仍保留的）
        removed_auto = sorted(self._auto_ids - set(self._document_ids))
        return {
            "content": self._content_edit.text().strip(),
            "key_points": self._points_edit.toPlainText().strip(),
            "regulation_basis": self._basis_edit.toPlainText().strip(),
            "review_materials": self._materials_edit.toPlainText().strip(),
            "document_ids": list(self._document_ids),
            "removed_auto_ids": removed_auto,
        }
