#!/usr/bin/env bash
set -euo pipefail

# Usage: ./release.sh 0.4.0

VERSION="${1:-}"
if [[ -z "$VERSION" ]]; then
  echo "Usage: ./release.sh <version>"
  echo "Example: ./release.sh 0.4.0"
  exit 1
fi

HOMEBREW_REPO="${HOME}/Developer/rt"
SOURCE_REPO="$(cd "$(dirname "$0")" && pwd)"

# Update version in rt script
sed -i '' "s/^RT_VERSION=\".*\"/RT_VERSION=\"${VERSION}\"/" "${SOURCE_REPO}/bin/rt"

# Commit, push, tag source repo
cd "$SOURCE_REPO"
git add -A
git commit -m "v${VERSION}" || true
git push
git tag -f "v${VERSION}"
git push origin "v${VERSION}" -f

# Wait for GitHub to generate the tarball
sleep 3

# Get sha256
SHA=$(curl -sL "https://github.com/rafgirao/remote-terminal/archive/refs/tags/v${VERSION}.tar.gz" | shasum -a 256 | awk '{print $1}')

# Update homebrew formula
cd "$HOMEBREW_REPO"
sed -i '' "s|archive/refs/tags/v.*\.tar\.gz|archive/refs/tags/v${VERSION}.tar.gz|" Formula/cli.rb
sed -i '' "s/sha256 \".*\"/sha256 \"${SHA}\"/" Formula/cli.rb
git add Formula/cli.rb
git commit -m "Bump formula to v${VERSION}"
git push

echo ""
echo "Released v${VERSION}"
echo "SHA256: ${SHA}"
echo ""
echo "Users can update with: brew upgrade rafgirao/remote-terminal/cli"
