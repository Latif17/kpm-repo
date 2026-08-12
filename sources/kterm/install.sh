#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing kterm..."

FW_VERSION=$(awk '{print $2}' /etc/prettyversion.txt 2>/dev/null || echo "0.0")
USE_ARMHF=$(awk -v fw="$FW_VERSION" 'BEGIN { split(fw, a, "."); if (a[1]+0 > 5 || (a[1]+0 == 5 && a[2]+0 > 16) || (a[1]+0 == 5 && a[2]+0 == 16 && a[3]+0 >= 3)) print 1; else print 0 }')

if [ "$USE_ARMHF" = "1" ]; then
    echo "Firmware >= 5.16.3 detected. Using armhf binary."
    mv "${PKG_DIR}/payload/bin/kterm_armhf" "${PKG_DIR}/payload/bin/kterm"
    rm -f "${PKG_DIR}/payload/bin/kterm_softfp"
else
    echo "Firmware < 5.16.3 detected. Using softfp binary."
    mv "${PKG_DIR}/payload/bin/kterm_softfp" "${PKG_DIR}/payload/bin/kterm"
    rm -f "${PKG_DIR}/payload/bin/kterm_armhf"
fi

echo "kterm installed successfully."
