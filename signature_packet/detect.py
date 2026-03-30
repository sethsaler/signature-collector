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
    r"\bname\s*:\s*\w+",
    r"\btitle\s*:\s*\w+",
    r"\btitle\s*\(if applicable\)",
    r"\bby:\b",
    r"\bits\s+general\s+partner\b",
    r"\bits\s+managing\s+member\b",
    r"\bits\s+authorized\s+agent\b",
    r"\bauthorized signature\b",
    r"\bacceptance\b",
    r"\backnowledg",
    r"\bexecution\b",
    r"\bin witness whereof\b",
    r"\bdate:\b",
    r"\bdated\b",
    r"\bsignatory\b",
    r"\bgeneral partner\b",
    r"\blimited partner\b",
    r"\bmanager\b",
    r"\bmanaging member\b",
)

# Lines that look like labeled signature blanks (underscores or long rules).
BLANK_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Label followed by underscores/spaces (e.g., "Signature: ______" or "By: ______")
    re.compile(
        r"^(?:signature|signer|name|title|date|by)\s*:\s*[_\s\-]{6,}", re.I | re.M
    ),
    # Line with text followed by many underscores (e.g., "By: ________________________________")
    re.compile(r"^by\s*:\s*\w*[_\s\-]{10,}", re.I | re.M),
    # Pure underscores or em dashes
    re.compile(r"_{10,}"),
    re.compile(r"—{8,}"),
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


# Structured signature block patterns (multi-line combinations)
STRUCTURED_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Entity name + By line + signature line pattern
    re.compile(
        r"(?:^|\n)\s*\w[^\n]*(?:l\.p\.|l\.l\.c\.|inc\.|corp\.|ltd\.|company)"  # Entity name
        r".*?by\s*:.*?[_\-]{6,}",  # By line with underscores (signature line)
        re.I | re.S,
    ),
    # Multiple signature elements in proximity
    re.compile(
        r"by\s*:.*?name\s*:.*?title\s*:",
        re.I | re.S,
    ),
)


def _structured_block_score(text: str) -> int:
    """Detect structured signature blocks with multiple related elements."""
    score = 0
    for pat in STRUCTURED_BLOCK_PATTERNS:
        if pat.search(text):
            score += 3  # Strong indicator of signature block
    # Bonus for having both Name: and Title: on the same page
    if re.search(r"\bname\s*:\s*\w+", text, re.I) and re.search(
        r"\btitle\s*:\s*\w+", text, re.I
    ):
        score += 2
    # Bonus for multiple "By:" lines (often indicates entity + signature line)
    by_count = len(re.findall(r"\bby\s*:", text, re.I))
    if by_count >= 2:
        score += 2
    return min(score, 6)


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
    struct = _structured_block_score(text)
    # Weight keywords heavily; blanks support typical "Name: _______" layouts;
    # structured blocks provide bonus for complete signature sections
    score = kw_count * 1.5 + blank * 0.8 + struct * 1.0
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
    return (
        score_page_ocr_text(
            text,
            keyword_patterns=keyword_patterns,
            min_keyword_hits=min_keyword_hits,
            min_score=min_score,
        )
        > 0
    )


def find_signature_pages(
    page_texts: list[str],
    *,
    keyword_patterns: tuple[str, ...] = DEFAULT_KEYWORDS,
    min_keyword_hits: int = 2,
    min_score: float = 2.0,
    organization_names: list[str] | None = None,
) -> list[PageScore]:
    """Return signature page indices in document order with diagnostic scores.

    If organization_names is provided, only return pages that contain at least
    one of the organization names (case-insensitive fuzzy matching).
    """
    out: list[PageScore] = []
    for i, t in enumerate(page_texts):
        kw_count, hits = _count_keyword_hits(t, keyword_patterns)
        blank = _blank_line_score(t)
        struct = _structured_block_score(t)
        sc = kw_count * 1.5 + blank * 0.8 + struct * 1.0
        if kw_count < min_keyword_hits or sc < min_score:
            continue

        # Check organization filter if provided
        if organization_names:
            org_matches = _count_organization_matches(t, organization_names)
            if org_matches == 0:
                continue  # Skip pages that don't match any organization

        out.append(PageScore(page_index=i, score=sc, matched_keywords=tuple(hits)))
    return out


def _count_organization_matches(text: str, org_names: list[str]) -> int:
    """Count how many organization names appear in the text (case-insensitive fuzzy match).

    Returns the number of organization names found in the text.
    """
    text_lower = text.lower()
    matches = 0
    for org in org_names:
        org_clean = org.lower().strip()
        if org_clean and org_clean in text_lower:
            matches += 1
    return matches
