"""
主窗口 — 菜单栏 + 工具栏 + 三栏布局
"""
import logging
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QToolBar, QMenuBar, QStatusBar,
    QLabel, QPushButton, QFileDialog, QMessageBox,
    QGridLayout, QFrame
)

import config
from ui.sidebar import Sidebar
from ui.document_panel import DocumentPanel, MODE_MANAGE, MODE_BROWSE, MODE_RECYCLE
from ui.add_edit_dialog import AddEditDialog
from ui.components.toast import Toast
from ui.styles import SEARCH_BAR_CONTAINER_LIGHT, DIALOG_BTN_SECONDARY, _FONT
from core import document_service, category_service, search_service, statistics_service
from models import SearchFilter

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """应用主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        self._current_category_id: Optional[int] = None
        self._current_view = "list"  # list / recent / recycle / stats
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._load_initial_data()

    def _setup_ui(self):
        """构建主界面布局"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 左侧边栏 ──
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # ── 右侧内容区 ──
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 搜索栏
        search_bar = QWidget()
        search_bar.setStyleSheet(SEARCH_BAR_CONTAINER_LIGHT)
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(16, 10, 16, 10)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("SearchBar")
        self._search_input.setPlaceholderText("🔍 搜索制度标题、文号、部门...")
        self._search_input.setMinimumHeight(38)
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        btn_search = QPushButton("搜索")
        btn_search.setFixedHeight(38)
        btn_search.setFixedWidth(80)
        btn_search.clicked.connect(self._on_search)
        search_layout.addWidget(btn_search)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedHeight(38)
        btn_clear.setFixedWidth(60)
        btn_clear.setStyleSheet(DIALOG_BTN_SECONDARY)
        btn_clear.clicked.connect(self._on_clear_search)
        search_layout.addWidget(btn_clear)

        right_layout.addWidget(search_bar)

        # 内容区容器（文档列表 / 统计看板 共用）
        self._content_stack = QWidget()
        self._content_layout = QVBoxLayout(self._content_stack)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        # 文档列表面板
        self._doc_panel = DocumentPanel()
        self._content_layout.addWidget(self._doc_panel)

        # 统计看板面板（初始隐藏）
        self._stats_panel = self._create_stats_panel()
        self._stats_panel.hide()
        self._content_layout.addWidget(self._stats_panel)

        right_layout.addWidget(self._content_stack, 1)

        main_layout.addWidget(right_widget, 1)

    def _create_stats_panel(self) -> QWidget:
        """创建统计看板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("📊 统计看板")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: #e2e8f0; font-family: {_FONT};")
        layout.addWidget(title)

        # 统计卡片网格
        self._stats_grid = QGridLayout()
        self._stats_grid.setSpacing(16)
        layout.addLayout(self._stats_grid)

        layout.addStretch()
        return panel

    def _build_stats_cards(self):
        """构建统计卡片"""
        # 清空旧卡片
        while self._stats_grid.count():
            item = self._stats_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        stats = statistics_service.get_summary()

        cards_data = [
            ("📋", "制度总数", str(stats["total_docs"]), "#6366f1"),
            ("📁", "分类数量", str(stats["total_categories"]), "#34d399"),
            ("✅", "现行有效", str(stats.get("active_count", 0)), "#60a5fa"),
            ("📦", "已归档", str(stats.get("archived_count", 0)), "#94a3b8"),
        ]

        for i, (icon, label, value, color) in enumerate(cards_data):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-left: 4px solid {color};
                    border-radius: 8px;
                    padding: 20px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 24px; background: transparent; font-family: {_FONT}; color: {color};")
            card_layout.addWidget(icon_label)

            val_label = QLabel(value)
            val_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color}; background: transparent; font-family: {_FONT};")
            card_layout.addWidget(val_label)

            text_label = QLabel(label)
            text_label.setStyleSheet(f"font-size: 13px; color: #94a3b8; background: transparent; font-family: {_FONT};")
            card_layout.addWidget(text_label)

            self._stats_grid.addWidget(card, i // 2, i % 2)

    def _setup_menu(self):
        """菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")

        act_add = QAction("新增制度(&N)", self)
        act_add.setShortcut(QKeySequence("Ctrl+N"))
        act_add.triggered.connect(self._on_add_document)
        file_menu.addAction(act_add)

        act_batch = QAction("批量导入(&B)", self)
        act_batch.triggered.connect(self._on_batch_import)
        file_menu.addAction(act_batch)

        file_menu.addSeparator()

        act_export = QAction("批量导出(&E)", self)
        act_export.triggered.connect(self._on_batch_export)
        file_menu.addAction(act_export)

        file_menu.addSeparator()

        act_backup = QAction("备份制度库...", self)
        act_backup.triggered.connect(self._on_backup)
        file_menu.addAction(act_backup)

        act_restore = QAction("恢复制度库...", self)
        act_restore.triggered.connect(self._on_restore)
        file_menu.addAction(act_restore)

        file_menu.addSeparator()

        act_exit = QAction("退出(&Q)", self)
        act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")

        act_theme = QAction("切换深色/亮色主题", self)
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")

        act_rebuild = QAction("重建搜索索引", self)
        act_rebuild.triggered.connect(self._rebuild_index)
        tools_menu.addAction(act_rebuild)

        act_settings = QAction("系统设置(&S)", self)
        act_settings.triggered.connect(self._on_settings)
        tools_menu.addAction(act_settings)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        act_about = QAction("关于(&A)", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    def _setup_toolbar(self):
        """工具栏"""
        toolbar = QToolBar("快捷操作")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        act_add = QAction("➕ 新增制度", self)
        act_add.triggered.connect(self._on_add_document)
        toolbar.addAction(act_add)

        act_import = QAction("📥 批量导入", self)
        act_import.triggered.connect(self._on_batch_import)
        toolbar.addAction(act_import)

        toolbar.addSeparator()

        act_refresh = QAction("🔄 刷新", self)
        act_refresh.triggered.connect(self._refresh_list)
        toolbar.addAction(act_refresh)

    def _setup_statusbar(self):
        """状态栏"""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")

    def _connect_signals(self):
        """信号连接"""
        self._sidebar.category_selected.connect(self._on_category_selected)
        self._sidebar.action_requested.connect(self._on_sidebar_action)
        self._sidebar.category_delete_requested.connect(self._on_delete_category)
        self._doc_panel.document_selected.connect(self._on_doc_selected)
        self._doc_panel.document_opened.connect(self._on_doc_opened)
        self._doc_panel.document_deleted.connect(self._on_doc_deleted)
        self._doc_panel.page_changed.connect(self._on_page_changed)
        # 批量操作信号
        self._doc_panel.batch_delete_requested.connect(self._on_batch_delete)
        self._doc_panel.batch_restore_requested.connect(self._on_batch_restore)
        self._doc_panel.batch_permanent_delete_requested.connect(self._on_batch_permanent_delete)

    def _load_initial_data(self):
        """加载初始数据"""
        self._refresh_categories()
        self._refresh_list()

    # ── 数据刷新 ───────────────────────────────────────────

    def _refresh_categories(self):
        """刷新分类树"""
        tree = category_service.get_category_tree()
        total = document_service.get_document_list(page_size=1).total
        self._sidebar.load_categories(tree, total)

    def _refresh_list(self):
        """刷新文档列表"""
        keyword = self._search_input.text().strip()
        if keyword:
            self._do_search(keyword)
            return

        if self._current_view == "recent":
            self._show_recent()
        elif self._current_view == "recycle":
            self._show_recycle()
        elif self._current_view == "stats":
            self._show_stats()
        else:
            self._doc_panel.set_panel_mode(MODE_MANAGE)
            result = document_service.get_document_list(
                category_id=self._current_category_id
            )
            self._doc_panel.load_result(result)
            title = "全部制度" if self._current_category_id is None else "分类文档"
            self._doc_panel.set_title(title)

        self._statusbar.showMessage("就绪")

    # ── 事件处理 ───────────────────────────────────────────

    def _on_category_selected(self, cat_id: int):
        """分类选中"""
        # 切换回文档列表视图
        self._show_doc_panel()

        if cat_id == 0:
            # 全部制度
            self._current_category_id = None
            self._current_view = "list"
            self._doc_panel.set_title("全部制度")
        elif cat_id == -1:
            # 最近使用
            self._current_view = "recent"
            self._show_recent()
            return
        elif cat_id == -2:
            # 回收站
            self._current_view = "recycle"
            self._show_recycle()
            return
        elif cat_id == -3:
            # 统计看板
            self._current_view = "stats"
            self._show_stats()
            return
        else:
            self._current_category_id = cat_id
            self._current_view = "list"
            cats = category_service.get_all_categories()
            cat_name = next((c.name for c in cats if c.id == cat_id), "分类")
            self._doc_panel.set_title(cat_name)

        self._refresh_list()

    def _show_doc_panel(self):
        """显示文档列表面板，隐藏统计面板"""
        self._stats_panel.hide()
        self._doc_panel.show()

    def _show_recent(self):
        """显示最近使用（按更新时间倒序，取前50）"""
        self._doc_panel.set_panel_mode(MODE_BROWSE)
        result = document_service.get_document_list(page_size=50)
        self._doc_panel.load_result(result)
        self._doc_panel.set_title("最近使用")
        self._statusbar.showMessage(f"显示最近 {result.total} 项制度")

    def _show_recycle(self):
        """显示回收站（已删除的文档）"""
        self._doc_panel.set_panel_mode(MODE_RECYCLE)
        result = document_service.get_deleted_documents()
        self._doc_panel.load_result(result)
        self._doc_panel.set_title("回收站")
        self._statusbar.showMessage(f"回收站共 {result.total} 项")

    def _show_stats(self):
        """显示统计看板"""
        self._doc_panel.hide()
        self._stats_panel.show()
        self._build_stats_cards()
        self._statusbar.showMessage("统计看板")

    def _on_sidebar_action(self, action: str):
        """侧边栏动作"""
        if action == "add_category":
            self._on_add_category()

    def _on_search(self):
        """搜索"""
        keyword = self._search_input.text().strip()
        if keyword:
            self._do_search(keyword)
        else:
            self._refresh_list()

    def _do_search(self, keyword: str):
        """执行搜索"""
        self._show_doc_panel()
        self._current_view = "list"
        self._doc_panel.set_panel_mode(MODE_MANAGE)
        f = SearchFilter(
            keyword=keyword,
            category_id=self._current_category_id,
        )
        result = search_service.search(f)
        self._doc_panel.load_result(result)
        self._doc_panel.set_title(f"搜索: {keyword}")
        self._statusbar.showMessage(f"找到 {result.total} 条结果")

    def _on_clear_search(self):
        """清空搜索"""
        self._search_input.clear()
        self._refresh_list()

    def _on_doc_selected(self, doc_id: int):
        """文档选中"""
        self._statusbar.showMessage(f"已选中文档 ID: {doc_id}")

    def _on_doc_opened(self, doc_id: int):
        """打开文档（双击）"""
        doc = document_service.get_document(doc_id)
        if doc and doc.file_path:
            import os
            os.startfile(doc.file_path) if os.name == 'nt' else os.system(f'xdg-open "{doc.file_path}"')
            self._statusbar.showMessage(f"已打开: {doc.title}")

    def _on_doc_deleted(self, doc_id: int):
        """删除文档（移入回收站）"""
        doc = document_service.get_document(doc_id)
        if not doc:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{doc.title}」吗？\n删除后可在回收站恢复。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if document_service.delete_document(doc_id):
                Toast.success(self, f"「{doc.title}」已移入回收站")
                self._refresh_categories()
                self._refresh_list()
            else:
                Toast.error(self, "删除失败")

    def _on_page_changed(self, page: int):
        """翻页"""
        keyword = self._search_input.text().strip()
        if keyword:
            f = SearchFilter(keyword=keyword, category_id=self._current_category_id, page=page)
            result = search_service.search(f)
        elif self._current_view == "recent":
            result = document_service.get_document_list(page=page, page_size=50)
        elif self._current_view == "recycle":
            result = document_service.get_deleted_documents(page=page)
        else:
            result = document_service.get_document_list(
                category_id=self._current_category_id, page=page
            )
        self._doc_panel.load_result(result)

    # ── 批量操作 ──────────────────────────────────────────────

    def _on_batch_delete(self, doc_ids: list):
        """批量移入回收站"""
        count = len(doc_ids)
        reply = QMessageBox.question(
            self, "批量删除确认",
            f"确定要将选中的 {count} 项制度移入回收站吗？\n\n移入后可在回收站中恢复。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        result = document_service.batch_delete(doc_ids)
        if result["success"] > 0:
            Toast.success(self, f"已将 {result['success']} 项制度移入回收站")
        if result["failed"] > 0:
            Toast.warning(self, f"{result['failed']} 项操作失败")
        self._refresh_categories()
        self._refresh_list()

    def _on_batch_restore(self, doc_ids: list):
        """批量还原"""
        count = len(doc_ids)
        reply = QMessageBox.question(
            self, "批量还原确认",
            f"确定要还原选中的 {count} 项制度吗？\n\n还原后将恢复到原分类列表中。",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        result = document_service.batch_restore(doc_ids)
        if result["success"] > 0:
            Toast.success(self, f"已还原 {result['success']} 项制度")
        if result["failed"] > 0:
            Toast.warning(self, f"{result['failed']} 项操作失败")
        self._refresh_categories()
        self._refresh_list()

    def _on_batch_permanent_delete(self, doc_ids: list):
        """批量彻底删除"""
        count = len(doc_ids)
        reply = QMessageBox.warning(
            self, "⚠️ 彻底删除确认",
            f"⚠️ 警告：此操作不可恢复！\n\n"
            f"将永久删除选中的 {count} 项制度及其文件。\n\n"
            f"确定要继续吗？",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        # 二次确认
        reply2 = QMessageBox.warning(
            self, "二次确认",
            f"请再次确认：永久删除 {count} 项制度？\n\n此操作无法撤销！",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply2 != QMessageBox.Yes:
            return
        result = document_service.batch_permanent_delete(doc_ids)
        if result["success"] > 0:
            Toast.success(self, f"已永久删除 {result['success']} 项制度")
        if result["failed"] > 0:
            Toast.warning(self, f"{result['failed']} 项操作失败")
        self._refresh_categories()
        self._refresh_list()
    # ── 对话框 ─────────────────────────────────────────────

    def _on_add_document(self):
        """新增制度"""
        cats = category_service.get_all_categories()
        dlg = AddEditDialog(cats, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            result = document_service.upload_document(
                file_path=data["file_path"],
                title=data["title"],
                doc_no=data["doc_no"],
                category_id=data["category_id"],
                department=data["department"],
                issuing_org=data["issuing_org"],
                effective_date=data["effective_date"],
                description=data["description"],
                tags=data["tags"],
            )
            if result:
                Toast.success(self, f"制度「{result.title}」添加成功")
                self._refresh_categories()
                self._refresh_list()
            else:
                Toast.error(self, "添加失败，请检查文件")

    def _on_add_category(self):
        """新增分类"""
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新增分类", "分类名称：")
        if ok and name.strip():
            result = category_service.add_category(name.strip())
            if result:
                Toast.success(self, f"分类「{name}」添加成功")
                self._refresh_categories()
            else:
                Toast.error(self, "添加分类失败（可能重名）")

    def _on_delete_category(self, cat_id: int):
        """删除分类（右键菜单触发）"""
        # 先查询分类名称和文档数
        cats = category_service.get_all_categories()
        cat = next((c for c in cats if c.id == cat_id), None)
        if not cat:
            Toast.error(self, "分类不存在")
            return

        cat_name = cat.name
        doc_count = cat.doc_count

        # 二次确认
        if doc_count > 0:
            msg = (
                f"确定要删除分类「{cat_name}」吗？\n\n"
                f"该分类下有 {doc_count} 项制度，\n"
                f"删除后这些制度将归入「未分类」（可在全部制度中查看）。"
            )
        else:
            msg = f"确定要删除分类「{cat_name}」吗？\n\n该分类下没有制度。"

        reply = QMessageBox.warning(
            self, "⚠️ 删除分类确认", msg,
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        result = category_service.delete_category(cat_id)
        if result["success"]:
            # 如果当前正在查看被删除的分类，切回全部制度
            if self._current_category_id == cat_id:
                self._current_category_id = None
                self._current_view = "list"
                self._sidebar.select_nav(0)
            Toast.success(self, f"分类「{cat_name}」已删除" + (f"，{doc_count} 项制度归入未分类" if doc_count > 0 else ""))
            self._refresh_categories()
            self._refresh_list()
        else:
            Toast.error(self, f"删除分类「{cat_name}」失败")

    def _on_batch_import(self):
        """批量导入"""
        folder = QFileDialog.getExistingDirectory(self, "选择制度文件夹")
        if not folder:
            return

        import os
        files = []
        for f in os.listdir(folder):
            ext = os.path.splitext(f)[1].lower()
            if ext in config.ALLOWED_EXTENSIONS:
                files.append(os.path.join(folder, f))

        if not files:
            Toast.warning(self, "所选文件夹中没有可导入的文件")
            return

        # 弹出分类选择对话框
        from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox as QCombo
        dlg = QDialog(self)
        dlg.setWindowTitle("批量导入 — 选择分类")
        dlg.setMinimumWidth(400)
        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(24, 24, 24, 24)
        dlg_layout.setSpacing(16)

        info_label = QLabel(f"共找到 {len(files)} 个文件，请选择要导入的分类：")
        info_label.setWordWrap(True)
        dlg_layout.addWidget(info_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        cat_combo = QCombo()
        cats = category_service.get_all_categories()
        for cat in cats:
            cat_combo.addItem(cat.name, cat.id)
        form.addRow("分类 *", cat_combo)
        dlg_layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(dlg.reject)
        btn_layout.addWidget(btn_cancel)
        btn_ok = QPushButton("开始导入")
        btn_ok.clicked.connect(dlg.accept)
        btn_layout.addWidget(btn_ok)
        dlg_layout.addLayout(btn_layout)

        if dlg.exec() != QDialog.Accepted:
            return

        category_id = cat_combo.currentData()
        if category_id is None:
            Toast.warning(self, "请选择分类")
            return

        results = document_service.batch_upload(files, category_id)
        msg = f"导入完成：成功 {results['success']}，失败 {results['failed']}，跳过 {results['skipped']}"
        Toast.success(self, msg)
        self._refresh_categories()
        self._refresh_list()

    def _on_batch_export(self):
        """批量导出"""
        Toast.info(self, "批量导出功能开发中")

    def _on_backup(self):
        """备份"""
        from utils import backup_manager
        path = backup_manager.create_backup("手动备份")
        if path:
            Toast.success(self, f"备份完成: {path.name}")
        else:
            Toast.error(self, "备份失败")

    def _on_restore(self):
        """恢复"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择备份文件", str(config.BACKUPS_DIR),
            "ZIP文件 (*.zip)"
        )
        if path:
            reply = QMessageBox.question(
                self, "确认恢复",
                "恢复将覆盖当前数据，确定继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from utils import backup_manager
                if backup_manager.restore_backup(path):
                    Toast.success(self, "恢复完成，重启应用后生效")
                    self._refresh_categories()
                    self._refresh_list()
                else:
                    Toast.error(self, "恢复失败")

    def _rebuild_index(self):
        """重建搜索索引"""
        from utils import search_engine
        search_engine.rebuild_index()
        Toast.success(self, "搜索索引已重建")

    def _toggle_theme(self):
        """切换主题"""
        Toast.info(self, "主题切换功能开发中")

    def _on_settings(self):
        """系统设置"""
        Toast.info(self, "系统设置功能开发中")

    def _on_about(self):
        """关于"""
        QMessageBox.about(
            self, "关于",
            f"<h3>{config.APP_NAME}</h3>"
            f"<p>版本：{config.APP_VERSION}</p>"
            f"<p>单机版制度文件集中管理系统</p>"
            f"<p>支持 .doc / .docx / .pdf 格式</p>"
        )
