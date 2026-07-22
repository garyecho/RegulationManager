#!/bin/bash
set -euo pipefail

if [ "$EUID" -ne 0 ]; then
    echo "SKIP: install integration test requires root"
    exit 0
fi

TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

SOURCE_DIR="$TEST_ROOT/source"
INSTALL_DIR="$TEST_ROOT/opt/Regulation Manager"
DESKTOP_FILE="$TEST_ROOT/applications/regulation-manager.desktop"
mkdir -p "$SOURCE_DIR/data" "$(dirname "$DESKTOP_FILE")"
cp "$(cd "$(dirname "$0")/.." && pwd)/dist_files/install.sh" "$SOURCE_DIR/install.sh"
printf '#!/bin/bash\n' > "$SOURCE_DIR/start.sh"
printf '#!/bin/bash\n' > "$SOURCE_DIR/RegulationManager"
chmod +x "$SOURCE_DIR/install.sh"
chown -R root:root "$SOURCE_DIR"

if REGULATION_INSTALL_DIR="$INSTALL_DIR" \
   REGULATION_DESKTOP_FILE="$DESKTOP_FILE" \
   "$SOURCE_DIR/install.sh" </dev/null; then
    echo "FAIL: root-only install unexpectedly succeeded without an install user"
    exit 1
fi

test ! -e "$DESKTOP_FILE"
test ! -e "$INSTALL_DIR"
echo "PASS: root-only install fails before creating an unusable desktop entry"
