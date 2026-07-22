#!/bin/bash
# ==========================================
#   制度汇编管理系统 — 安装到开始菜单
#   使用: 双击运行此脚本，或执行 ./install.sh
# ==========================================
set -e

APP_NAME="制度汇编管理系统"
INSTALL_DIR="${REGULATION_INSTALL_DIR:-/opt/RegulationManager}"
DESKTOP_FILE="${REGULATION_DESKTOP_FILE:-/usr/share/applications/regulation-manager.desktop}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "  $APP_NAME — 安装到开始菜单"
echo "=========================================="
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "需要管理员权限来安装。"
    INSTALL_USER="$(id -un)"
    if command -v pkexec &>/dev/null; then
        exec pkexec /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/install.sh"
    elif command -v sudo &>/dev/null; then
        exec sudo /usr/bin/env REGULATION_INSTALL_USER="$INSTALL_USER" "$SCRIPT_DIR/install.sh"
    else
        echo "请以 root 身份运行此脚本：sudo ./install.sh"
        exit 1
    fi
fi

# 在复制文件前确定实际使用者，避免留下 root 所有且不可用的半安装目录。
INSTALL_USER="${REGULATION_INSTALL_USER:-${SUDO_USER:-}}"
if [ -z "$INSTALL_USER" ]; then
    SOURCE_OWNER="$(stat -c '%U' "$SCRIPT_DIR" 2>/dev/null || true)"
    if [ -n "$SOURCE_OWNER" ] && [ "$SOURCE_OWNER" != "root" ]; then
        INSTALL_USER="$SOURCE_OWNER"
    fi
fi
if [ -z "$INSTALL_USER" ] || ! id "$INSTALL_USER" &>/dev/null; then
    echo "错误：无法确定使用该程序的普通用户。"
    echo "请指定用户后重新运行：REGULATION_INSTALL_USER=用户名 sudo -E ./install.sh"
    exit 1
fi

echo "[1/3] 安装程序文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -af "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/start.sh"
chmod +x "$INSTALL_DIR/RegulationManager"

# /opt 下的程序文件归 root 管理，但运行数据必须允许安装用户读写。
mkdir -p "$INSTALL_DIR/data"
chown -R "$INSTALL_USER":"$(id -gn "$INSTALL_USER")" "$INSTALL_DIR/data"

echo "[2/3] 创建开始菜单快捷方式 ..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Name[zh_CN]=$APP_NAME
Comment=单机版制度文件集中管理系统
Exec="$INSTALL_DIR/start.sh"
Path=$INSTALL_DIR
Icon=
Terminal=false
Categories=Office;
EOF
chmod +x "$DESKTOP_FILE"

echo "[3/3] 刷新菜单 ..."
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database
fi

echo ""
echo "=========================================="
echo "  安装完成！"
echo "  可以在开始菜单中找到「$APP_NAME」"
echo "  程序文件位于: $INSTALL_DIR/"
echo "=========================================="
echo ""
echo "提示：按 Enter 退出..."
if [ -t 0 ]; then
    read -r
fi
