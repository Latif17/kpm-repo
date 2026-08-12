#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"

# Run the kindlefetch shell script using kterm, similar to how it was invoked in the original KUAL extension.
exec "${PKG_DIR}/../kterm/bin/kterm" -e "bash ${PKG_DIR}/payload/bin/kindlefetch.sh" -k 1 -o U -s 7 "$@"
