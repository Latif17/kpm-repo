#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting kterm launch..." > /mnt/us/kpm_kterm_launch.log
export DISPLAY=${DISPLAY:-:0}
# Clear the e-ink screen to white before launching. Kterm's GTK theme might have a transparent background, 
# which causes it to inherit KPM's background (resulting in black-on-black text).
eips -c || true
exec sh "${PKG_DIR}/payload/bin/kterm.sh" "$@" >> /mnt/us/kpm_kterm_launch.log 2>&1
