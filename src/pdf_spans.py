# -*- coding: utf-8 -*-
"""Ask the PDF which text is Latin.

A legacy Hindi PDF draws its Hindi in a legacy 8-bit font and its English in a
normal Latin font. The font name of each span is therefore ground truth about
what must not be run through the converter -- far better evidence than any
dictionary or statistical guess about the characters themselves.
"""

import re
from collections import Counter
from typing import Set

__all__ = ["latin_terms", "latin_spans", "font_report", "LEGACY_FONT_RE"]

# Families whose 8-bit code points carry Devanagari glyphs.
LEGACY_FONT_RE = re.compile(
    r"kruti|krutidev|dev\s*lys|devlys|chanakya|walkman|shree|shusha|shivaji|"
    r"agra|amar|ajay|priya|richa|kundli|yogesh|aparajita|apsdv|bhasha|"
    r"sanskrit\s*99|ml-|dvb-|akruti|susha",
    re.I,
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9.'\-]*[A-Za-z0-9]|[A-Za-z]")


def _family(font_name: str) -> str:
    name = re.sub(r"^[A-Z]{6}\+", "", font_name or "")
    name = re.split(r"[,\-]", name)[0]
    return re.sub(r"(Bold|Italic|Regular|Normal|Oblique|MT|PS)+$", "", name).strip().lower()


def latin_terms(pdf_path: str, min_len: int = 2) -> Set[str]:
    """Words drawn in a non-legacy font, collected across the document.

    Returns an empty set if the file cannot be read, so callers can fall back
    to the heuristic path (which is what OCR output needs anyway).
    """
    try:
        import pymupdf
    except ImportError:
        return set()

    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return set()

    per_family: Counter = Counter()
    spans = []
    try:
        for page in doc:
            try:
                data = page.get_text("dict")
            except Exception:
                continue
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text") or ""
                        if not text.strip():
                            continue
                        fam = _family(span.get("font", ""))
                        per_family[fam] += len(text)
                        spans.append((fam, text))
    finally:
        doc.close()

    if not spans:
        return set()

    dominant = per_family.most_common(1)[0][0]
    legacy = {f for f in per_family if LEGACY_FONT_RE.search(f)}
    # In a legacy document the body font is the legacy one even if its name is
    # not in the list above.
    if not legacy:
        legacy = {dominant}

    terms: Set[str] = set()
    for fam, text in spans:
        if fam in legacy:
            continue
        for tok in _TOKEN_RE.findall(text):
            tok = tok.strip(".'-")
            if len(tok) >= min_len:
                terms.add(tok)
    return terms


def latin_spans(pdf_path: str):
    """Latin-font runs in document order, as (text,) strings.

    Order matters. This document uses "(v)" for the Hindi letter अ and "(i)"
    for a Roman numeral; only the position in the page stream tells them
    apart, so a flat set of words is not enough.
    """
    try:
        import pymupdf
    except ImportError:
        return []

    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return []

    per_family: Counter = Counter()
    ordered = []
    try:
        for page in doc:
            try:
                data = page.get_text("dict")
            except Exception:
                continue
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text") or ""
                        if not text.strip():
                            continue
                        fam = _family(span.get("font", ""))
                        per_family[fam] += len(text)
                        ordered.append((fam, text))
    finally:
        doc.close()

    if not ordered:
        return []

    legacy = {f for f in per_family if LEGACY_FONT_RE.search(f)}
    if not legacy:
        legacy = {per_family.most_common(1)[0][0]}

    out = []
    for fam, text in ordered:
        if fam in legacy:
            continue
        stripped = text.strip()
        if stripped and re.search(r"[A-Za-z]", stripped):
            out.append(stripped)
    return out


def font_report(pdf_path: str) -> dict:
    """Summarise the fonts a PDF uses.

    Returns {"families": {name: chars}, "dominant": name,
             "legacy_chars": int, "latin_chars": int, "legacy": bool}.
    Whether the body font is a legacy 8-bit Devanagari font is the single most
    reliable signal for choosing a profile -- far better than counting
    character patterns in the extracted text.
    """
    try:
        import pymupdf
    except ImportError:
        return {}

    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return {}

    per_family: Counter = Counter()
    try:
        for page in doc:
            try:
                data = page.get_text("dict")
            except Exception:
                continue
            for block in data.get("blocks", []):
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = (span.get("text") or "").strip()
                        if text:
                            per_family[_family(span.get("font", ""))] += len(text)
    finally:
        doc.close()

    if not per_family:
        return {}

    legacy_chars = sum(n for f, n in per_family.items() if LEGACY_FONT_RE.search(f))
    total = sum(per_family.values())
    dominant = per_family.most_common(1)[0][0]
    return {
        "families": dict(per_family),
        "dominant": dominant,
        "legacy_chars": legacy_chars,
        "latin_chars": total - legacy_chars,
        "legacy": bool(LEGACY_FONT_RE.search(dominant)) or legacy_chars > total * 0.2,
    }
