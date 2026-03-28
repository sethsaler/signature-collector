# signature-packet

Python CLI that rasterizes PDF pages, runs **Tesseract OCR**, scores each page with keyword/heuristic rules, keeps pages that look like **signature / execution / notary** blocks, and writes a single merged **signature packet** PDF.

## Requirements

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) on `PATH` (or pass `--tesseract-cmd`)
- For **`.docx`**: [LibreOffice](https://www.libreoffice.org/) (`soffice` or `libreoffice` on `PATH`) for headless conversion to PDF

## Install

```bash
pip install -e .
```

## Usage

```bash
signature-packet contract1.pdf agreement.docx -o combined_signatures.pdf -v
```

Options include `--dpi`, `--lang` (Tesseract languages), `--min-keywords`, `--min-score`, and `--title-page`.

Detection is heuristic: tune `--min-keywords` / `--min-score` if you get false positives or misses.

## Tests

```bash
pip install -e ".[dev]"
pytest
```
