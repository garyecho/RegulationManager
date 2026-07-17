#!/bin/bash
# ==========================================
#   RegulationManager - Linux Build Script
#   Usage: ./build_linux.sh [clone|pull|build|all]
# ==========================================
set -e

# ── 配置 ──
REPO_URL="http://192.168.10.238:30080/development/regulationmanager.git"
BUILD_DIR="$HOME/RegulationManager_build"
BRANCH="master"

# 检测架构
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    ARCH_NAME="x64"
elif [ "$ARCH" = "aarch64" ]; then
    ARCH_NAME="ARM64"
else
    echo "不支持的架构: $ARCH"
    exit 1
fi
OUTPUT_NAME="RegulationManager_Kylin_${ARCH_NAME}"

echo "=========================================="
echo "  RegulationManager Linux Build"
echo "  架构: $ARCH ($ARCH_NAME)"
echo "  输出: $OUTPUT_NAME"
echo "=========================================="

# ── 命令解析 ──
ACTION="${1:-all}"

clone_repo() {
    echo "[1/4] 克隆仓库..."
    if [ -d "$BUILD_DIR/.git" ]; then
        echo "  仓库已存在，跳过克隆"
    else
        git clone -b "$BRANCH" "$REPO_URL" "$BUILD_DIR"
        echo "  克隆完成"
    fi
}

pull_latest() {
    echo "[2/4] 拉取最新代码..."
    cd "$BUILD_DIR"
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
    echo "  当前版本: $(git log --oneline -1)"
}

setup_env() {
    echo "[3/4] 配置 Python 环境..."
    cd "$BUILD_DIR"

    # 创建虚拟环境（如果不存在）
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo "  虚拟环境已创建"
    fi

    source .venv/bin/activate

    # 安装依赖
    pip install --upgrade pip -q
    pip install PyQt5 SQLAlchemy PyMuPDF python-docx jieba pyinstaller -q
    echo "  依赖安装完成"
    echo "  Python: $(python3 --version)"
    echo "  PyQt5: $(python3 -c 'import PyQt5.QtCore; print(PyQt5.QtCore.PYQT_VERSION_STR)')"
}

build() {
    echo "[4/4] 打包构建..."
    cd "$BUILD_DIR"
    source .venv/bin/activate

    # 清理旧构建
    rm -rf build dist/$OUTPUT_NAME

    # 设置架构环境变量（spec 文件中使用）
    export BUILD_ARCH="Kylin_${ARCH_NAME}"

    # 执行 PyInstaller
    pyinstaller RegulationManager.spec --clean --noconfirm

    # 复制交付文件
    mkdir -p "dist/$OUTPUT_NAME/data/documents"
    mkdir -p "dist/$OUTPUT_NAME/data/backups"
    mkdir -p "dist/$OUTPUT_NAME/data/logs"
    cp -f dist_files/README.txt "dist/$OUTPUT_NAME/"
    cp -f dist_files/backup.txt "dist/$OUTPUT_NAME/"
    cp -f dist_files/CHANGELOG.txt "dist/$OUTPUT_NAME/"

    # Linux 下 Qt 插件路径可能不同，清理不必要的文件
    rm -rf "dist/$OUTPUT_NAME/_internal/PyQt5/Qt5/qml" 2>/dev/null || true
    rm -rf "dist/$OUTPUT_NAME/_internal/PyQt5/Qt5/translations" 2>/dev/null || true

    echo ""
    echo "=========================================="
    echo "  构建完成！"
    echo "  输出目录: $BUILD_DIR/dist/$OUTPUT_NAME/"
    echo "  可执行文件: $BUILD_DIR/dist/$OUTPUT_NAME/RegulationManager"
    echo "=========================================="
}

# ── 执行 ──
case "$ACTION" in
    clone)
        clone_repo
        ;;
    pull)
        pull_latest
        ;;
    build)
        build
        ;;
    all)
        clone_repo
        pull_latest
        setup_env
        build
        ;;
    *)
        echo "用法: ./build_linux.sh [clone|pull|build|all]"
        echo "  clone  - 仅克隆仓库"
        echo "  pull   - 仅拉取最新代码"
        echo "  build  - 仅打包构建（需要先 clone + setup_env）"
        echo "  all    - 完整流程（默认）"
        exit 1
        ;;
esac
