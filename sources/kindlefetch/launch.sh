#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
KTERM_BIN="${PKG_DIR}/../kterm/bin/kterm"

if [ ! -x "$KTERM_BIN" ]; then
    echo "ERROR: kterm executable not found at $KTERM_BIN or not executable. Please ensure kterm is installed." >&2
    exit 1
fi

if [ ! -f "${PKG_DIR}/payload/bin/kindlefetch.sh" ]; then
    echo "ERROR: kindlefetch.sh not found at ${PKG_DIR}/payload/bin/kindlefetch.sh" >&2
    exit 1
fi

# Run the kindlefetch shell script using kterm, similar to how it was invoked in the original KUAL extension.
exec "$KTERM_BIN" -e "bash ${PKG_DIR}/payload/bin/kindlefetch.sh" -k 1 -o U -s 7 "$@"
