#!/bin/bash
# 制度汇编管理系统 — 图形界面启动脚本
# 由 Launch_RegulationManager.desktop 和开始菜单快捷方式调用。

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_EXE="$APP_DIR/RegulationManager"

show_error() {
    if command -v zenity &>/dev/null && [ -n "${DISPLAY:-}" ]; then
        zenity --error --title="制度汇编管理系统" --text="$1"
    else
        echo "错误：$1" >&2
    fi
}

# 确保可执行权限
if [ ! -f "$APP_EXE" ]; then
    show_error "未找到程序文件 RegulationManager。请确认没有删除或移动程序文件夹中的文件。"
    exit 1
fi
chmod +x "$APP_EXE" || {
    show_error "无法获取程序执行权限。请将整个程序文件夹复制到您的个人目录后再试。"
    exit 1
}

# 启用中文输入法
export QT_IM_MODULE="${QT_IM_MODULE:-fcitx}"

# 启动程序
cd "$APP_DIR"
exec "$APP_EXE"
