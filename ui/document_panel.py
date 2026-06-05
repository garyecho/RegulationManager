"""
文档列表面板 — 表格视图 + 卡片视图 + 分页 + 复选框批量操作
三种模式：manage（管理）、browse（浏览）、recycle（回收站）
"""
from typing import List, Optional, Set

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QStackedWidget, QScrollArea,
    QHeaderView, QAbstractItemView, QGridLayout, QCheckBox
)

from models import DocumentData, SearchResult
from ui.components.card_widget import DocumentCard
from ui.styles import (
    PANEL_TOOLBAR_LIGHT, PANEL_TITLE_LIGHT, PANEL_COUNT_LIGHT,
    PANEL_SORT_LABEL_LIGHT, PANEL_SEPARATOR_LIGHT,
    tool_btn_style, view_btn_style,
    PAGE_BTN_LIGHT, PAGE_LABEL_LIGHT, _FONT,
)

# ── 面板模式常量 ──
MODE_MANAGE = "manage"    # 全部制度 / 分类列表
MODE_BROWSE = "browse"    # 最近使用
MODE_RECYCLE = "recycle"  # 回收站


class DocumentPanel(QWidget):

    document_selected = pyqtSignal(int)
    document_opened = pyqtSignal(int)
    document_deleted = pyqtSignal(int)
    page_changed = pyqtSignal(int)
    view_mode_changed = pyqtSignal(str)
    batch_delete_requested = pyqtSignal(list)
    batch_permanent_delete_requested = pyqtSignal(list)
    batch_restore_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._view_mode = "list"
        self._panel_mode = MODE_MANAGE
        self._current_page = 1
        self._total_pages = 1
        self._documents: List[DocumentData] = []
        self._checked_ids: Set[int] = set()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部工具栏 ──
        toolbar = QWidget()
        toolbar.setStyleSheet(PANEL_TOOLBAR_LIGHT)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)

        self._title_label = QLabel("全部制度")
        self._title_label.setStyleSheet(PANEL_TITLE_LIGHT)
        tb_layout.addWidget(self._title_label)

        self._count_label = QLabel("0 项")
        self._count_label.setStyleSheet(PANEL_COUNT_LIGHT)
        tb_layout.addWidget(self._count_label)
        tb_layout.addStretch()

        # ── 批量操作区（manage + recycle 模式可见）──
        self._batch_widget = QWidget()
        batch_layout = QHBoxLayout(self._batch_widget)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setSpacing(6)

        self._selected_count_label = QLabel("已选 0 项")
        self._selected_count_label.setStyleSheet(
            f"color: #2d5aa0; font-size: 12px; font-weight: bold; font-family: {_FONT};"
        )
        batch_layout.addWidget(self._selected_count_label)

        # manage 模式：批量删除
        self._btn_batch_delete = QPushButton("🗑 批量删除")
        self._btn_batch_delete.setStyleSheet(
            f"QPushButton {{ background: rgba(248,113,113,0.12); color: #f87171; "
            f"border: 1px solid rgba(248,113,113,0.3); border-radius: 6px; "
            f"padding: 4px 12px; font-size: 12px; font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: rgba(248,113,113,0.25); }}"
        )
        self._btn_batch_delete.setFixedHeight(30)
        self._btn_batch_delete.clicked.connect(self._on_batch_delete)
        batch_layout.addWidget(self._btn_batch_delete)

        # recycle 模式：还原
        self._btn_batch_restore = QPushButton("♻️ 还原")
        self._btn_batch_restore.setStyleSheet(
            f"QPushButton {{ background: rgba(52,211,153,0.12); color: #34d399; "
            f"border: 1px solid rgba(52,211,153,0.3); border-radius: 6px; "
            f"padding: 4px 12px; font-size: 12px; font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: rgba(52,211,153,0.25); }}"
        )
        self._btn_batch_restore.setFixedHeight(30)
        self._btn_batch_restore.clicked.connect(self._on_batch_restore)
        batch_layout.addWidget(self._btn_batch_restore)

        # recycle 模式：彻底删除
        self._btn_batch_permanent = QPushButton("⚠️ 彻底删除")
        self._btn_batch_permanent.setStyleSheet(
            f"QPushButton {{ background: #dc3545; color: #fff; "
            f"border: none; border-radius: 6px; "
            f"padding: 4px 14px; font-size: 12px; font-weight: bold; font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: #c82333; }}"
        )
        self._btn_batch_permanent.setFixedHeight(30)
        self._btn_batch_permanent.clicked.connect(self._on_batch_permanent_delete)
        batch_layout.addWidget(self._btn_batch_permanent)

        tb_layout.addWidget(self._batch_widget)
        self._batch_widget.hide()

        # ── 排序 + 视图切换 + 单个删除（所有模式共用容器，按模式显隐）──
        self._sort_label = QLabel("排序：")
        self._sort_label.setStyleSheet(PANEL_SORT_LABEL_LIGHT)
        tb_layout.addWidget(self._sort_label)

        btn_newest = QPushButton("最新更新")
        btn_newest.setStyleSheet(tool_btn_style(True))
        btn_newest.clicked.connect(lambda: self._on_sort("updated_at"))
        tb_layout.addWidget(btn_newest)

        btn_name = QPushButton("按名称")
        btn_name.setStyleSheet(tool_btn_style(False))
        btn_name.clicked.connect(lambda: self._on_sort("title"))
        tb_layout.addWidget(btn_name)

        self._sep1 = QLabel("|")
        self._sep1.setStyleSheet(PANEL_SEPARATOR_LIGHT)
        tb_layout.addWidget(self._sep1)

        self._btn_list = QPushButton("☰")
        self._btn_list.setToolTip("列表视图")
        self._btn_list.setStyleSheet(view_btn_style(True))
        self._btn_list.setFixedSize(32, 32)
        self._btn_list.clicked.connect(lambda: self._switch_view("list"))
        tb_layout.addWidget(self._btn_list)

        self._btn_card = QPushButton("▦")
        self._btn_card.setToolTip("卡片视图")
        self._btn_card.setStyleSheet(view_btn_style(False))
        self._btn_card.setFixedSize(32, 32)
        self._btn_card.clicked.connect(lambda: self._switch_view("card"))
        tb_layout.addWidget(self._btn_card)

        self._sep2 = QLabel("|")
        self._sep2.setStyleSheet(PANEL_SEPARATOR_LIGHT)
        tb_layout.addWidget(self._sep2)

        self._btn_delete = QPushButton("🗑 删除")
        self._btn_delete.setStyleSheet(
            f"QPushButton {{ background: transparent; color: #f87171; "
            f"border: 1px solid transparent; border-radius: 6px; "
            f"padding: 4px 12px; font-size: 12px; font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: rgba(248,113,113,0.12); border-color: #f87171; }}"
        )
        self._btn_delete.setFixedHeight(32)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        tb_layout.addWidget(self._btn_delete)

        layout.addWidget(toolbar)

        # ── 全选栏 ──
        self._select_all_bar = QWidget()
        self._select_all_bar.setStyleSheet(
            f"background: #162032; border-bottom: 1px solid #334155;"
        )
        sa_layout = QHBoxLayout(self._select_all_bar)
        sa_layout.setContentsMargins(16, 4, 16, 4)

        self._select_all_cb = QCheckBox("全选")
        self._select_all_cb.setStyleSheet(
            f"QCheckBox {{ font-size: 12px; color: #94a3b8; font-family: {_FONT}; "
            f"spacing: 6px; }} "
            f"QCheckBox::indicator {{ width: 16px; height: 16px; }}"
        )
        self._select_all_cb.stateChanged.connect(self._on_select_all_changed)
        sa_layout.addWidget(self._select_all_cb)
        sa_layout.addStretch()

        self._select_all_bar.hide()
        layout.addWidget(self._select_all_bar)

        # ── 内容区 ──
        self._stack = QStackedWidget()
        self._table = self._create_table()
        self._stack.addWidget(self._table)

        self._card_scroll = QScrollArea()
        self._card_scroll.setWidgetResizable(True)
        self._card_widget = QWidget()
        self._card_layout = QGridLayout(self._card_widget)
        self._card_layout.setSpacing(12)
        self._card_layout.setContentsMargins(16, 16, 16, 16)
        self._card_scroll.setWidget(self._card_widget)
        self._stack.addWidget(self._card_scroll)
        layout.addWidget(self._stack, 1)

        # ── 分页栏 ──
        page_bar = QWidget()
        page_bar.setStyleSheet(PANEL_TOOLBAR_LIGHT)
        page_layout = QHBoxLayout(page_bar)
        page_layout.setContentsMargins(16, 4, 16, 4)

        self._btn_prev = QPushButton("◀ 上一页")
        self._btn_prev.setStyleSheet(PAGE_BTN_LIGHT)
        self._btn_prev.clicked.connect(lambda: self._goto_page(self._current_page - 1))
        page_layout.addWidget(self._btn_prev)

        self._page_label = QLabel("第 1 / 1 页")
        self._page_label.setStyleSheet(PAGE_LABEL_LIGHT)
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self._page_label, 1)

        self._btn_next = QPushButton("下一页 ▶")
        self._btn_next.setStyleSheet(PAGE_BTN_LIGHT)
        self._btn_next.clicked.connect(lambda: self._goto_page(self._current_page + 1))
        page_layout.addWidget(self._btn_next)
        layout.addWidget(page_bar)

    # ── 表格创建 ──

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["✓", "标题", "文号", "分类", "状态", "部门", "更新时间"]
        )
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 7):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.itemClicked.connect(self._on_table_clicked)
        table.itemDoubleClicked.connect(self._on_table_double_clicked)
        return table

    # ── 模式切换 ──

    def set_panel_mode(self, mode: str):
        """设置面板模式：manage / browse / recycle"""
        self._panel_mode = mode
        # 清空勾选
        self._checked_ids.clear()
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(False)
        self._select_all_cb.blockSignals(False)
        self._batch_widget.hide()

        is_manage = (mode == MODE_MANAGE)
        is_browse = (mode == MODE_BROWSE)
        is_recycle = (mode == MODE_RECYCLE)

        # 复选框列显隐
        self._table.setColumnHidden(0, is_browse)
        if is_browse:
            self._table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )
        else:
            self._table.setColumnWidth(0, 40)
            self._table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.Fixed
            )
            self._table.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch
            )

        # 全选栏
        self._select_all_bar.setVisible(not is_browse and len(self._documents) > 0)

        # 排序/视图切换（browse + manage 可见）
        self._sort_label.setVisible(not is_recycle)
        self._btn_list.setVisible(not is_recycle)
        self._btn_card.setVisible(not is_recycle)
        self._sep1.setVisible(not is_recycle)

        # 单个删除按钮（仅 manage 可见）
        self._btn_delete.setVisible(is_manage)
        self._sep2.setVisible(is_manage)

        # 批量按钮按模式区分（在 _update_batch_ui 中控制）
        self._update_batch_ui()

    # ── 视图切换 ──

    def _switch_view(self, mode: str):
        self._view_mode = mode
        if mode == "list":
            self._stack.setCurrentIndex(0)
            self._btn_list.setStyleSheet(view_btn_style(True))
            self._btn_card.setStyleSheet(view_btn_style(False))
            if self._panel_mode != MODE_BROWSE:
                self._select_all_bar.setVisible(len(self._documents) > 0)
        else:
            self._stack.setCurrentIndex(1)
            self._btn_list.setStyleSheet(view_btn_style(False))
            self._btn_card.setStyleSheet(view_btn_style(True))
            self._select_all_bar.hide()
            self._rebuild_cards()
        self.view_mode_changed.emit(mode)

    def _on_sort(self, field: str):
        self._current_sort = field
        self.page_changed.emit(self._current_page)

    def _goto_page(self, page: int):
        if 1 <= page <= self._total_pages:
            self._current_page = page
            self.page_changed.emit(page)

    # ── 复选框逻辑 ──

    def _on_checkbox_changed(self, state: int, doc_id: int):
        if state == Qt.CheckState.Checked.value:
            self._checked_ids.add(doc_id)
        else:
            self._checked_ids.discard(doc_id)
        self._update_batch_ui()

    def _on_select_all_changed(self, state: int):
        checked = (state == Qt.CheckState.Checked.value)
        if checked:
            for doc in self._documents:
                self._checked_ids.add(doc.id)
        else:
            self._checked_ids.clear()
        table = self._table
        table.blockSignals(True)
        for row in range(table.rowCount()):
            cb_widget = table.cellWidget(row, 0)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb:
                    cb.setChecked(checked)
        table.blockSignals(False)
        self._update_batch_ui()

    def _update_batch_ui(self):
        count = len(self._checked_ids)
        if count > 0:
            self._selected_count_label.setText(f"已选 {count} 项")
            self._batch_widget.show()
            self._btn_batch_delete.setVisible(self._panel_mode == MODE_MANAGE)
            self._btn_batch_restore.setVisible(self._panel_mode == MODE_RECYCLE)
            self._btn_batch_permanent.setVisible(self._panel_mode == MODE_RECYCLE)
        else:
            self._batch_widget.hide()

    # ── 批量操作信号 ──

    def _on_batch_delete(self):
        ids = list(self._checked_ids)
        if ids:
            self.batch_delete_requested.emit(ids)

    def _on_batch_restore(self):
        ids = list(self._checked_ids)
        if ids:
            self.batch_restore_requested.emit(ids)

    def _on_batch_permanent_delete(self):
        ids = list(self._checked_ids)
        if ids:
            self.batch_permanent_delete_requested.emit(ids)

    # ── 表格事件 ──

    def _on_table_clicked(self, item):
        row = item.row()
        if 0 <= row < len(self._documents):
            self.document_selected.emit(self._documents[row].id)

    def _on_table_double_clicked(self, item):
        row = item.row()
        if 0 <= row < len(self._documents):
            self.document_opened.emit(self._documents[row].id)

    # ── 公共接口 ──

    def set_title(self, title: str):
        self._title_label.setText(title)

    def load_result(self, result: SearchResult):
        self._documents = result.documents
        self._current_page = result.page
        self._total_pages = result.total_pages
        self._count_label.setText(f"{result.total} 项")
        # 清空勾选
        self._checked_ids.clear()
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(False)
        self._select_all_cb.blockSignals(False)
        self._batch_widget.hide()
        self._update_table()
        if self._view_mode == "card":
            self._rebuild_cards()
        self._update_pagination()
        # 全选栏显隐
        show_sa = (self._panel_mode != MODE_BROWSE
                   and self._view_mode == "list"
                   and len(self._documents) > 0)
        self._select_all_bar.setVisible(show_sa)

    def _update_table(self):
        table = self._table
        table.setRowCount(len(self._documents))
        table.blockSignals(True)
        from config import DOC_STATUS_LABELS
        for row, doc in enumerate(self._documents):
            # 复选框列
            cb = QCheckBox()
            cb.setStyleSheet(
                f"QCheckBox {{ spacing: 0px; }} "
                f"QCheckBox::indicator {{ width: 18px; height: 18px; }}"
            )
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(row, 0, cb_widget)
            cb.stateChanged.connect(
                lambda state, did=doc.id: self._on_checkbox_changed(state, did)
            )

            # 数据列
            table.setItem(row, 1, QTableWidgetItem(doc.title))
            table.setItem(row, 2, QTableWidgetItem(doc.doc_no))
            table.setItem(row, 3, QTableWidgetItem(doc.category_name))
            status_text = DOC_STATUS_LABELS.get(doc.status, doc.status)
            table.setItem(row, 4, QTableWidgetItem(status_text))
            table.setItem(row, 5, QTableWidgetItem(doc.department))
            table.setItem(row, 6, QTableWidgetItem(
                doc.updated_at[:10] if len(doc.updated_at) >= 10 else doc.updated_at
            ))
        table.blockSignals(False)
        # 根据当前模式隐藏复选框列
        table.setColumnHidden(0, self._panel_mode == MODE_BROWSE)

    def _rebuild_cards(self):
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cols = max(1, (self._card_scroll.width() - 32) // 300)
        for i, doc in enumerate(self._documents):
            card = DocumentCard(doc)
            card.clicked.connect(lambda doc_id=doc.id: self.document_selected.emit(doc_id))
            card.double_clicked.connect(lambda doc_id=doc.id: self.document_opened.emit(doc_id))
            row, col = divmod(i, cols)
            self._card_layout.addWidget(card, row, col)

    def _update_pagination(self):
        self._page_label.setText(f"第 {self._current_page} / {self._total_pages} 页")
        self._btn_prev.setEnabled(self._current_page > 1)
        self._btn_next.setEnabled(self._current_page < self._total_pages)

    def get_selected_doc_id(self) -> Optional[int]:
        if self._view_mode == "list":
            rows = self._table.selectionModel().selectedRows()
            if rows:
                row = rows[0].row()
                if 0 <= row < len(self._documents):
                    return self._documents[row].id
        return None

    def _on_delete_clicked(self):
        doc_id = self.get_selected_doc_id()
        if doc_id is not None:
            self.document_deleted.emit(doc_id)
