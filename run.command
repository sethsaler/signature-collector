#!/bin/bash
cd "$(dirname "$0")"
# shellcheck source=scripts/resolve_venv.sh
source "./scripts/resolve_venv.sh"
VENV_DIR="$(signature_packet_venv_path "$(pwd -P)")"

if [ ! -d "$VENV_DIR" ]; then
  echo "Setting up virtual environment..."
  mkdir -p "$(dirname "$VENV_DIR")"
  python3 -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install -U pip
  "$VENV_DIR/bin/pip" install ".[gui]"
fi

exec "$VENV_DIR/bin/python" -m signature_packet.gui
