#!/bin/bash
# 制度汇编管理系统 — 一键启动（双击即可运行）
# 自动处理权限、输入法、运行环境

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_EXE="$APP_DIR/RegulationManager"

# 确保可执行权限
[ -f "$APP_EXE" ] && chmod +x "$APP_EXE"
[ -f "$APP_DIR/start.sh" ] && chmod +x "$APP_DIR/start.sh"
[ -f "$APP_DIR/install.sh" ] && chmod +x "$APP_DIR/install.sh"

# 启用中文输入法
export QT_IM_MODULE="${QT_IM_MODULE:-fcitx}"

# 启动程序
cd "$APP_DIR"
exec "$APP_EXE"
