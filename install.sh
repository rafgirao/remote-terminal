#!/usr/bin/env bash
set -euo pipefail

REPO="rafgirao/remote-terminal"
INSTALL_DIR="${HOME}/.local"
BIN_DIR="${INSTALL_DIR}/bin"
SHARE_DIR="${INSTALL_DIR}/share/rt"

echo ""
echo "  Installing Remote Terminal..."
echo ""

# Check dependencies
missing=()
for dep in tmux ttyd caddy qrencode python3; do
  command -v "$dep" &>/dev/null || missing+=("$dep")
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "  Missing dependencies: ${missing[*]}"
  echo ""
  if command -v brew &>/dev/null; then
    read -r -p "  Install them with Homebrew? [Y/n] " answer </dev/tty
    case "${answer:-Y}" in
      [Yy]|"")
        for dep in "${missing[@]}"; do
          [[ "$dep" == "python3" ]] && dep="python@3"
          echo "  Installing ${dep}..."
          brew install "$dep" 2>/dev/null
        done
        ;;
      *)
        echo "  Please install: ${missing[*]}"
        exit 1
        ;;
    esac
  else
    echo "  Please install them manually: ${missing[*]}"
    exit 1
  fi
fi

# Download latest release
echo "  Downloading latest release..."
TMPDIR=$(mktemp -d)
curl -sL "https://github.com/${REPO}/archive/refs/heads/main.tar.gz" | tar xz -C "$TMPDIR"
SRC="${TMPDIR}/remote-terminal-main"

# Install
mkdir -p "$BIN_DIR" "$SHARE_DIR"
cp "$SRC/bin/rt" "$BIN_DIR/rt"
chmod +x "$BIN_DIR/rt"
cp "$SRC/share/rt/"* "$SHARE_DIR/"
chmod +x "$SHARE_DIR/tmux-client.sh"

# Cleanup
rm -rf "$TMPDIR"

# Check PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  echo ""
  echo "  Add this to your shell profile (~/.zshrc or ~/.bashrc):"
  echo ""
  echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
fi

echo "  Remote Terminal installed!"
echo ""
echo "  Start a session with: rt"
echo ""
