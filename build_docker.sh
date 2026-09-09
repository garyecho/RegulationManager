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

# Fix PyMuPDF symlinks: replace broken symlinks with actual files
echo "Fixing PyMuPDF symlinks..."
find "dist/RegulationManager_${ARCH_LABEL}/_internal" -name "libmupdf*" -type l | while read link; do
    # Try to find the actual file
    target=$(readlink -f "$link" 2>/dev/null || readlink "$link" 2>/dev/null)
    
    if [ -n "$target" ] && [ -f "$target" ]; then
        echo "  Replacing symlink: $(basename "$link") -> $(basename "$target")"
        rm -f "$link"
        cp -a "$target" "$link"
        chmod 755 "$link"
    else
        # If symlink is broken, try to find the library in pymupdf package
        link_name=$(basename "$link")
        pymupdf_lib=$(find /usr -name "$link_name" -path "*/pymupdf/*" 2>/dev/null | head -1)
        
        if [ -n "$pymupdf_lib" ] && [ -f "$pymupdf_lib" ]; then
            echo "  Found in pymupdf package: $link_name"
            rm -f "$link"
            cp -a "$pymupdf_lib" "$link"
            chmod 755 "$link"
        else
            echo "  Warning: Broken symlink found, removing: $link"
            rm -f "$link"
        fi
    fi
done

# Also fix any other broken symlinks in the distribution
echo "Checking for other broken symlinks..."
find "dist/RegulationManager_${ARCH_LABEL}/_internal" -type l | while read link; do
    if [ ! -e "$link" ]; then
        echo "  Removing broken symlink: $link"
        rm -f "$link"
    fi
done

# Clean up unnecessary Qt files
rm -rf "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/qml" 2>/dev/null || true
rm -rf "dist/RegulationManager_${ARCH_LABEL}/_internal/PyQt5/Qt5/translations" 2>/dev/null || true

# Copy release files
cp dist_files/README.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/backup.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/CHANGELOG.txt "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/start.sh "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/install.sh "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/Launch_RegulationManager.desktop "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
cp dist_files/Install_RegulationManager.desktop "dist/RegulationManager_${ARCH_LABEL}/" 2>/dev/null || true
chmod +x "dist/RegulationManager_${ARCH_LABEL}/start.sh"
chmod +x "dist/RegulationManager_${ARCH_LABEL}/install.sh"
chmod +x "dist/RegulationManager_${ARCH_LABEL}/Launch_RegulationManager.desktop"
chmod +x "dist/RegulationManager_${ARCH_LABEL}/Install_RegulationManager.desktop"

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
