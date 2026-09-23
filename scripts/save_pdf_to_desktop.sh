#!/usr/bin/env bash
# Run this in YOUR WSL (not the cloud VM). Saves implementation_guide.pdf to the Windows desktop.
set -euo pipefail

URL="https://github.com/bdm-nb/-/raw/cursor/visual-servo-practice-report-4530/implementation_guide.pdf"
NAME="implementation_guide.pdf"

dest=""
for d in \
  /mnt/c/Users/*/Desktop \
  /mnt/c/Users/*/OneDrive/Desktop \
  "$HOME/Desktop" \
  /home/biand/Desktop
do
  if [[ -d $d ]]; then
    dest=$d
    break
  fi
done

if [[ -z "$dest" ]]; then
  echo "No Desktop folder found. Download in the browser:"
  echo "  $URL"
  exit 1
fi

out="$dest/$NAME"
if command -v curl >/dev/null; then
  curl -fsSL -o "$out" "$URL"
else
  wget -q -O "$out" "$URL"
fi
echo "saved $out"
ls -la "$out"
