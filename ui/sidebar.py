"""
左侧边栏 — 分类树 + 快捷入口 + 统计摘要
"""
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QAction,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QPushButton, QFrame, QMenu
)


class Sidebar(QWidget):

    category_selected = pyqtSignal(int)
    action_requested = pyqtSignal(str)
    category_delete_requested = pyqtSignal(int)  # 新增：删除分类信号

    EXPANDED_WIDTH = 260
    COLLAPSED_WIDTH = 56

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self._collapsed = False
        self._current_cat_id: Optional[int] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 折叠/展开按钮
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 8, 4)
        header_layout.setSpacing(4)

        self._title = QLabel("制度汇编")
        self._title.setObjectName("SidebarTitle")
        header_layout.addWidget(self._title, 1)

        self._btn_toggle = QPushButton("◀")
        self._btn_toggle.setObjectName("SidebarToggleBtn")
        self._btn_toggle.setFixedSize(28, 28)
        self._btn_toggle.setToolTip("折叠侧边栏")
        self._btn_toggle.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self._btn_toggle)

        layout.addWidget(header)

        from config import APP_VERSION
        self._subtitle = QLabel(f"管理系统 {APP_VERSION}")
        self._subtitle.setObjectName("SidebarSubtitle")
        layout.addWidget(self._subtitle)

        sep = QFrame()
        sep.setObjectName("SidebarSeparator")
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        # 导航按钮
        self._btn_all = QPushButton("  全部制度")
        self._btn_all.setCheckable(True)
        self._btn_all.setChecked(True)
        self._btn_all.clicked.connect(lambda: self._on_nav_clicked(self._btn_all, 0))
        layout.addWidget(self._btn_all)

        self._btn_recent = QPushButton("  最近使用")
        self._btn_recent.setCheckable(True)
        self._btn_recent.clicked.connect(lambda: self._on_nav_clicked(self._btn_recent, -1))
        layout.addWidget(self._btn_recent)

        self._btn_recycle = QPushButton("  回收站")
        self._btn_recycle.setCheckable(True)
        self._btn_recycle.clicked.connect(lambda: self._on_nav_clicked(self._btn_recycle, -2))
        layout.addWidget(self._btn_recycle)

        self._btn_stats = QPushButton("  统计看板")
        self._btn_stats.setCheckable(True)
        self._btn_stats.clicked.connect(lambda: self._on_nav_clicked(self._btn_stats, -3))
        layout.addWidget(self._btn_stats)

        self._btn_scorecard = QPushButton("  评级打分卡")
        self._btn_scorecard.setCheckable(True)
        self._btn_scorecard.clicked.connect(lambda: self._on_nav_clicked(self._btn_scorecard, -4))
        layout.addWidget(self._btn_scorecard)

        # 保存导航按钮列表（折叠/展开时统一处理）
        self._nav_buttons = [self._btn_all, self._btn_recent, self._btn_recycle,
                             self._btn_stats, self._btn_scorecard]

        sep2 = QFrame()
        sep2.setObjectName("SidebarSeparator")
        sep2.setFrameShape(QFrame.HLine)
        layout.addWidget(sep2)

        self._cat_label = QLabel("  分类目录")
        self._cat_label.setObjectName("SidebarCatLabel")
        layout.addWidget(self._cat_label)

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

        self._btn_add_cat = QPushButton("  + 添加分类")
        self._btn_add_cat.setObjectName("SidebarAddCatBtn")
        self._btn_add_cat.clicked.connect(lambda: self.action_requested.emit("add_category"))
        layout.addWidget(self._btn_add_cat)

    def _on_nav_clicked(self, btn, cat_id):
        for b in [self._btn_all, self._btn_recent, self._btn_recycle, self._btn_stats,
                  self._btn_scorecard]:
            if b != btn:
                b.setChecked(False)
        self._tree.clearSelection()
        self._current_cat_id = cat_id
        self.category_selected.emit(cat_id)

    def _on_category_clicked(self, item, column):
        for b in [self._btn_all, self._btn_recent, self._btn_recycle, self._btn_stats,
                  self._btn_scorecard]:
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
                if cat.children:
                    add_items(item, cat.children)

        add_items(None, categories)
        self._tree.expandAll()
        self._stats_label.setText(f"  共 {total_docs} 项制度")

    def select_nav(self, nav_id: int):
        btn_map = {0: self._btn_all, -1: self._btn_recent, -2: self._btn_recycle,
                   -3: self._btn_stats, -4: self._btn_scorecard}
        if nav_id in btn_map:
            self._on_nav_clicked(btn_map[nav_id], nav_id)

    def _toggle_collapse(self):
        """切换侧边栏折叠/展开"""
        self._collapsed = not self._collapsed
        target_width = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH

        # 动画过渡
        anim = QPropertyAnimation(self, b"minimumWidth")
        anim.setDuration(200)
        anim.setStartValue(self.width())
        anim.setEndValue(target_width)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        anim.start()
        # 保持引用防止被 GC
        self._anim = anim

        self.setFixedWidth(target_width)

        # 折叠时隐藏文字元素，只保留图标按钮
        show_text = not self._collapsed
        self._title.setVisible(show_text)
        self._subtitle.setVisible(show_text)
        self._cat_label.setVisible(show_text)
        self._stats_label.setVisible(show_text)
        self._tree.setVisible(show_text)
        self._btn_add_cat.setVisible(show_text)

        # 导航按钮：折叠时隐藏文字，展开时恢复
        nav_texts = [
            "  全部制度",
            "  最近使用",
            "  回收站",
            "  统计看板",
            "  评级打分卡",
        ]
        for btn, text in zip(self._nav_buttons, nav_texts):
            btn.setText(text if show_text else "")

        self._btn_toggle.setText("▶" if self._collapsed else "◀")
        self._btn_toggle.setToolTip("展开侧边栏" if self._collapsed else "折叠侧边栏")
