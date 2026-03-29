"""Tests for signature-page heuristics (no OCR)."""

from signature_packet.detect import find_signature_pages, is_signature_page


def test_empty_not_signature():
    assert not is_signature_page("")


def test_typical_signature_block():
    text = """
    IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first above written.

    Acme Corp.

    By: _________________________
    Name: _______________________
    Title: ______________________
    Date: _______________________
    """
    assert is_signature_page(text)


def test_boilerplate_only_low_score():
    text = "This agreement is governed by the laws of Delaware. Confidentiality obligations survive."
    assert not is_signature_page(text)


def test_find_pages_order():
    pages = [
        "Section 1. Definitions.",
        "Signature: _____________  Witness: _____________  Date: ______",
        "Exhibit A",
    ]
    hits = find_signature_pages(pages)
    assert [h.page_index for h in hits] == [1]
