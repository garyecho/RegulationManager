#!/bin/bash
# RegulationManager Docker build script
# Usage: ./build_docker.sh [x86_64|arm64]

ARCH="${1:-x86_64}"

if [ "$ARCH" = "arm64" ]; then
    ARCH_LABEL="Kylin_ARM64"
elif [ "$ARCH" = "x86_64" ]; then
    ARCH_LABEL="Kylin_x64"
else
    echo "Unknown arch: $ARCH"
    exit 1
fi

echo "Building for $ARCH_LABEL..."

cd /build

# Build
export BUILD_ARCH="$ARCH_LABEL"
pyinstaller RegulationManager.spec --clean --noconfirm

# Prepare dist
mkdir -p "dist/RegulationManager_${ARCH_LABEL}/data/documents"
mkdir -p "dist/RegulationManager_${ARCH_LABEL}/data/backups"
mkdir -p "dist/RegulationManager_${ARCH_LABEL}/data/logs"

# Clean up unnecessary Qt files
rm -rf "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/qml" 2>/dev/null || true
rm -rf "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/translations" 2>/dev/null || true

# Copy release files
cp dist_files/README.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/backup.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/CHANGELOG.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/start.sh "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/install.sh "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
chmod +x "dist/RegulationManager_${ARCH_LABEL}/start.sh"
chmod +x "dist/RegulationManager_${ARCH_LABEL}/install.sh"

# Copy fcitx input method plugin for Chinese input on Kylin
FCITX_PLUGIN=$(find /usr -name "libfcitxplatforminputcontextplugin.so" 2>/dev/null | head -1)
if [ -n "$FCITX_PLUGIN" ]; then
    mkdir -p "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/plugins/platforminputcontexts"
    cp "$FCITX_PLUGIN" "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/plugins/platforminputcontexts/"
fi

# Show size and create tar.gz archive (inside container to avoid Windows corruption)
echo ""
echo "=========================================="
echo "  Build complete: dist/RegulationManager_${ARCH_LABEL}/"
echo "=========================================="
du -sh "dist/RegulationManager_${ARCH_LABEL}/"

echo ""
echo "Creating tar.gz archive..."
cd dist
tar czf "RegulationManager_${ARCH_LABEL}.tar.gz" "RegulationManager_${ARCH_LABEL}/"
echo "  Archive: dist/RegulationManager_${ARCH_LABEL}.tar.gz"
du -sh "RegulationManager_${ARCH_LABEL}.tar.gz"
