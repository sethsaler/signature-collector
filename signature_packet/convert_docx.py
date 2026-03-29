"""Convert DOCX to PDF using LibreOffice (soffice) when available."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path


def find_soffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def docx_to_pdf(docx_path: str, output_dir: str | None = None) -> str:
    """
    Convert docx_path to PDF via headless LibreOffice.
    Returns path to the created PDF (same basename as docx).
    """
    src = Path(docx_path).resolve()
    if not src.is_file():
        raise FileNotFoundError(docx_path)
    if src.suffix.lower() not in {".docx", ".doc"}:
        raise ValueError(f"Expected .docx or .doc, got {src.suffix}")

    soffice = find_soffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice (soffice or libreoffice) is not installed or not on PATH. "
            "Install it to convert DOCX files, or convert DOCX to PDF manually."
        )

    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="sigpkt_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        soffice,
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(src),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if proc.returncode != 0:
        raise RuntimeError(
            f"LibreOffice conversion failed (exit {proc.returncode}): "
            f"{proc.stderr or proc.stdout}"
        )

    pdf_path = out_dir / f"{src.stem}.pdf"
    if not pdf_path.is_file():
        raise RuntimeError(f"Expected PDF not found after conversion: {pdf_path}")

    return str(pdf_path)
