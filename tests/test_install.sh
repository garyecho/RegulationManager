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
printf 'existing data\n' > "$SOURCE_DIR/data/regulation.db"
chmod +x "$SOURCE_DIR/install.sh"

INSTALL_USER="nobody"
if ! id "$INSTALL_USER" &>/dev/null; then
    echo "SKIP: test user nobody is unavailable"
    exit 0
fi

REGULATION_INSTALL_USER="$INSTALL_USER" \
REGULATION_INSTALL_DIR="$INSTALL_DIR" \
REGULATION_DESKTOP_FILE="$DESKTOP_FILE" \
    "$SOURCE_DIR/install.sh" </dev/null

test -x "$INSTALL_DIR/RegulationManager"
test -x "$INSTALL_DIR/start.sh"
test -f "$DESKTOP_FILE"
grep -Fq "Exec=\"$INSTALL_DIR/start.sh\"" "$DESKTOP_FILE"
grep -Fq "Path=$INSTALL_DIR" "$DESKTOP_FILE"
test "$(stat -c '%U' "$INSTALL_DIR/data")" = "$INSTALL_USER"
test "$(stat -c '%U' "$INSTALL_DIR/data/regulation.db")" = "$INSTALL_USER"

echo "PASS: install data directory is writable by the install user"
