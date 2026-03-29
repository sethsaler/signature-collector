"""Heuristics for signature-page detection from OCR text."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Phrases and terms commonly found on signature / execution pages.
DEFAULT_KEYWORDS: tuple[str, ...] = (
    r"\bsignature\b",
    r"\bsign here\b",
    r"\bsigned\b",
    r"\bnotary\b",
    r"\bnotarization\b",
    r"\bwitness\b",
    r"\bprint name\b",
    r"\btitle\s*\(if applicable\)",
    r"\bby:\s*$",
    r"\bauthorized signature\b",
    r"\bacceptance\b",
    r"\backnowledg",
    r"\bexecution\b",
    r"\bin witness whereof\b",
    r"\bdate:\b",
    r"\bdated\b",
    r"\bsignatory\b",
)

# Lines that look like labeled signature blanks (underscores or long rules).
BLANK_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^(?:signature|signer|name|title|date)\s*:\s*[_\s\-]{8,}", re.I | re.M),
    re.compile(r"_{10,}"),
    re.compile(r"—{8,}"),  # em dash rules
)


@dataclass(frozen=True)
class PageScore:
    page_index: int
    score: float
    matched_keywords: tuple[str, ...]


def _count_keyword_hits(text: str, patterns: tuple[str, ...]) -> tuple[int, list[str]]:
    lowered = text.lower()
    hits: list[str] = []
    for p in patterns:
        if re.search(p, lowered, re.I):
            hits.append(p)
    return len(hits), hits


def _blank_line_score(text: str) -> int:
    n = 0
    for pat in BLANK_LINE_PATTERNS:
        n += len(pat.findall(text))
    return min(n, 5)


def score_page_ocr_text(
    text: str,
    *,
    keyword_patterns: tuple[str, ...] = DEFAULT_KEYWORDS,
    min_keyword_hits: int = 2,
    min_score: float = 2.0,
) -> float:
    """
    Return a non-negative score; pages with score >= min_score and at least
    min_keyword_hits distinct keyword matches are treated as signature pages.
    """
    kw_count, _ = _count_keyword_hits(text, keyword_patterns)
    blank = _blank_line_score(text)
    # Weight keywords heavily; blanks support typical "Name: _______" layouts.
    score = kw_count * 1.5 + blank * 0.8
    if kw_count < min_keyword_hits:
        return 0.0
    return score if score >= min_score else 0.0


def is_signature_page(
    text: str,
    *,
    keyword_patterns: tuple[str, ...] = DEFAULT_KEYWORDS,
    min_keyword_hits: int = 2,
    min_score: float = 2.0,
) -> bool:
    return score_page_ocr_text(
        text,
        keyword_patterns=keyword_patterns,
        min_keyword_hits=min_keyword_hits,
        min_score=min_score,
    ) > 0


def find_signature_pages(
    page_texts: list[str],
    *,
    keyword_patterns: tuple[str, ...] = DEFAULT_KEYWORDS,
    min_keyword_hits: int = 2,
    min_score: float = 2.0,
) -> list[PageScore]:
    """Return signature page indices in document order with diagnostic scores."""
    out: list[PageScore] = []
    for i, t in enumerate(page_texts):
        kw_count, hits = _count_keyword_hits(t, keyword_patterns)
        blank = _blank_line_score(t)
        sc = kw_count * 1.5 + blank * 0.8
        if kw_count < min_keyword_hits or sc < min_score:
            continue
        out.append(PageScore(page_index=i, score=sc, matched_keywords=tuple(hits)))
    return out
