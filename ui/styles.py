"""
UI 样式常量 — 深色主题适配
"""

# 通用中文字体族
_FONT = ('"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI Variable", '
         '"Segoe UI", "SimHei", sans-serif')

# ── 深色主题色板 ──
_BG_PRIMARY = "#0f172a"      # 最深背景
_BG_SECONDARY = "#1e293b"    # 次级背景（侧边栏、卡片）
_BG_TERTIARY = "#334155"     # 三级背景（hover、分割）
_TEXT_PRIMARY = "#e2e8f0"     # 主文字
_TEXT_SECONDARY = "#94a3b8"   # 次要文字
_TEXT_MUTED = "#64748b"       # 弱化文字
_ACCENT = "#6366f1"          # 主强调色
_ACCENT_HOVER = "#818cf8"    # 强调色 hover
_BORDER = "#334155"          # 边框
_SUCCESS = "#34d399"         # 成功绿
_WARNING = "#fbbf24"         # 警告黄
_ERROR = "#f87171"           # 错误红

# ── 文件选择标签 ──
FILE_LABEL_DEFAULT = f"color: {_TEXT_MUTED}; padding: 8px; font-family: {_FONT};"
FILE_LABEL_SELECTED_LIGHT = f"color: {_TEXT_PRIMARY}; padding: 8px; font-weight: bold; font-family: {_FONT};"

# ── 对话框按钮 ──
DIALOG_BTN_SECONDARY = (
    f"QPushButton {{ background: {_BG_TERTIARY}; color: {_TEXT_PRIMARY}; "
    f"border: 1px solid #475569; border-radius: 8px; padding: 8px 20px; "
    f"font-family: {_FONT}; }} "
    f"QPushButton:hover {{ background: #475569; border-color: {_ACCENT}; }}"
)

# ── 工具栏/面板 ──
PANEL_TOOLBAR_LIGHT = (
    f"background-color: {_BG_SECONDARY}; border-bottom: 1px solid {_BORDER}; "
    f"padding: 8px; font-family: {_FONT};"
)
PANEL_TITLE_LIGHT = f"font-size: 16px; font-weight: bold; color: {_TEXT_PRIMARY}; font-family: {_FONT};"
PANEL_COUNT_LIGHT = f"color: {_TEXT_MUTED}; font-size: 13px; margin-left: 8px; font-family: {_FONT};"
PANEL_SORT_LABEL_LIGHT = f"color: {_TEXT_SECONDARY}; font-size: 12px; font-family: {_FONT};"
PANEL_SEPARATOR_LIGHT = f"color: #475569; margin: 0 4px; font-family: {_FONT};"


def tool_btn_style(active: bool) -> str:
    if active:
        return (f"QPushButton {{ background: rgba(99,102,241,0.15); color: #818cf8; "
                f"border: 1px solid rgba(99,102,241,0.3); border-radius: 6px; padding: 4px 12px; "
                f"font-size: 12px; font-weight: bold; font-family: {_FONT}; }}")
    return (f"QPushButton {{ background: transparent; color: {_TEXT_MUTED}; "
            f"border: 1px solid transparent; border-radius: 6px; padding: 4px 12px; "
            f"font-size: 12px; font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: {_BG_TERTIARY}; color: {_TEXT_PRIMARY}; }}")


def view_btn_style(active: bool) -> str:
    if active:
        return (f"QPushButton {{ background: {_ACCENT}; color: #fff; border: none; "
                f"border-radius: 6px; font-size: 16px; font-family: {_FONT}; }}")
    return (f"QPushButton {{ background: {_BG_TERTIARY}; color: {_TEXT_MUTED}; "
            f"border: 1px solid #475569; border-radius: 6px; font-size: 16px; "
            f"font-family: {_FONT}; }} "
            f"QPushButton:hover {{ background: #475569; color: {_TEXT_PRIMARY}; }}")


# ── 分页按钮 ──
PAGE_BTN_LIGHT = (
    f"QPushButton {{ background: {_BG_TERTIARY}; color: {_TEXT_SECONDARY}; "
    f"border: 1px solid #475569; border-radius: 6px; padding: 4px 12px; "
    f"font-size: 12px; font-family: {_FONT}; }}"
)
PAGE_LABEL_LIGHT = f"color: {_TEXT_MUTED}; font-size: 12px; font-family: {_FONT};"

# ── 侧边栏 ──
SIDEBAR_CAT_LABEL_LIGHT = (
    f"color: #818cf8; font-size: 11px; "
    f"padding: 12px 16px 4px 16px; font-weight: bold; "
    f"font-family: {_FONT};"
)
SIDEBAR_STATS_LIGHT = (
    f"color: {_TEXT_MUTED}; font-size: 11px; padding: 12px 16px; "
    f"font-family: {_FONT};"
)
SIDEBAR_ADD_CAT_BTN = (
    f"QPushButton {{ background: transparent; color: #818cf8; "
    f"border: 1px dashed #475569; border-radius: 8px; "
    f"padding: 8px 16px; text-align: center; margin: 8px 12px; "
    f"font-family: {_FONT}; }}"
    f"QPushButton:hover {{ background-color: rgba(99,102,241,0.1); color: #a5b4fc; }}"
)

# ── 搜索栏容器 ──
SEARCH_BAR_CONTAINER_LIGHT = (
    f"background: {_BG_SECONDARY}; border-bottom: 1px solid {_BORDER}; "
    f"font-family: {_FONT};"
)
