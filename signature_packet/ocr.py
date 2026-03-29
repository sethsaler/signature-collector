"""Render PDF pages to images and run Tesseract OCR."""

from __future__ import annotations

import io
from collections.abc import Iterator

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def iter_page_texts_from_pdf(
    pdf_path: str,
    *,
    dpi: int = 200,
    lang: str = "eng",
    tesseract_config: str = "",
) -> Iterator[str]:
    """Yield OCR text for each page of a PDF (path or bytes-backed via fitz)."""
    doc = fitz.open(pdf_path)
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            mode = "RGB" if pix.n < 4 else "RGBA"
            img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
            if mode == "RGBA":
                img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            text = pytesseract.image_to_string(
                Image.open(buf),
                lang=lang,
                config=tesseract_config,
            )
            yield text or ""
    finally:
        doc.close()


def ocr_pdf_pages(pdf_path: str, **kwargs: object) -> list[str]:
    return list(iter_page_texts_from_pdf(pdf_path, **kwargs))  # type: ignore[arg-type]
