#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Setting up virtual environment..."
  python3 -m venv .venv
  .venv/bin/pip install -U pip
  .venv/bin/pip install ".[gui]"
fi

exec .venv/bin/python -m signature_packet.gui
