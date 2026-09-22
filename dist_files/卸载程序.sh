#!/bin/bash
# 制度汇编管理系统 — 卸载
# 双击此文件，输入系统密码即可从系统中移除程序
set -e

APP_NAME="制度汇编管理系统"
INSTALL_DIR="${REGULATION_INSTALL_DIR:-/opt/RegulationManager}"
DESKTOP_FILE="${REGULATION_DESKTOP_FILE:-/usr/share/applications/regulation-manager.desktop}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

wait_for_exit() {
    echo ""
    echo "按 Enter 关闭窗口..."
    if [ -t 0 ]; then
        read -r
    else
        sleep 30
    fi
}

show_info() {
    if command -v zenity &>/dev/null && [ -n "${DISPLAY:-}" ]; then
        zenity --info --title="$APP_NAME" --text="$1" --timeout=30
    else
        echo "$1"
    fi
}

show_error() {
    if command -v zenity &>/dev/null && [ -n "${DISPLAY:-}" ]; then
        zenity --error --title="$APP_NAME" --text="$1"
    else
        echo "错误：$1" >&2
    fi
}

show_confirm() {
    if command -v zenity &>/dev/null && [ -n "${DISPLAY:-}" ]; then
        zenity --question --title="$APP_NAME" \
            --text="$1" \
            --ok-label="确认卸载" --cancel-label="取消"
        return $?
    else
        echo "$1"
        echo "输入 y 确认卸载，其他键取消："
        read -r answer
        [ "$answer" = "y" ] || [ "$answer" = "Y" ]
    fi
}

echo "=========================================="
echo "  $APP_NAME — 卸载"
echo "=========================================="
echo ""

# 检查是否已安装
if [ ! -d "$INSTALL_DIR" ]; then
    show_error "未找到已安装的程序目录 $INSTALL_DIR，可能尚未安装或已被移除。"
    wait_for_exit
    exit 1
fi

# 确认卸载
if ! show_confirm "即将卸载「$APP_NAME」：\n\n• 删除程序目录：$INSTALL_DIR\n• 删除开始菜单快捷方式\n• 删除系统图标\n\n程序数据（制度文件、数据库）将一并删除。\n如需保留数据，请先手动备份 $INSTALL_DIR/data/ 目录。\n\n确认卸载？"; then
    echo "已取消卸载。"
    exit 0
fi

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "需要管理员权限来卸载。"
    INSTALL_USER="$(id -un)"
    if command -v pkexec &>/dev/null; then
        exec pkexec /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/卸载程序.sh"
    elif command -v sudo &>/dev/null && [ -t 0 ]; then
        exec sudo /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/卸载程序.sh"
    else
        show_error "系统未提供图形授权工具 pkexec。请在本文件夹空白处右键，选择"在终端中打开"，然后输入 ./卸载程序.sh 并按 Enter。"
        wait_for_exit
        exit 1
    fi
fi

echo "[1/3] 删除程序文件 ..."
rm -rf "$INSTALL_DIR"

echo "[2/3] 删除开始菜单快捷方式 ..."
rm -f "$DESKTOP_FILE"

echo "[3/3] 清理系统图标 ..."
for size_dir in 256x256 128x128 64x64 48x48; do
    rm -f "/usr/share/icons/hicolor/${size_dir}/apps/regulation_manager.png"
done
rm -f /usr/share/pixmaps/regulation_manager.png
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database
fi

echo ""
echo "=========================================="
echo "  卸载完成！"
echo "  「$APP_NAME」已从系统中移除。"
echo "=========================================="
echo ""
show_info "卸载完成！「$APP_NAME」已从系统中移除。"
wait_for_exit