#!/bin/sh
set -e

PKG_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing KindleFetch..."
# KindleFetch is now portable and runs directly from the package directory.
# No files need to be copied to /mnt/us/extensions.
echo "KindleFetch installed successfully."
