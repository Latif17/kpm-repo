#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"${SCRIPT_DIR}/../../kterm/bin/kterm" -e "bash ${SCRIPT_DIR}/bin/kindlefetch.sh" -k 1 -o U -s 7
