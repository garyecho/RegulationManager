#!/bin/bash
# 制度汇编管理系统 — 图形界面启动脚本
# 由 Launch_RegulationManager.desktop 调用。

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

# 设置 Qt 环境变量
export QT_IM_MODULE="${QT_IM_MODULE:-fcitx}"
export QT_QPA_PLATFORM_PLUGIN_PATH="$APP_DIR/_internal/PyQt5/Qt/plugins/platforms"
export LD_LIBRARY_PATH="$APP_DIR/_internal:${LD_LIBRARY_PATH:-}"

# Wayland 会话下自动切换到 xcb（打包的 Qt 不含 wayland 插件）
if [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then
    export QT_QPA_PLATFORM=xcb
fi

# 启动程序
cd "$APP_DIR"
exec "$APP_EXE"
