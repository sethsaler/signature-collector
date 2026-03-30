#!/bin/bash
# Signature Packet GUI Launcher
# Double-click this file to launch the Signature Packet GUI without opening a terminal

set -euo pipefail

# Find the virtual environment
VENV_DIR="${HOME}/.signature-packet/signature-collector/.venv"

if [ ! -d "$VENV_DIR" ]; then
  osascript -e 'display dialog "Signature Packet is not installed. Please run the installer first:

curl -fsSL https://raw.githubusercontent.com/sethsaler/signature-collector/main/scripts/install_deps.sh -o install_deps.sh && bash install_deps.sh" buttons {"OK"} default button 1 with icon stop'
  exit 1
fi

# Activate venv and run GUI
exec "$VENV_DIR/bin/python" -m signature_packet.gui
