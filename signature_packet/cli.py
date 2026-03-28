"""CLI: extract signature pages from DOCX/PDF and merge into one PDF."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from signature_packet.convert_docx import docx_to_pdf
from signature_packet.detect import find_signature_pages
from signature_packet.merge import merge_pages
from signature_packet.ocr import ocr_pdf_pages


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Use Tesseract OCR to find likely signature pages in PDF or DOCX files, "
            "then merge those pages into a single signature packet PDF."
        )
    )
    p.add_argument(
        "inputs",
        nargs="+",
        help="One or more .pdf or .docx paths",
    )
    p.add_argument(
        "-o",
        "--output",
        default="signature_packet.pdf",
        help="Output merged PDF path (default: signature_packet.pdf)",
    )
    p.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Rasterization DPI for OCR (default: 200)",
    )
    p.add_argument(
        "--lang",
        default="eng",
        help="Tesseract language code(s), e.g. eng or eng+deu (default: eng)",
    )
    p.add_argument(
        "--min-keywords",
        type=int,
        default=2,
        help="Minimum distinct keyword matches required per page (default: 2)",
    )
    p.add_argument(
        "--min-score",
        type=float,
        default=2.0,
        help="Minimum heuristic score to treat a page as a signature page (default: 2)",
    )
    p.add_argument(
        "--tesseract-cmd",
        default=None,
        help="Path to tesseract executable if not on PATH",
    )
    p.add_argument(
        "--title-page",
        action="store_true",
        help="Prepend a simple title page to the output PDF",
    )
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print per-file detected page indices",
    )
    return p.parse_args(argv)


def _ensure_pdf(path: str, temp_dirs: list[str]) -> str:
    suf = Path(path).suffix.lower()
    if suf == ".pdf":
        return path
    if suf in {".docx", ".doc"}:
        td = tempfile.mkdtemp(prefix="sigpkt_docx_")
        temp_dirs.append(td)
        return docx_to_pdf(path, output_dir=td)
    raise ValueError(f"Unsupported file type: {path}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.tesseract_cmd:
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = args.tesseract_cmd

    temp_dirs: list[str] = []
    segments: list[tuple[str, list[int]]] = []

    try:
        for raw in args.inputs:
            pdf_path = _ensure_pdf(raw, temp_dirs)
            texts = ocr_pdf_pages(
                pdf_path,
                dpi=args.dpi,
                lang=args.lang,
            )
            hits = find_signature_pages(
                texts,
                min_keyword_hits=args.min_keywords,
                min_score=args.min_score,
            )
            indices = [h.page_index for h in hits]
            if args.verbose:
                print(f"{raw} -> pages {[i + 1 for i in indices]} (1-based)", file=sys.stderr)
            if not indices:
                print(f"Warning: no signature pages detected in {raw}", file=sys.stderr)
                continue
            segments.append((pdf_path, indices))

        if not segments:
            print("Error: no signature pages found in any input.", file=sys.stderr)
            return 2

        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if len(segments) == 1:
            merge_pages(
                segments[0][0],
                segments[0][1],
                str(out_path),
                prepend_blank=args.title_page,
            )
        else:
            import fitz

            merged = fitz.open()
            try:
                if args.title_page:
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

        print(f"Wrote {out_path}")
        return 0
    finally:
        for d in temp_dirs:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
