#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
SHARE_DIR="${HOME}/.local/share/rt"
CACHE_DIR="${HOME}/.cache/rt"

echo ""
echo "  Uninstalling Remote Terminal..."

rm -f "${BIN_DIR}/rt"
rm -rf "$SHARE_DIR"
rm -rf "$CACHE_DIR"

echo "  Done."
echo ""
