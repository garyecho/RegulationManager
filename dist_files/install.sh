#!/bin/bash
# ==========================================
#   制度汇编管理系统 — 安装到开始菜单
#   使用: 双击运行此脚本，或执行 ./安装到开始菜单.sh
# ==========================================
set -e

APP_NAME="制度汇编管理系统"
INSTALL_DIR="/opt/RegulationManager"
DESKTOP_FILE="/usr/share/applications/regulation-manager.desktop"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "  $APP_NAME — 安装到开始菜单"
echo "=========================================="
echo ""

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "需要管理员权限来安装。"
    if command -v pkexec &>/dev/null; then
        exec pkexec "$0"
    elif command -v sudo &>/dev/null; then
        exec sudo "$0"
    else
        echo "请以 root 身份运行此脚本：sudo ./install.sh"
        exit 1
    fi
fi

echo "[1/3] 安装程序文件到 $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
cp -af "$SCRIPT_DIR"/* "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/start.sh"
chmod +x "$INSTALL_DIR/RegulationManager"

echo "[2/3] 创建开始菜单快捷方式 ..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Name[zh_CN]=$APP_NAME
Comment=单机版制度文件集中管理系统
Exec=$INSTALL_DIR/start.sh
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
read -r
