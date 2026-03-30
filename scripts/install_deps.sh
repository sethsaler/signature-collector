#!/usr/bin/env bash
# Install system packages (Tesseract, LibreOffice, Tk) and Python deps for signature-packet.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/OWNER/REPO/BRANCH/scripts/install_deps.sh | bash
# Or from a clone:
#   bash scripts/install_deps.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

have() { command -v "$1" >/dev/null 2>&1; }

install_apt() {
  export DEBIAN_FRONTEND=noninteractive
  sudo apt-get update -qq
  sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    tesseract-ocr \
    libreoffice-writer
}

install_dnf() {
  sudo dnf install -y \
    python3 \
    python3-pip \
    python3-tkinter \
    tesseract \
    libreoffice-writer
}

install_brew() {
  brew install tesseract || true
  brew install --cask libreoffice || true
  echo "On macOS, use a Python build that includes Tk (python.org installer or pyenv with tk)."
}

if have apt-get; then
  install_apt
elif have dnf; then
  install_dnf
elif have brew; then
  install_brew
else
  echo "No supported package manager found (apt-get, dnf, or brew)."
  echo "Install manually: Python 3.10+, pip, Tk (python3-tk), Tesseract, LibreOffice."
  exit 1
fi

if ! have python3; then
  echo "python3 not found after install."
  exit 1
fi

# Virtualenv path: VENV env overrides; else project .venv if writable; else user cache
# (mirrors scripts/resolve_venv.sh for curl|bash users who only have this file).
signature_packet_venv_path() {
  local root="$1"
  if [ -n "${VENV:-}" ]; then
    printf '%s\n' "$VENV"
    return
  fi
  if [ -w "$root" ]; then
    printf '%s\n' "$root/.venv"
    return
  fi
  local home="${HOME:-/tmp}"
  local cache_root="${XDG_CACHE_HOME:-$home/.cache}"
  printf '%s\n' "$cache_root/signature-packet/venv"
}
VENV="$(signature_packet_venv_path "$ROOT")"
mkdir -p "$(dirname "$VENV")"
if [[ ! -w "$ROOT" ]]; then
  echo "Project directory is read-only; using virtualenv at: $VENV"
fi
python3 -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install -U pip
python -m pip install -e ".[gui]"

echo ""
echo "Done. Activate the venv and run:"
echo "  source $VENV/bin/activate"
echo "  signature-packet-gui    # or: signature-packet file1.pdf -o out.pdf"
