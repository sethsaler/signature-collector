# signature-packet

Python CLI that rasterizes PDF pages, runs **Tesseract OCR**, scores each page with keyword/heuristic rules, keeps pages that look like **signature / execution / notary** blocks, and writes a single merged **signature packet** PDF.

## Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on `PATH` (or pass `--tesseract-cmd`)
- For **`.docx`**: [LibreOffice](https://www.libreoffice.org/) (`soffice` or `libreoffice` on `PATH`) for headless conversion to PDF

## Quick Install (macOS/Linux)

**One command** installs everything and creates a Desktop launcher:

```bash
curl -fsSL https://raw.githubusercontent.com/sethsaler/signature-collector/main/scripts/install_deps.sh | bash
```

This will:
- Install system packages (Tesseract, LibreOffice, Python, Tk)
- Clone the repo to your **Desktop**
- Create a **Desktop launcher** (double-click to open GUI)
- Set up a Python virtual environment

After installation, simply **double-click the "Signature Packet" icon** on your Desktop!

## Usage (GUI)

**Option 1: Double-click the Desktop icon** (easiest)

**Option 2: From terminal:**
```bash
cd ~/Desktop/signature-collector
source .venv/bin/activate
signature-packet-gui
```

Minimal window: **Browse…** for multi-select, **drag-and-drop** onto the list when `tkinterdnd2` is installed (included in `pip install -e ".[gui]"`), optional title page, then **Build packet**.

## Usage (CLI)

```bash
cd ~/Desktop/signature-collector
source .venv/bin/activate
signature-packet contract1.pdf agreement.docx -o combined_signatures.pdf -v
```

CLI options include `--dpi`, `--lang` (Tesseract languages), `--min-keywords`, `--min-score`, and `--title-page`.

Detection is heuristic: tune `--min-keywords` / `--min-score` if you get false positives or misses.

## Manual Install (Advanced)

If you prefer not to use the automated installer:

```bash
git clone https://github.com/sethsaler/signature-collector.git
cd signature-collector
pip install -e ".[gui]"
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Use your fork/branch URL if you are not on `main`. From a local clone you can run `bash scripts/install_deps.sh` instead.

Manual install:

```bash
pip install -e ".[gui]"
```

## Usage (CLI)

```bash
signature-packet contract1.pdf agreement.docx -o combined_signatures.pdf -v
```

## Usage (GUI)

```bash
signature-packet-gui
```

Minimal window: **Browse…** for multi-select, **drag-and-drop** onto the list when `tkinterdnd2` is installed (included in `pip install -e ".[gui]"`), optional title page, then **Build packet**.

CLI options include `--dpi`, `--lang` (Tesseract languages), `--min-keywords`, `--min-score`, and `--title-page`.

Detection is heuristic: tune `--min-keywords` / `--min-score` if you get false positives or misses.

## Tests

```bash
pip install -e ".[dev]"
pytest
```
