"""Merge selected PDF pages into one output PDF."""

from __future__ import annotations

import fitz


def merge_pages(
    source_pdf_path: str,
    page_indices: list[int],
    output_path: str,
    *,
    prepend_blank: bool = False,
) -> None:
    """
    Copy 0-based page_indices from source into a new PDF at output_path.
    If prepend_blank is True, insert a title page before extracted pages.
    """
    if not page_indices:
        raise ValueError("No pages to merge")

    src = fitz.open(source_pdf_path)
    try:
        out = fitz.open()
        try:
            if prepend_blank:
                # Single letter page with minimal metadata line (optional).
                blank = out.new_page(width=src[0].rect.width, height=src[0].rect.height)
                blank.insert_text(
                    (72, 72),
                    "Signature packet (extracted pages)",
                    fontsize=14,
                )
            for idx in page_indices:
                if idx < 0 or idx >= len(src):
                    raise IndexError(f"Page index {idx} out of range for {source_pdf_path}")
                out.insert_pdf(src, from_page=idx, to_page=idx)
            out.save(output_path)
        finally:
            out.close()
    finally:
        src.close()
