#!/bin/bash
# ==========================================
#   制度汇编管理系统 — 麒麟 Linux 启动脚本
#   使用方式: ./run.sh
# ==========================================

DIR="$(cd "$(dirname "$0")" && pwd)"
EXE="$DIR/RegulationManager"

# 确保可执行权限
[ -f "$EXE" ] && chmod +x "$EXE"

# 启用中文输入法
export QT_IM_MODULE=fcitx

# 启动
cd "$DIR"
exec "$EXE"
