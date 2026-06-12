"""
左侧边栏 — 分类树 + 快捷入口 + 统计摘要
"""
from typing import Dict, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QPushButton, QFrame, QMenu
)

from ui.styles import SIDEBAR_CAT_LABEL_LIGHT, SIDEBAR_STATS_LIGHT, SIDEBAR_ADD_CAT_BTN


class Sidebar(QWidget):

    category_selected = pyqtSignal(int)
    action_requested = pyqtSignal(str)
    category_delete_requested = pyqtSignal(int)  # 新增：删除分类信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)
        self._current_cat_id: Optional[int] = None
        self._category_items: Dict[int, QTreeWidgetItem] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title = QLabel("制度汇编")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        subtitle = QLabel("管理系统 v1.0")
        subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setObjectName("SidebarSeparator")
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        btn_all = QPushButton("  📋  全部制度")
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        btn_all.clicked.connect(lambda: self._on_nav_clicked(btn_all, 0))
        self._btn_all = btn_all
        layout.addWidget(btn_all)

        btn_recent = QPushButton("  🕐  最近使用")
        btn_recent.setCheckable(True)
        btn_recent.clicked.connect(lambda: self._on_nav_clicked(btn_recent, -1))
        self._btn_recent = btn_recent
        layout.addWidget(btn_recent)

        btn_recycle = QPushButton("  🗑  回收站")
        btn_recycle.setCheckable(True)
        btn_recycle.clicked.connect(lambda: self._on_nav_clicked(btn_recycle, -2))
        self._btn_recycle = btn_recycle
        layout.addWidget(btn_recycle)

        btn_stats = QPushButton("  📊  统计看板")
        btn_stats.setCheckable(True)
        btn_stats.clicked.connect(lambda: self._on_nav_clicked(btn_stats, -3))
        self._btn_stats = btn_stats
        layout.addWidget(btn_stats)

        sep2 = QFrame()
        sep2.setObjectName("SidebarSeparator")
        sep2.setFrameShape(QFrame.HLine)
        layout.addWidget(sep2)

        cat_label = QLabel("  分类目录")
        cat_label.setObjectName("SidebarCatLabel")
        layout.addWidget(cat_label)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self._tree.itemClicked.connect(self._on_category_clicked)
        layout.addWidget(self._tree, 1)

        sep3 = QFrame()
        sep3.setObjectName("SidebarSeparator")
        sep3.setFrameShape(QFrame.HLine)
        layout.addWidget(sep3)

        self._stats_label = QLabel("  共 0 项制度")
        self._stats_label.setObjectName("SidebarStats")
        layout.addWidget(self._stats_label)

        btn_add_cat = QPushButton("  + 添加分类")
        btn_add_cat.setObjectName("SidebarAddCatBtn")
        btn_add_cat.clicked.connect(lambda: self.action_requested.emit("add_category"))
        layout.addWidget(btn_add_cat)

    def _on_nav_clicked(self, btn, cat_id):
        for b in [self._btn_all, self._btn_recent, self._btn_recycle, self._btn_stats]:
            if b != btn:
                b.setChecked(False)
        self._tree.clearSelection()
        self._current_cat_id = cat_id
        self.category_selected.emit(cat_id)

    def _on_category_clicked(self, item, column):
        for b in [self._btn_all, self._btn_recent, self._btn_recycle, self._btn_stats]:
            b.setChecked(False)
        cat_id = item.data(0, Qt.UserRole)
        if cat_id is not None:
            self._current_cat_id = cat_id
            self.category_selected.emit(cat_id)

    def _on_tree_context_menu(self, pos):
        """右键菜单 — 删除分类"""
        item = self._tree.itemAt(pos)
        if not item:
            return
        cat_id = item.data(0, Qt.UserRole)
        if cat_id is None:
            return

        menu = QMenu(self)
        act_delete = QAction("🗑  删除分类", self)
        act_delete.triggered.connect(lambda checked=False, cid=cat_id: self.category_delete_requested.emit(cid))
        menu.addAction(act_delete)
        viewport = self._tree.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(pos))

    def load_categories(self, categories: list, total_docs: int = 0):
        self._tree.clear()
        self._category_items.clear()

        def add_items(parent_item, cats):
            for cat in cats:
                item = QTreeWidgetItem()
                item.setText(0, f"{cat.name}  ({cat.doc_count})")
                item.setData(0, Qt.UserRole, cat.id)
                item.setToolTip(0, cat.name)
                if parent_item:
                    parent_item.addChild(item)
                else:
                    self._tree.addTopLevelItem(item)
                self._category_items[cat.id] = item
                if cat.children:
                    add_items(item, cat.children)

        add_items(None, categories)
        self._tree.expandAll()
        self._stats_label.setText(f"  共 {total_docs} 项制度")

    def select_category(self, cat_id: int):
        if cat_id in self._category_items:
            self._tree.setCurrentItem(self._category_items[cat_id])

    def select_nav(self, nav_id: int):
        btn_map = {0: self._btn_all, -1: self._btn_recent, -2: self._btn_recycle, -3: self._btn_stats}
        if nav_id in btn_map:
            self._on_nav_clicked(btn_map[nav_id], nav_id)
