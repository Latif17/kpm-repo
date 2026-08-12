#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "${PKG_DIR}/payload/bin/kterm.sh" "$@"
