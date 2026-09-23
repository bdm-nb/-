#!/usr/bin/env bash
# Run this in YOUR WSL (not the cloud VM). Saves all same-content handbook PDFs to the Windows desktop.
set -euo pipefail

BRANCH="cursor/visual-servo-practice-report-4530"
BASE="https://github.com/bdm-nb/-/raw/${BRANCH}"

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
  echo "No Desktop folder found. Open these in the browser:"
  echo "  $BASE/implementation_guide.pdf"
  echo "  $BASE/实施手册.pdf"
  echo "  $BASE/眼在手视觉伺服实施文档.pdf"
  exit 1
fi

download() {
  local name=$1
  local enc
  enc=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$name")
  local out="$dest/$name"
  local url="$BASE/$enc"
  if command -v curl >/dev/null; then
    curl -fsSL -o "$out" "$url"
  else
    wget -q -O "$out" "$url"
  fi
  echo "saved $out"
}

download "implementation_guide.pdf"
download "实施手册.pdf"
download "眼在手视觉伺服实施文档.pdf"
ls -la "$dest/implementation_guide.pdf" "$dest/实施手册.pdf" "$dest/眼在手视觉伺服实施文档.pdf"
