"""Core pipeline: OCR pages, detect signature pages, merge to one PDF."""

from __future__ import annotations

import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import fitz

from signature_packet.convert_docx import docx_to_pdf
from signature_packet.detect import find_signature_pages
from signature_packet.merge import merge_pages
from signature_packet.ocr import ocr_pdf_pages


@dataclass
class PacketOptions:
    output: str = "signature_packet.pdf"
    dpi: int = 200
    lang: str = "eng"
    min_keywords: int = 2
    min_score: float = 2.0
    tesseract_cmd: str | None = None
    title_page: bool = False
    verbose: bool = False


def _ensure_pdf(path: str, temp_dirs: list[str]) -> str:
    suf = Path(path).suffix.lower()
    if suf == ".pdf":
        return path
    if suf in {".docx", ".doc"}:
        td = tempfile.mkdtemp(prefix="sigpkt_docx_")
        temp_dirs.append(td)
        return docx_to_pdf(path, output_dir=td)
    raise ValueError(f"Unsupported file type: {path}")


def build_signature_packet(
    inputs: list[str],
    options: PacketOptions,
    *,
    log: Callable[[str], None] | None = None,
    warn: Callable[[str], None] | None = None,
) -> tuple[int, str | None]:
    """
    Run the full pipeline. Returns (exit_code, output_path).
    exit_code 0 = success, 2 = no pages / error.
    """
    if options.tesseract_cmd:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = options.tesseract_cmd

    def _warn(msg: str) -> None:
        if warn:
            warn(msg)
        else:
            print(msg, file=sys.stderr)

    temp_dirs: list[str] = []
    segments: list[tuple[str, list[int]]] = []

    try:
        for raw in inputs:
            pdf_path = _ensure_pdf(raw, temp_dirs)
            texts = ocr_pdf_pages(
                pdf_path,
                dpi=options.dpi,
                lang=options.lang,
            )
            hits = find_signature_pages(
                texts,
                min_keyword_hits=options.min_keywords,
                min_score=options.min_score,
            )
            indices = [h.page_index for h in hits]
            if options.verbose:
                _warn(f"{raw} -> pages {[i + 1 for i in indices]} (1-based)")
            if not indices:
                _warn(f"Warning: no signature pages detected in {raw}")
                continue
            segments.append((pdf_path, indices))

        if not segments:
            _warn("Error: no signature pages found in any input.")
            return 2, None

        out_path = Path(options.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if len(segments) == 1:
            merge_pages(
                segments[0][0],
                segments[0][1],
                str(out_path),
                prepend_blank=options.title_page,
            )
        else:
            merged = fitz.open()
            try:
                if options.title_page:
                    doc0 = fitz.open(segments[0][0])
                    try:
                        w, h = doc0[0].rect.width, doc0[0].rect.height
                    finally:
                        doc0.close()
                    title = merged.new_page(width=w, height=h)
                    title.insert_text(
                        (72, 72),
                        "Signature packet (extracted pages)",
                        fontsize=14,
                    )

                for pdf_path, indices in segments:
                    src = fitz.open(pdf_path)
                    try:
                        for idx in indices:
                            merged.insert_pdf(src, from_page=idx, to_page=idx)
                    finally:
                        src.close()
                merged.save(str(out_path))
            finally:
                merged.close()

        done = f"Wrote {out_path}"
        if log:
            log(done)
        else:
            print(done)
        return 0, str(out_path)
    finally:
        for d in temp_dirs:
            shutil.rmtree(d, ignore_errors=True)
