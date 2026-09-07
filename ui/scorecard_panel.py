"""
央行评级标准打分卡面板 — 左树钻取 + 右详情 + 关键词搜索定位
"""
import logging
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QSplitter, QScrollArea,
    QListWidget, QListWidgetItem, QFrame, QMenu, QAction, QInputDialog,
    QDialog,
)

from core import scorecard_service
from models import ScorecardCheckData
from ui.components.toast import Toast

logger = logging.getLogger(__name__)

# 树节点 UserRole 存 (kind, id)
ROLE_NODE = Qt.UserRole


class ScorecardPanel(QWidget):
    """打分卡主面板"""

    document_open_requested = pyqtSignal(int)  # 请求主窗口打开某制度文档

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scorecards = []          # List[ScorecardData]
        self._current_scorecard_id = None
        self._current_check = None     # type: Optional[ScorecardCheckData]
        self._hits = []                # 搜索命中
        self._setup_ui()
        self.reload_scorecards()

    # ── 界面构建 ──

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏：银行类型 + 搜索
        toolbar = QWidget()
        toolbar.setObjectName("PanelToolbar")
        tb = QHBoxLayout(toolbar)
        tb.setContentsMargins(16, 8, 16, 8)

        title = QLabel("央行评级标准打分卡")
        title.setObjectName("PanelTitle")
        tb.addWidget(title)

        tb.addWidget(QLabel("  银行类型："))
        self._type_combo = QComboBox()
        self._type_combo.setMinimumWidth(180)
        self._type_combo.currentIndexChanged.connect(self._on_scorecard_changed)
        tb.addWidget(self._type_combo)

        tb.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setObjectName("SearchBar")
        self._search_input.setPlaceholderText("🔍 搜索打分卡内容…")
        self._search_input.setMinimumWidth(260)
        self._search_input.returnPressed.connect(self._on_search)
        tb.addWidget(self._search_input)

        btn_search = QPushButton("搜索")
        btn_search.clicked.connect(self._on_search)
        tb.addWidget(btn_search)

        btn_clear = QPushButton("清空")
        btn_clear.setObjectName("DialogBtnSecondary")
        btn_clear.clicked.connect(self._on_clear_search)
        tb.addWidget(btn_clear)

        layout.addWidget(toolbar)

        # 主体：左树 / 右详情
        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self._result_list = QListWidget()
        self._result_list.setMaximumHeight(160)
        self._result_list.itemClicked.connect(self._on_result_clicked)
        self._result_list.hide()
        left_layout.addWidget(self._result_list)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_tree_menu)
        self._tree.itemClicked.connect(self._on_tree_clicked)
        left_layout.addWidget(self._tree, 1)
        splitter.addWidget(left)

        # 右侧详情（可滚动）
        self._detail_scroll = QScrollArea()
        self._detail_scroll.setWidgetResizable(True)
        self._detail_scroll.setFrameShape(QFrame.NoFrame)
        self._detail_host = QWidget()
        self._detail_layout = QVBoxLayout(self._detail_host)
        self._detail_layout.setContentsMargins(20, 16, 20, 16)
        self._detail_layout.setSpacing(4)
        self._detail_scroll.setWidget(self._detail_host)
        splitter.addWidget(self._detail_scroll)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter, 1)

        self._show_placeholder("请选择左侧打分卡条目查看详情")

    # ── 数据加载 ──

    def reload_scorecards(self):
        """加载打分卡列表（银行类型）"""
        self._scorecards = scorecard_service.get_scorecards()
        self._type_combo.blockSignals(True)
        self._type_combo.clear()
        for card in self._scorecards:
            self._type_combo.addItem(card.name, card.id)
        self._type_combo.blockSignals(False)

        if self._scorecards:
            self._current_scorecard_id = self._scorecards[0].id
            self._reload_tree()
        else:
            self._show_placeholder("暂无打分卡数据")

    def _on_scorecard_changed(self, index: int):
        if index < 0:
            return
        self._current_scorecard_id = self._type_combo.itemData(index)
        self._on_clear_search()
        self._reload_tree()

    def _reload_tree(self):
        """按当前银行类型重建四层树"""
        self._tree.clear()
        self._current_check = None
        self._show_placeholder("请选择左侧打分卡条目查看详情")
        if self._current_scorecard_id is None:
            return

        for module in scorecard_service.get_tree(self._current_scorecard_id):
            m_item = QTreeWidgetItem([module.name])
            m_item.setData(0, ROLE_NODE, ("module", module.id))
            self._tree.addTopLevelItem(m_item)
            for section in module.children:
                s_item = QTreeWidgetItem([section.name])
                s_item.setData(0, ROLE_NODE, ("section", section.id))
                m_item.addChild(s_item)
                for item in section.children:
                    i_item = QTreeWidgetItem([item.name])
                    i_item.setData(0, ROLE_NODE, ("item", item.id))
                    s_item.addChild(i_item)
                    for check in item.checks:
                        text = check.content or "（无评级内容）"
                        c_item = QTreeWidgetItem([text])
                        c_item.setData(0, ROLE_NODE, ("check", check.id))
                        c_item.setToolTip(0, text)
                        i_item.addChild(c_item)
        self._tree.expandToDepth(0)

    # ── 树交互 ──

    def _on_tree_clicked(self, item: QTreeWidgetItem, column: int):
        node = item.data(0, ROLE_NODE)
        if not node:
            return
        kind, node_id = node
        if kind == "check":
            self._show_check(node_id)
        else:
            item.setExpanded(not item.isExpanded())
            self._show_node_summary(item, kind)

    def _show_node_summary(self, item: QTreeWidgetItem, kind: str):
        """非叶子节点：展示其下层清单概览"""
        kind_label = {"module": "模块", "section": "一级指标", "item": "二级指标"}.get(kind, "")
        children = [item.child(i).text(0) for i in range(item.childCount())]
        self._clear_detail()
        self._add_detail_title(f"{kind_label}：{item.text(0)}")
        self._add_detail_field(f"下级条目（{len(children)}）", "\n".join(
            f"· {name}" for name in children) or "（无）")

    def _show_check(self, check_id: int):
        """叶子节点：展示检查项全字段 + 关联制度"""
        scorecard_service.sync_auto_links(check_id)  # 引用自动识别，先同步再取详情
        check = scorecard_service.get_check(check_id)
        if not check:
            self._show_placeholder("该条目不存在或已被删除")
            return
        self._current_check = check

        self._clear_detail()
        self._add_detail_title(check.content or "（无评级内容）")
        self._add_detail_field("评分要点", check.key_points)
        self._add_detail_field("监管制度和条款（依据）", check.regulation_basis)
        self._add_detail_field("需调阅材料（清单）", check.review_materials)

        # 关联制度
        label = QLabel("关联制度")
        label.setStyleSheet(
            "font-weight: bold; color: #0066CC; font-size: 13px; "
            "padding-left: 2px; margin-top: 8px;"
        )
        self._detail_layout.addWidget(label)
        if check.documents:
            for doc in check.documents:
                # 信息卡片：每条关联制度一个卡片
                card = QFrame()
                card.setFrameShape(QFrame.StyledPanel)
                card.setStyleSheet(
                    "QFrame { background-color: #F0F7FF; border: 1px solid #D0E3F7; "
                    "border-radius: 6px; padding: 4px 8px; }"
                )
                row = QHBoxLayout(card)
                row.setContentsMargins(12, 8, 12, 8)
                row.setSpacing(8)

                # 文档信息区
                info_layout = QVBoxLayout()
                info_layout.setSpacing(2)

                name = QLabel(f"📄 {doc.title}")
                name.setWordWrap(True)
                name.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: #1E40AF; "
                    "background: transparent; border: none;"
                )
                info_layout.addWidget(name)

                # 详情行：文号 + 文件类型 + 自动关联标记
                details = []
                if doc.doc_no:
                    details.append(f"文号：{doc.doc_no}")
                if doc.file_type:
                    details.append(doc.file_type.upper())
                if getattr(doc, 'is_auto', False):
                    details.append("🔗 自动关联")
                if details:
                    detail_text = "  |  ".join(details)
                    detail_lbl = QLabel(detail_text)
                    detail_lbl.setStyleSheet(
                        "font-size: 11px; color: #6B7280; "
                        "background: transparent; border: none;"
                    )
                    info_layout.addWidget(detail_lbl)

                row.addLayout(info_layout, 1)

                # Tooltip：悬停展示完整信息
                tooltip_parts = [doc.title]
                if doc.doc_no:
                    tooltip_parts.append(f"文号：{doc.doc_no}")
                if doc.status:
                    tooltip_parts.append(f"状态：{doc.status}")
                if doc.file_type:
                    tooltip_parts.append(f"类型：{doc.file_type}")
                if doc.category_name:
                    tooltip_parts.append(f"分类：{doc.category_name}")
                if doc.effective_date:
                    tooltip_parts.append(f"生效日期：{doc.effective_date}")
                if getattr(doc, 'is_auto', False):
                    tooltip_parts.append("关联方式：引用自动识别")
                card.setToolTip("\n".join(tooltip_parts))

                btn = QPushButton("打开")
                btn.setFixedWidth(70)
                btn.setStyleSheet(
                    "QPushButton { font-size: 12px; padding: 4px 8px; }"
                )
                btn.clicked.connect(lambda _, d=doc.id: self.document_open_requested.emit(d))
                row.addWidget(btn)

                self._detail_layout.addWidget(card)
        else:
            empty_hint = QLabel("  暂未关联制度文档")
            empty_hint.setStyleSheet(
                "color: #9CA3AF; font-size: 12px; padding: 8px 12px; "
                "background-color: #F9FAFB; border: 1px dashed #D1D5DB; "
                "border-radius: 6px;"
            )
            self._detail_layout.addWidget(empty_hint)

        # 编辑入口
        btn_edit = QPushButton("✏ 编辑本条目")
        btn_edit.setFixedWidth(140)
        btn_edit.clicked.connect(lambda: self._edit_check(check.id))
        self._detail_layout.addWidget(btn_edit)
        self._detail_layout.addStretch()

    # ── 详情区辅助 ──

    def _clear_detail(self):
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_placeholder(self, text: str):
        self._clear_detail()
        hint = QLabel(text)
        hint.setStyleSheet("color: #999999;")
        self._detail_layout.addWidget(hint)
        self._detail_layout.addStretch()

    def _add_detail_title(self, text: str):
        title = QLabel(text)
        title.setWordWrap(True)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #111827; "
            "padding: 4px 0; line-height: 1.4;"
        )
        self._detail_layout.addWidget(title)

    def _add_detail_field(self, label_text: str, value: str):
        """添加一个带卡片背景的详情字段（标签 + 内容）"""
        # 字段标题
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "font-weight: bold; color: #0066CC; font-size: 13px; "
            "padding-left: 2px; margin-top: 8px;"
        )
        self._detail_layout.addWidget(lbl)

        # 内容卡片：带浅色背景 + 圆角边框
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(
            "QFrame { background-color: #F8F9FA; border: 1px solid #E9ECEF; "
            "border-radius: 6px; padding: 8px 12px; }"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        body = QLabel()
        body.setTextFormat(Qt.RichText)
        body.setWordWrap(True)
        body.setTextInteractionFlags(
            Qt.TextBrowserInteraction | Qt.TextSelectableByMouse
        )
        body.setText(scorecard_service.render_linked_html(value) or "（空）")
        body.linkActivated.connect(self._on_citation_link)
        body.setStyleSheet(
            "color: #212529; font-size: 13px; line-height: 1.5; "
            "background-color: transparent; border: none;"
        )
        card_layout.addWidget(body)

        self._detail_layout.addWidget(card)

    def _on_citation_link(self, link: str):
        """制度引用超链：doc://{id} 打开文件，missing:// 弹出详情对话框"""
        if link.startswith("doc://"):
            self.document_open_requested.emit(int(link[6:]))
        elif link.startswith("missing://"):
            from urllib.parse import unquote
            citation_text = unquote(link[10:])
            self._show_missing_citation_dialog(citation_text)

    def _show_missing_citation_dialog(self, citation_text: str):
        """弹出对话框展示未匹配的制度引用详情"""
        dlg = QDialog(self)
        dlg.setWindowTitle("制度引用 — 未匹配")
        dlg.setMinimumWidth(480)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 图标 + 标题
        header = QLabel("⚠ 该制度引用未在库中找到匹配文件")
        header.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #B45309; "
            "padding: 0; background: transparent;"
        )
        layout.addWidget(header)

        # 引用原文（卡片样式，方便复制）
        ref_label = QLabel("引用原文：")
        ref_label.setStyleSheet(
            "font-weight: bold; color: #495057; font-size: 13px; "
            "background: transparent; border: none;"
        )
        layout.addWidget(ref_label)

        ref_card = QFrame()
        ref_card.setFrameShape(QFrame.StyledPanel)
        ref_card.setStyleSheet(
            "QFrame { background-color: #FFF7ED; border: 1px solid #FED7AA; "
            "border-radius: 6px; padding: 10px 14px; }"
        )
        ref_layout = QVBoxLayout(ref_card)
        ref_layout.setContentsMargins(14, 10, 14, 10)
        ref_content = QLabel(citation_text)
        ref_content.setWordWrap(True)
        ref_content.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ref_content.setStyleSheet(
            "font-size: 14px; color: #92400E; font-weight: bold; "
            "background: transparent; border: none; line-height: 1.5;"
        )
        ref_layout.addWidget(ref_content)
        layout.addWidget(ref_card)

        # 建议操作
        hint = QLabel(
            "可能的原因：\n"
            "  · 该制度尚未导入到制度库中\n"
            "  · 标题或文号与库中记录不完全一致\n\n"
            "建议操作：\n"
            "  · 检查制度库中是否已导入该文件\n"
            "  · 如已导入，请核对标题和文号是否匹配"
        )
        hint.setStyleSheet(
            "color: #6B7280; font-size: 12px; line-height: 1.6; "
            "background-color: #F3F4F6; border-radius: 6px; "
            "padding: 12px 14px;"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # 关闭按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setMinimumWidth(80)
        btn_close.clicked.connect(dlg.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        dlg.exec_()

    # ── 搜索 ──

    def _on_search(self):
        keyword = self._search_input.text().strip()
        self._result_list.clear()
        if not keyword:
            self._result_list.hide()
            return
        if self._current_scorecard_id is None:
            return

        self._hits = scorecard_service.search(self._current_scorecard_id, keyword)
        if not self._hits:
            self._result_list.addItem("无匹配结果")
            self._result_list.show()
            return

        for hit in self._hits:
            text = f"[{hit.matched_field}] {hit.path}"
            if hit.kind == "check":
                text += f" — {hit.snippet}"
            list_item = QListWidgetItem(text)
            list_item.setData(Qt.UserRole, hit.ids_chain)
            list_item.setToolTip(text)
            self._result_list.addItem(list_item)
        self._result_list.show()

    def _on_clear_search(self):
        self._search_input.clear()
        self._result_list.clear()
        self._result_list.hide()
        self._hits = []

    def _on_result_clicked(self, list_item: QListWidgetItem):
        ids_chain = list_item.data(Qt.UserRole)
        if not ids_chain:
            return
        self._locate(ids_chain)

    def _locate(self, ids_chain: List[int]):
        """按 ids_chain 逐层展开树并选中目标节点"""
        kinds = ["module", "section", "item", "check"]
        parent = self._tree.invisibleRootItem()
        target = None
        for depth, node_id in enumerate(ids_chain):
            kind = kinds[depth]
            found = None
            for idx in range(parent.childCount()):
                child = parent.child(idx)
                node = child.data(0, ROLE_NODE)
                if node and node[0] == kind and node[1] == node_id:
                    found = child
                    break
            if found is None:
                break
            found.setExpanded(True)
            parent = found
            target = found

        if target is not None:
            self._tree.setCurrentItem(target)
            self._tree.scrollToItem(target)
            node = target.data(0, ROLE_NODE)
            if node and node[0] == "check":
                self._show_check(node[1])

    # ── 编辑 ──

    def _on_tree_menu(self, pos):
        item = self._tree.itemAt(pos)
        if not item:
            return
        node = item.data(0, ROLE_NODE)
        if not node:
            return
        kind, node_id = node

        menu = QMenu(self)
        if kind in ("module", "section", "item"):
            act = QAction("✏  重命名", self)
            act.triggered.connect(lambda: self._rename_node(kind, node_id, item))
            menu.addAction(act)
        else:
            act = QAction("✏  编辑条目", self)
            act.triggered.connect(lambda: self._edit_check(node_id))
            menu.addAction(act)
        viewport = self._tree.viewport()
        if viewport:
            menu.exec(viewport.mapToGlobal(pos))

    def _rename_node(self, kind: str, node_id: int, item: QTreeWidgetItem):
        kind_label = {"module": "模块", "section": "一级指标", "item": "二级指标"}.get(kind, "节点")
        new_name, ok = QInputDialog.getText(self, f"重命名{kind_label}", "新名称：", text=item.text(0))
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            Toast.warning(self, "名称不能为空")
            return
        if scorecard_service.rename_node(kind, node_id, new_name):
            item.setText(0, new_name)
            Toast.success(self, f"{kind_label}已重命名")
        else:
            Toast.error(self, "重命名失败（可能与同级条目重名）")

    def _edit_check(self, check_id: int):
        from ui.scorecard_edit_dialog import ScorecardCheckDialog

        check = scorecard_service.get_check(check_id)
        if not check:
            Toast.error(self, "条目不存在")
            return
        dlg = ScorecardCheckDialog(check, parent=self)
        if dlg.exec():
            data = dlg.get_data()
            ok = scorecard_service.update_check(
                check_id,
                content=data["content"],
                key_points=data["key_points"],
                regulation_basis=data["regulation_basis"],
                review_materials=data["review_materials"],
            )
            if not ok:
                Toast.error(self, "保存失败（评级内容不能为空）")
                return
            scorecard_service.set_check_documents(check_id, data["document_ids"])
            if data.get("removed_auto_ids"):
                scorecard_service.ignore_auto_links(check_id, data["removed_auto_ids"])
            Toast.success(self, "条目已保存")
            self._refresh_check_node(check_id, data["content"])
            self._show_check(check_id)

    def _refresh_check_node(self, check_id: int, new_text: str):
        """更新树上该检查项的显示文本"""
        iterator = self._tree.findItems("", Qt.MatchContains | Qt.MatchRecursive, 0)
        for item in iterator:
            node = item.data(0, ROLE_NODE)
            if node and node[0] == "check" and node[1] == check_id:
                item.setText(0, new_text or "（无评级内容）")
                break
