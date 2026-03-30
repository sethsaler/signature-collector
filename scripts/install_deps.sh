#!/usr/bin/env bash
# Install system packages (Tesseract, LibreOffice, Tk) and Python deps for signature-packet.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sethsaler/signature-collector/main/scripts/install_deps.sh | bash
# Or from a clone:
#   bash scripts/install_deps.sh

set -euo pipefail

# Detect if script is being piped directly
IS_PIPED=false
if [[ -z "${BASH_SOURCE[0]:-}" ]] || [[ "${BASH_SOURCE[0]}" == "-" ]] || [[ ! -f "${BASH_SOURCE[0]}" ]]; then
  IS_PIPED=true
fi

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

# Install system dependencies
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

# Determine ROOT and INSTALL_METHOD based on execution context
if [[ "$IS_PIPED" == "true" ]]; then
  # Script is being piped - need to get the code somehow
  INSTALL_METHOD=""
  
  if have git; then
    # Option 1: Clone the repository
    CLONE_DIR="${HOME}/.signature-packet/signature-collector"
    echo "Detected piped execution with git available."
    echo "Cloning repository to $CLONE_DIR..."
    
    # Remove existing clone if present
    if [[ -d "$CLONE_DIR" ]]; then
      rm -rf "$CLONE_DIR"
    fi
    
    git clone --depth 1 https://github.com/sethsaler/signature-collector.git "$CLONE_DIR"
    ROOT="$CLONE_DIR"
    INSTALL_METHOD="editable"
    echo "Repository cloned successfully."
  else
    # Option 2: Direct pip install from GitHub
    echo "Detected piped execution without git."
    echo "Will install directly from GitHub (non-editable)."
    INSTALL_METHOD="direct"
    ROOT=""  # Not needed for direct install
  fi
else
  # Script is run from a clone - use current directory
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  INSTALL_METHOD="editable"
fi

# Virtualenv path determination
signature_packet_venv_path() {
  local root="${1:-}"
  if [ -n "${VENV:-}" ]; then
    printf '%s\n' "$VENV"
    return
  fi
  if [[ -n "$root" ]] && [[ -w "$root" ]]; then
    printf '%s\n' "$root/.venv"
    return
  fi
  local home="${HOME:-/tmp}"
  local cache_root="${XDG_CACHE_HOME:-$home/.cache}"
  printf '%s\n' "$cache_root/signature-packet/venv"
}

VENV="$(signature_packet_venv_path "$ROOT")"
mkdir -p "$(dirname "$VENV")"

if [[ -n "$ROOT" ]] && [[ ! -w "$ROOT" ]]; then
  echo "Project directory is read-only; using virtualenv at: $VENV"
fi

python3 -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install -U pip

# Install signature-packet based on method
if [[ "$INSTALL_METHOD" == "editable" ]]; then
  cd "$ROOT"
  python -m pip install -e ".[gui]"
  echo ""
  echo "✓ Installed in editable mode from: $ROOT"
  echo ""
  echo "Done. Activate the venv and run:"
  echo "  source $VENV/bin/activate"
  echo "  signature-packet-gui    # or: signature-packet file1.pdf -o out.pdf"
  echo ""
  echo "To update: cd $ROOT && git pull"
  
  if [[ "$IS_PIPED" == "true" ]]; then
    echo ""
    echo "Repository cloned to: $ROOT"
  fi
else
  # Direct install from GitHub
  python -m pip install "git+https://github.com/sethsaler/signature-collector.git#egg=signature-packet[gui]"
  echo ""
  echo "✓ Installed directly from GitHub (non-editable)"
  echo ""
  echo "Done. Activate the venv and run:"
  echo "  source $VENV/bin/activate"
  echo "  signature-packet-gui    # or: signature-packet file1.pdf -o out.pdf"
  echo ""
  echo "Note: To modify the code, clone the repository:"
  echo "  git clone https://github.com/sethsaler/signature-collector.git"
  echo "  cd signature-collector"
  echo "  bash scripts/install_deps.sh"
fi
