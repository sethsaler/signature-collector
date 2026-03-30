"""CLI: extract signature pages from DOCX/PDF and merge into one PDF."""

from __future__ import annotations

import argparse
import sys

from signature_packet.engine import PacketOptions, build_signature_packet


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
    p.add_argument(
        "--organizations",
        required=True,
        nargs="*",
        help="Organization names to filter by (one or more, space-separated). Only signature pages mentioning these organizations will be extracted.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    opts = PacketOptions(
        output=args.output,
        dpi=args.dpi,
        lang=args.lang,
        min_keywords=args.min_keywords,
        min_score=args.min_score,
        tesseract_cmd=args.tesseract_cmd,
        title_page=args.title_page,
        verbose=args.verbose,
        organization_names=list(args.organizations) if args.organizations else None,
    )
    code, _path = build_signature_packet(args.inputs, opts)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
