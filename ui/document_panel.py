"""
文档列表面板 — 表格视图 + 卡片视图 + 分页 + 复选框批量操作
三种模式：manage（管理）、browse（浏览）、recycle（回收站）
"""
from typing import List, Optional, Set

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QStackedWidget, QScrollArea,
    QHeaderView, QAbstractItemView, QGridLayout, QCheckBox
)

from models import DocumentData, SearchResult
from config import DOC_STATUS_LABELS
from ui.components.card_widget import DocumentCard
from utils.text_utils import highlight_text

# ── 面板模式常量 ──
MODE_MANAGE = "manage"    # 全部制度 / 分类列表
MODE_BROWSE = "browse"    # 最近使用
MODE_RECYCLE = "recycle"  # 回收站


class ClickableLabel(QLabel):
    """可双击的标签，转发双击事件到父表格"""
    double_clicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)


class DocumentPanel(QWidget):

    document_selected = pyqtSignal(int)
    document_opened = pyqtSignal(int)
    document_deleted = pyqtSignal(int)
    document_edit_requested = pyqtSignal(int)
    page_changed = pyqtSignal(int)
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
        self._current_sort: str = "updated_at"
        self._search_keyword: str = ""
        self._setup_ui()

    def _highlight(self, text: str) -> str:
        """将关键词用黄色背景高亮显示"""
        return highlight_text(text, self._search_keyword)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 顶部工具栏 ──
        toolbar = QWidget()
        toolbar.setObjectName("PanelToolbar")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)

        self._title_label = QLabel("全部制度")
        self._title_label.setObjectName("PanelTitle")
        tb_layout.addWidget(self._title_label)

        self._count_label = QLabel("0 项")
        self._count_label.setObjectName("PanelCount")
        tb_layout.addWidget(self._count_label)
        tb_layout.addStretch()

        # ── 批量操作区（manage + recycle 模式可见）──
        self._batch_widget = QWidget()
        batch_layout = QHBoxLayout(self._batch_widget)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setSpacing(6)

        self._selected_count_label = QLabel("已选 0 项")
        self._selected_count_label.setObjectName("SelectedCount")
        batch_layout.addWidget(self._selected_count_label)

        # manage 模式：批量删除
        self._btn_batch_delete = QPushButton("🗑 批量删除")
        self._btn_batch_delete.setObjectName("BatchDeleteBtn")
        self._btn_batch_delete.setFixedHeight(30)
        self._btn_batch_delete.clicked.connect(self._on_batch_delete)
        batch_layout.addWidget(self._btn_batch_delete)

        # recycle 模式：还原
        self._btn_batch_restore = QPushButton("♻️ 还原")
        self._btn_batch_restore.setObjectName("BatchRestoreBtn")
        self._btn_batch_restore.setFixedHeight(30)
        self._btn_batch_restore.clicked.connect(self._on_batch_restore)
        batch_layout.addWidget(self._btn_batch_restore)

        # recycle 模式：彻底删除
        self._btn_batch_permanent = QPushButton("⚠️ 彻底删除")
        self._btn_batch_permanent.setObjectName("BatchPermanentBtn")
        self._btn_batch_permanent.setFixedHeight(30)
        self._btn_batch_permanent.clicked.connect(self._on_batch_permanent_delete)
        batch_layout.addWidget(self._btn_batch_permanent)

        tb_layout.addWidget(self._batch_widget)
        self._batch_widget.hide()

        # ── 排序 + 视图切换 + 单个删除（所有模式共用容器，按模式显隐）──
        self._sort_label = QLabel("排序：")
        self._sort_label.setObjectName("PanelSortLabel")
        tb_layout.addWidget(self._sort_label)

        btn_newest = QPushButton("最新更新")
        btn_newest.setObjectName("SortBtnActive")
        btn_newest.clicked.connect(lambda: self._on_sort("updated_at"))
        tb_layout.addWidget(btn_newest)

        btn_name = QPushButton("按名称")
        btn_name.setObjectName("SortBtnInactive")
        btn_name.clicked.connect(lambda: self._on_sort("title"))
        tb_layout.addWidget(btn_name)

        self._sep1 = QLabel("|")
        self._sep1.setObjectName("PanelSep")
        tb_layout.addWidget(self._sep1)

        self._btn_list = QPushButton("☰")
        self._btn_list.setToolTip("列表视图")
        self._btn_list.setObjectName("ViewBtnActive")
        self._btn_list.setFixedSize(32, 32)
        self._btn_list.clicked.connect(lambda: self._switch_view("list"))
        tb_layout.addWidget(self._btn_list)

        self._btn_card = QPushButton("▦")
        self._btn_card.setToolTip("卡片视图")
        self._btn_card.setObjectName("ViewBtnInactive")
        self._btn_card.setFixedSize(32, 32)
        self._btn_card.clicked.connect(lambda: self._switch_view("card"))
        tb_layout.addWidget(self._btn_card)

        self._sep2 = QLabel("|")
        self._sep2.setObjectName("PanelSep")
        tb_layout.addWidget(self._sep2)

        self._btn_delete = QPushButton("🗑 删除")
        self._btn_delete.setObjectName("DeleteBtn")
        self._btn_delete.setFixedHeight(32)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        tb_layout.addWidget(self._btn_delete)

        layout.addWidget(toolbar)

        # ── 全选栏 ──
        self._select_all_bar = QWidget()
        self._select_all_bar.setObjectName("SelectAllBar")
        sa_layout = QHBoxLayout(self._select_all_bar)
        sa_layout.setContentsMargins(16, 4, 16, 4)

        self._select_all_cb = QCheckBox("全选")
        self._select_all_cb.setObjectName("SelectAllCheckbox")
        self._select_all_cb.stateChanged.connect(self._on_select_all_changed)
        sa_layout.addWidget(self._select_all_cb)
        sa_layout.addStretch()

        self._select_all_bar.hide()
        layout.addWidget(self._select_all_bar)

        # ── 内容区 ──
        self._stack = QStackedWidget()
        self._table = self._create_table()
        self._stack.addWidget(self._table)

        # 恢复用户上次保存的列宽和顺序（必须在 self._table 赋值之后）
        self._restoring_header = False
        self._restore_header_state()

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
        page_bar.setObjectName("PanelToolbar")
        page_layout = QHBoxLayout(page_bar)
        page_layout.setContentsMargins(16, 4, 16, 4)

        self._btn_prev = QPushButton("◀ 上一页")
        self._btn_prev.setObjectName("PageBtn")
        self._btn_prev.clicked.connect(lambda: self._goto_page(self._current_page - 1))
        page_layout.addWidget(self._btn_prev)

        self._page_label = QLabel("第 1 / 1 页")
        self._page_label.setObjectName("PageLabel")
        self._page_label.setAlignment(Qt.AlignCenter)
        page_layout.addWidget(self._page_label, 1)

        self._btn_next = QPushButton("下一页 ▶")
        self._btn_next.setObjectName("PageBtn")
        self._btn_next.clicked.connect(lambda: self._goto_page(self._current_page + 1))
        page_layout.addWidget(self._btn_next)
        layout.addWidget(page_bar)

    # ── 表格创建 ──

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(
            ["✓", "标题", "文号", "分类", "状态", "更新时间", "操作"]
        )
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionsMovable(True)

        # 所有列允许拖拽调宽
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        # 根据字体大小动态设置初始列宽（首次运行或字体变更时使用）
        from ui.settings_dialog import get_font_size
        cur_size = get_font_size()
        checkbox_width = max(40, cur_size * 2 + 10)
        status_width = max(90, cur_size * 6 + 10)
        action_width = max(90, cur_size * 5 + 20)

        table.setColumnWidth(0, checkbox_width)
        table.setColumnWidth(4, status_width)
        table.setColumnWidth(6, action_width)

        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        # 根据字体大小动态设置行高（需要容纳标题+摘要两行）
        table.verticalHeader().setDefaultSectionSize(max(60, cur_size * 4 + 20))
        table.setShowGrid(False)
        table.itemClicked.connect(self._on_table_clicked)
        table.itemDoubleClicked.connect(self._on_table_double_clicked)

        # 列宽/顺序变化时自动保存
        header.sectionResized.connect(self._on_header_changed)
        header.sectionMoved.connect(self._on_header_changed)

        return table

    def _save_header_state(self):
        """保存表头状态（列宽+顺序）到 QSettings"""
        from PyQt5.QtCore import QSettings
        state = self._table.horizontalHeader().saveState()
        QSettings("RegulationManager", "RegulationManager").setValue(
            "ui/table_header_state", state
        )

    def _restore_header_state(self):
        """从 QSettings 恢复表头状态"""
        from PyQt5.QtCore import QSettings
        state = QSettings("RegulationManager", "RegulationManager").value(
            "ui/table_header_state"
        )
        if state is not None:
            self._restoring_header = True
            self._table.horizontalHeader().restoreState(state)
            self._restoring_header = False

    def _on_header_changed(self, *args):
        """列宽或顺序变化时保存"""
        if not self._restoring_header:
            self._save_header_state()

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
            self._btn_list.setObjectName("ViewBtnActive")
            self._btn_card.setObjectName("ViewBtnInactive")
            if self._panel_mode != MODE_BROWSE:
                self._select_all_bar.setVisible(len(self._documents) > 0)
        else:
            self._stack.setCurrentIndex(1)
            self._btn_list.setObjectName("ViewBtnInactive")
            self._btn_card.setObjectName("ViewBtnActive")
            self._select_all_bar.hide()
            self._rebuild_cards()

    def _on_sort(self, field: str):
        self._current_sort = field
        self.page_changed.emit(self._current_page)

    def _goto_page(self, page: int):
        if 1 <= page <= self._total_pages:
            self._current_page = page
            self.page_changed.emit(page)

    # ── 复选框逻辑 ──

    def _on_checkbox_changed(self, state: int, doc_id: int):
        if state == Qt.Checked:
            self._checked_ids.add(doc_id)
        else:
            self._checked_ids.discard(doc_id)
        self._update_batch_ui()

    def _on_select_all_changed(self, state: int):
        checked = (state == Qt.Checked)
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

    def refresh_row_height(self):
        """刷新表格行高和列宽（字体大小变化后调用）"""
        from ui.settings_dialog import get_font_size
        cur_size = get_font_size()
        new_height = max(60, cur_size * 4 + 20)
        checkbox_width = max(40, cur_size * 2 + 10)
        status_width = max(90, cur_size * 6 + 10)
        action_width = max(90, cur_size * 5 + 20)

        self._table.verticalHeader().setDefaultSectionSize(new_height)
        self._table.setColumnWidth(0, checkbox_width)
        self._table.setColumnWidth(4, status_width)
        self._table.setColumnWidth(6, action_width)
        # 刷新当前显示
        if self._documents:
            self._update_table()

    def load_result(self, result: SearchResult, keyword: str = ""):
        self._documents = result.documents
        self._current_page = result.page
        self._total_pages = result.total_pages
        self._count_label.setText(f"{result.total} 项")
        self._search_keyword = keyword
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

        # 获取字体大小（只调用一次）
        from ui.settings_dialog import get_font_size
        cur_size = get_font_size()
        snippet_size = max(11, cur_size - 3)

        for row, doc in enumerate(self._documents):
            # 复选框列
            cb = QCheckBox()
            cb.setObjectName("TableCheckbox")
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(row, 0, cb_widget)
            cb.stateChanged.connect(
                lambda state, did=doc.id: self._on_checkbox_changed(state, did)
            )

            # 标题列（包含搜索摘要，关键词高亮）
            if doc.snippet:
                title_html = f"<div style='margin:2px 0;font-size:{cur_size}px'>{self._highlight(doc.title)}</div><div style='color:#888;font-size:{snippet_size}px'>{self._highlight(doc.snippet)}</div>"
            else:
                title_html = f"<div style='font-size:{cur_size}px'>{self._highlight(doc.title)}</div>"

            title_label = ClickableLabel()
            title_label.setTextFormat(Qt.RichText)
            title_label.setText(title_html)
            title_label.setWordWrap(True)
            title_label.setStyleSheet(f"padding: 4px 8px; font-size: {cur_size}px;")
            title_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            # 双击标题打开文档
            doc_id = doc.id
            title_label.double_clicked.connect(lambda did=doc_id: self.document_opened.emit(did))
            table.setCellWidget(row, 1, title_label)
            table.setItem(row, 2, QTableWidgetItem(doc.doc_no))
            table.setItem(row, 3, QTableWidgetItem(doc.category_name))

            # 状态列
            status_text = DOC_STATUS_LABELS.get(doc.status, doc.status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            if doc.status == "active":
                status_item.setForeground(QColor("#28A745"))
                status_item.setBackground(QColor(40, 167, 69, 30))
                f = status_item.font(); f.setBold(True); status_item.setFont(f)
            elif doc.status == "expired":
                status_item.setForeground(QColor("#DC3545"))
                status_item.setBackground(QColor(220, 53, 69, 30))
                f = status_item.font(); f.setBold(True); status_item.setFont(f)
            table.setItem(row, 4, status_item)

            table.setItem(row, 5, QTableWidgetItem(
                doc.updated_at[:10] if len(doc.updated_at) >= 10 else doc.updated_at
            ))

            # 操作列
            btn_edit = QPushButton("✏ 编辑")
            btn_edit.setObjectName("TableEditBtn")
            btn_edit.setFixedHeight(28)
            btn_edit.clicked.connect(lambda _, did=doc.id: self.document_edit_requested.emit(did))
            edit_widget = QWidget()
            edit_layout = QHBoxLayout(edit_widget)
            edit_layout.addWidget(btn_edit)
            edit_layout.setAlignment(Qt.AlignCenter)
            edit_layout.setContentsMargins(0, 0, 0, 0)
            table.setCellWidget(row, 6, edit_widget)

        table.blockSignals(False)
        table.setColumnHidden(0, self._panel_mode == MODE_BROWSE)

    def _rebuild_cards(self):
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        cols = max(1, (self._card_scroll.width() - 32) // 300)
        for i, doc in enumerate(self._documents):
            card = DocumentCard(doc, keyword=self._search_keyword)
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
