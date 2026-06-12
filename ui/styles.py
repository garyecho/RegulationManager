"""
UI 样式常量 — 2026 浅色现代企业级主题
与 resources/styles/light.qss 配合使用
色板：Primary #0066CC  Accent #0078D4  Success #28A745  Danger #DC3545
"""

# 通用中文字体族
_FONT = ('"Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI Variable", '
         '"Segoe UI", "SimHei", "DengXian", sans-serif')

# ── 色板 ──
_PRIMARY = "#0066CC"           # 主色蓝
_PRIMARY_HOVER = "#0052A3"     # 主色悬停
_PRIMARY_DARK = "#003D7A"      # 主色按下
_PRIMARY_LIGHT = "#E3F2FD"     # 主色浅底（选中/高亮）
_ACCENT = "#0078D4"            # 强调色
_BG = "#F8F9FA"                # 主背景
_SURFACE = "#FFFFFF"           # 卡片/表格/对话框背景
_HOVER = "#F5F7FA"             # 悬停背景
_TEXT = "#212529"               # 主文字
_TEXT_SEC = "#666666"           # 次要文字
_TEXT_MUTED = "#999999"         # 弱化文字
_BORDER = "#E0E0E0"            # 边框
_BORDER_LIGHT = "#F0F0F0"      # 轻边框
_SUCCESS = "#28A745"           # 成功/现行有效
_SUCCESS_BG = "#E8F5E9"        # 成功浅底
_DANGER = "#DC3545"            # 危险/已废止
_DANGER_BG = "#FDECEA"         # 危险浅底
_WARNING = "#FFC107"           # 警告

# ── 字号标准 ──
FS_BODY = "13px"               # 正文
FS_TITLE = "16px"              # 标题
FS_SUBTITLE = "15px"           # 副标题/分组标题
FS_SMALL = "12px"              # 小字/表头/分页
FS_CAPTION = "11px"            # 极小字

# ── 文件选择标签 ──
FILE_LABEL_DEFAULT = (
    f"color: {_TEXT_MUTED}; padding: 8px; "
    f"font-size: {FS_BODY}; font-family: {_FONT};"
)
FILE_LABEL_SELECTED_LIGHT = (
    f"color: {_TEXT}; padding: 8px; font-weight: bold; "
    f"font-size: {FS_BODY}; font-family: {_FONT};"
)

# ── 对话框按钮（次要） ──
DIALOG_BTN_SECONDARY = (
    f"QPushButton {{ background: {_BG}; color: {_TEXT}; "
    f"border: 1px solid {_BORDER}; border-radius: 6px; "
    f"padding: 8px 20px; font-size: {FS_BODY}; font-family: {_FONT}; }} "
    f"QPushButton:hover {{ background: #EEF0F2; border-color: #CCCCCC; }}"
)

# ── 面板工具栏 ──
PANEL_TOOLBAR_LIGHT = (
    f"background-color: {_SURFACE}; border-bottom: 1px solid {_BORDER}; "
    f"padding: 8px; font-family: {_FONT};"
)
PANEL_TITLE_LIGHT = (
    f"font-size: {FS_TITLE}; font-weight: bold; color: {_TEXT}; "
    f"font-family: {_FONT};"
)
PANEL_COUNT_LIGHT = (
    f"color: {_TEXT_MUTED}; font-size: {FS_SMALL}; margin-left: 8px; "
    f"font-family: {_FONT};"
)
PANEL_SORT_LABEL_LIGHT = (
    f"color: {_TEXT_SEC}; font-size: {FS_SMALL}; font-family: {_FONT};"
)
PANEL_SEPARATOR_LIGHT = (
    f"color: {_BORDER}; margin: 0 4px; font-family: {_FONT};"
)


def tool_btn_style(active: bool) -> str:
    """排序/筛选按钮样式"""
    if active:
        return (
            f"QPushButton {{ background: {_PRIMARY_LIGHT}; color: {_PRIMARY}; "
            f"border: 1px solid #B3D9F2; border-radius: 6px; "
            f"padding: 4px 12px; font-size: {FS_SMALL}; font-weight: bold; "
            f"font-family: {_FONT}; }}"
        )
    return (
        f"QPushButton {{ background: transparent; color: {_TEXT_MUTED}; "
        f"border: 1px solid transparent; border-radius: 6px; "
        f"padding: 4px 12px; font-size: {FS_SMALL}; font-family: {_FONT}; }} "
        f"QPushButton:hover {{ background: {_HOVER}; color: {_TEXT}; }}"
    )


def view_btn_style(active: bool) -> str:
    """列表/卡片视图切换按钮"""
    if active:
        return (
            f"QPushButton {{ background: {_PRIMARY}; color: #fff; border: none; "
            f"border-radius: 6px; font-size: 16px; font-family: {_FONT}; }}"
        )
    return (
        f"QPushButton {{ background: {_BG}; color: {_TEXT_MUTED}; "
        f"border: 1px solid {_BORDER}; border-radius: 6px; font-size: 16px; "
        f"font-family: {_FONT}; }} "
        f"QPushButton:hover {{ background: #EEF0F2; color: {_TEXT}; }}"
    )


# ── 分页按钮 ──
PAGE_BTN_LIGHT = (
    f"QPushButton {{ background: {_SURFACE}; color: {_TEXT_SEC}; "
    f"border: 1px solid {_BORDER}; border-radius: 6px; "
    f"padding: 4px 14px; font-size: {FS_SMALL}; font-family: {_FONT}; }}"
    f"QPushButton:hover {{ background: {_HOVER}; }}"
)
PAGE_LABEL_LIGHT = (
    f"color: {_TEXT_MUTED}; font-size: {FS_SMALL}; font-family: {_FONT};"
)

# ── 侧边栏 ──
SIDEBAR_CAT_LABEL_LIGHT = (
    f"color: {_PRIMARY}; font-size: {FS_CAPTION}; "
    f"padding: 12px 16px 4px 16px; font-weight: bold; "
    f"font-family: {_FONT};"
)
SIDEBAR_STATS_LIGHT = (
    f"color: {_TEXT_MUTED}; font-size: {FS_CAPTION}; padding: 12px 16px; "
    f"font-family: {_FONT};"
)
SIDEBAR_ADD_CAT_BTN = (
    f"QPushButton {{ background: transparent; color: {_PRIMARY}; "
    f"border: 1px dashed {_BORDER}; border-radius: 8px; "
    f"padding: 8px 16px; text-align: center; margin: 8px 12px; "
    f"font-family: {_FONT}; }}"
    f"QPushButton:hover {{ background-color: {_PRIMARY_LIGHT}; }}"
)

# ── 搜索栏容器 ──
SEARCH_BAR_CONTAINER_LIGHT = (
    f"background: {_SURFACE}; border-bottom: 1px solid {_BORDER}; "
    f"font-family: {_FONT};"
)
