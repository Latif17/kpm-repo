#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting kterm launch..." > /mnt/us/kpm_kterm_launch.log
export DISPLAY=${DISPLAY:-:0}
exec sh "${PKG_DIR}/payload/bin/kterm.sh" "$@" >> /mnt/us/kpm_kterm_launch.log 2>&1
