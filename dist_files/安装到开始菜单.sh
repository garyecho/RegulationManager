#!/bin/bash
# 制度汇编管理系统 — 安装到开始菜单
# 双击此文件，输入系统密码即可安装到开始菜单
set -e

APP_NAME="制度汇编管理系统"
INSTALL_DIR="${REGULATION_INSTALL_DIR:-/opt/RegulationManager}"
DESKTOP_FILE="${REGULATION_DESKTOP_FILE:-/usr/share/applications/regulation-manager.desktop}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

show_info() {
    if command -v zenity &>/dev/null && [ -n "${DISPLAY:-}" ]; then
        zenity --info --title="$APP_NAME" --text="$1" --timeout=12
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

echo "=========================================="
echo "  $APP_NAME — 安装到开始菜单"
echo "=========================================="
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "需要管理员权限来安装。"
    INSTALL_USER="$(id -un)"
    if command -v pkexec &>/dev/null; then
        exec pkexec /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/安装到开始菜单.sh"
    elif command -v sudo &>/dev/null && [ -t 0 ]; then
        exec sudo /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/安装到开始菜单.sh"
    else
        show_error "系统未提供图形授权工具 pkexec。请在本文件夹空白处右键，选择"在终端中打开"，然后输入 ./安装到开始菜单.sh 并按 Enter。"
        exit 1
    fi
fi

# 在复制文件前确定实际使用者
INSTALL_USER="${REGULATION_INSTALL_USER:-${SUDO_USER:-}}"
if [ -z "$INSTALL_USER" ]; then
    SOURCE_OWNER="$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || true)"
    if [ -n "$SOURCE_OWNER" ] && [ "$SOURCE_OWNER" != "root" ]; then
        INSTALL_USER="$SOURCE_OWNER"
    fi
fi
if [ -z "$INSTALL_USER" ] || ! id "$INSTALL_USER" &>/dev/null; then
    echo "错误：无法确定使用该程序的普通用户。"
    echo "请指定用户后重新运行：REGULATION_INSTALL_USER=用户名 sudo -E ./安装到开始菜单.sh"
    exit 1
fi

echo "[1/4] 安装程序文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -af "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/RegulationManager"
chmod +x "$INSTALL_DIR/start.sh"

# /opt 下的程序文件归 root 管理，但运行数据必须允许安装用户读写。
mkdir -p "$INSTALL_DIR/data"
chown -R "$INSTALL_USER":"$(id -gn "$INSTALL_USER")" "$INSTALL_DIR/data"

echo "[2/4] 安装应用图标 ..."
for size_dir in 256x256 128x128 64x64 48x48; do
    ICON_SRC="$SCRIPT_DIR/share/icons/hicolor/${size_dir}/apps/regulation_manager.png"
    ICON_DST="/usr/share/icons/hicolor/${size_dir}/apps/regulation_manager.png"
    if [ -f "$ICON_SRC" ]; then
        mkdir -p "$(dirname "$ICON_DST")"
        cp -f "$ICON_SRC" "$ICON_DST"
    fi
done
if [ -f "$SCRIPT_DIR/share/pixmaps/regulation_manager.png" ]; then
    cp -f "$SCRIPT_DIR/share/pixmaps/regulation_manager.png" /usr/share/pixmaps/
fi

echo "[3/4] 创建开始菜单快捷方式 ..."
# 用绝对路径创建 .desktop，不依赖任何占位符或相对路径
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Name[zh_CN]=$APP_NAME
Comment=单机版制度文件集中管理系统
Exec=$INSTALL_DIR/start.sh
Icon=regulation_manager
Terminal=false
Categories=Office;
EOF
chmod +x "$DESKTOP_FILE"

echo "[4/4] 刷新菜单 ..."
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database
fi
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache /usr/share/icons/hicolor/ 2>/dev/null || true
fi

echo ""
echo "=========================================="
echo "  安装完成！"
echo "  可以在开始菜单中找到「$APP_NAME」"
echo "  程序文件位于: $INSTALL_DIR/"
echo "=========================================="
echo ""
show_info "安装完成！现在可以从开始菜单中打开「$APP_NAME」。"
echo "提示：按 Enter 退出..."
if [ -t 0 ]; then
    read -r
fi