#!/usr/bin/env bash
# Install system packages (Tesseract, LibreOffice, Tk) and Python deps for signature-packet.
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/sethsaler/signature-collector/main/scripts/install_deps.sh | bash
# Or from a clone:
#   bash scripts/install_deps.sh

set -euo pipefail

# Configuration
DESKTOP_DIR="${HOME}/Desktop"
LAUNCHER_NAME="Signature Packet.command"
REPO_NAME="signature-collector"

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
echo "═══════════════════════════════════════════════════════════"
echo "  Installing System Dependencies"
echo "═══════════════════════════════════════════════════════════"
echo ""

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

# Setup desktop directory
echo ""
echo "Setting up Desktop directory..."
mkdir -p "$DESKTOP_DIR"

# Determine ROOT and INSTALL_METHOD based on execution context
if [[ "$IS_PIPED" == "true" ]]; then
  # Script is being piped - clone to Desktop
  CLONE_DIR="${DESKTOP_DIR}/${REPO_NAME}"
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "  Installing to Desktop"
  echo "═══════════════════════════════════════════════════════════"
  echo ""
  echo "Cloning repository to $CLONE_DIR..."
  
  # Remove existing clone if present
  if [[ -d "$CLONE_DIR" ]]; then
    rm -rf "$CLONE_DIR"
  fi
  
  git clone --depth 1 https://github.com/sethsaler/signature-collector.git "$CLONE_DIR"
  ROOT="$CLONE_DIR"
  INSTALL_METHOD="editable"
  echo "✓ Repository cloned successfully."
else
  # Script is run from a clone
  CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  
  # Check if already on Desktop
  if [[ "$CURRENT_DIR" == "$DESKTOP_DIR/$REPO_NAME" ]]; then
    echo "✓ Already running from Desktop location"
    ROOT="$CURRENT_DIR"
    INSTALL_METHOD="editable"
  else
    # Move/symlink to Desktop
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Moving Repository to Desktop"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    
    TARGET_DIR="${DESKTOP_DIR}/${REPO_NAME}"
    
    # Remove existing if present
    if [[ -d "$TARGET_DIR" ]]; then
      echo "Removing existing directory at $TARGET_DIR..."
      rm -rf "$TARGET_DIR"
    fi
    
    # Copy to Desktop
    echo "Copying repository to Desktop..."
    cp -R "$CURRENT_DIR" "$TARGET_DIR"
    ROOT="$TARGET_DIR"
    INSTALL_METHOD="editable"
    echo "✓ Repository copied to Desktop"
  fi
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

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Creating Python Virtual Environment"
echo "═══════════════════════════════════════════════════════════"
echo ""

python3 -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install -U pip

# Install signature-packet based on method
echo ""
echo "Installing signature-packet..."
cd "$ROOT"
python -m pip install -e ".[gui]"

echo ""
echo "✓ Installed successfully from: $ROOT"

# Create launcher .command file on Desktop
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Creating Desktop Launcher"
echo "═══════════════════════════════════════════════════════════"
echo ""

LAUNCHER_PATH="${DESKTOP_DIR}/${LAUNCHER_NAME}"

# Create the .command launcher file
cat > "$LAUNCHER_PATH" << LAUNCHER_EOF
#!/bin/bash
# Signature Packet GUI Launcher
# Double-click this file to launch the Signature Packet GUI

set -euo pipefail

# Change to the repo directory
REPO_DIR="\${HOME}/Desktop/${REPO_NAME}"
cd "\$REPO_DIR"

# Find the virtual environment
VENV_DIR="\${REPO_DIR}/.venv"

if [ ! -d "\$VENV_DIR" ]; then
  osascript -e 'display dialog "Signature Packet is not installed. Please reinstall." buttons {"OK"} default button 1 with icon stop'
  exit 1
fi

# Activate venv and run GUI
exec "\$VENV_DIR/bin/python" -m signature_packet.gui
LAUNCHER_EOF

chmod +x "$LAUNCHER_PATH"

echo "✅ Desktop launcher created: $LAUNCHER_PATH"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Installation Complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📁 Repository location: $ROOT"
echo "🚀 Desktop launcher: $LAUNCHER_PATH"
echo ""
echo "To use Signature Packet:"
echo "  1. Double-click the 'Signature Packet' icon on your Desktop"
echo "  2. Or run from terminal:"
echo "     cd $ROOT"
echo "     source .venv/bin/activate"
echo "     signature-packet-gui"
echo ""
echo "To update: cd $ROOT && git pull && pip install -e '.[gui]'"
echo ""
