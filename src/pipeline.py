# -*- coding: utf-8 -*-
"""One PDF in, one Markdown string out."""

import os
import re
import tempfile
from typing import List, Optional, Sequence, Tuple

from .converter import PASSTHROUGH, auto_detect_font, convert_legacy_text
from .extractor import ExtractionError, extract_raw_markdown
from .markdown_utils import protect_non_hindi_syntax, restore_non_hindi_syntax
from .pdf_spans import font_report, latin_spans

__all__ = ["convert_pdf", "clean_lines", "normalize_extracted_markdown"]

# Boilerplate that appears on every page of a reprinted textbook.
_DEFAULT_DROP = (r"^\s*Reprint\s+\d{4}(?:\s*[-–.]\s*\d{2,4})?\s*$",)


_EMPH = r"(?:\*\*|__|[*_])+"

# pymupdf4llm wraps a font-size blip in <sup>/<sub>, which can land in the
# middle of a word and split it. Putting the pieces back before conversion
# matters: "C;wVhI" + "+" + "kqQy" is one word, ब्यूटीफुल.
_SPLIT_SUP = re.compile(
    rf"([A-Za-z])({_EMPH})?<(sub|sup)>({_EMPH})?([^<>\s]{{1,3}}?)({_EMPH})?</\3>"
    rf"\s*({_EMPH})?([A-Za-z])"
)

# <mark>, <sub> and <sup> also fragment a word and make the extractor close
# and reopen emphasis around the break, which leaves stray delimiters and a
# spurious space in the middle of a word. A sentinel lets us delete only the
# delimiters and spaces that exist because of the tag, and leave real ones.
_TAG_SENTINEL = "\ue000"
_INLINE_TAG = re.compile(r"</?(?:mark|sub|sup)>")
_TAG_DEBRIS = re.compile(
    rf"(?<=\S)((?:[*_]+[ \t]?)*){_TAG_SENTINEL}[ \t]?((?:[ \t]?[*_]+)*)(?=\S)")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)

# The extractor sometimes emphasises a single combining key in the middle of a
# word, e.g. "o.kZu djs **a** A" for वर्णन करें।. Only these keys qualify: they
# are matras and signs, never words, so bold around one is always an artefact.
_LEGACY_SIGNS = "a\u00a1%WsSqwhk`Zf\u201a+z~"
_BOLD_SIGN = re.compile(
    rf"(?<=[A-Za-z])[ \t]?\*\*([{re.escape(_LEGACY_SIGNS)}])\*\*[ \t]?(?=[A-Za-z\u00a1])")


def normalize_extracted_markdown(text: str) -> str:
    """Repair artefacts of the Markdown extractor before conversion."""
    text = text.replace(_TAG_SENTINEL, "")
    text = _SPLIT_SUP.sub(lambda m: m.group(1) + m.group(5) + m.group(8), text)
    text = _INLINE_TAG.sub(_TAG_SENTINEL, text)
    text = _TAG_DEBRIS.sub("", text)
    text = text.replace(_TAG_SENTINEL, "")
    text = _BOLD_SIGN.sub(r"\1", text)
    text = _HTML_COMMENT.sub("", text)
    return text


def clean_lines(text: str, drop_patterns: Sequence[str] = ()) -> str:
    """Remove running headers and footers.

    The original hard-coded three NCERT book titles, which silently deleted
    those words from any other document. Patterns are now explicit.
    """
    compiled = [re.compile(p) for p in tuple(_DEFAULT_DROP) + tuple(drop_patterns)]
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped and any(rx.search(stripped) for rx in compiled):
            continue
        out.append(line)
    return "\n".join(out)


def convert_pdf(
    pdf_path: str,
    font: str = "auto",
    enhance_ocr: bool = False,
    ocr: bool = True,
    ocr_language: str = "hin",
    ocr_dpi: int = 400,
    enhance_options: Optional[dict] = None,
    drop_patterns: Sequence[str] = (),
    pages: Optional[Sequence[int]] = None,
) -> Tuple[str, str, List[str]]:
    """Return (markdown, profile_used, warnings)."""
    warnings: List[str] = []
    target = pdf_path
    temp_pdf = None

    if enhance_ocr:
        from .image_cleaner import OpenCVMissing, enhance_pdf_images
        fd, temp_pdf = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            enhance_pdf_images(pdf_path, temp_pdf, **(enhance_options or {}))
            target = temp_pdf
        except (OpenCVMissing, Exception) as exc:
            warnings.append(f"image enhancement skipped: {exc}")
            target = pdf_path

    try:
        raw = extract_raw_markdown(
            target, ocr=ocr, ocr_language=ocr_language, ocr_dpi=ocr_dpi,
            pages=pages, warnings=warnings,
        )
    finally:
        if temp_pdf and os.path.exists(temp_pdf):
            os.remove(temp_pdf)

    raw = normalize_extracted_markdown(raw)

    # The body font settles the profile far more reliably than character
    # statistics: a PDF whose text is drawn in a normal Latin font has nothing
    # to convert, whatever its characters look like.
    if font == "auto":
        try:
            report = font_report(pdf_path)
        except Exception:
            report = {}
        if report and not report.get("legacy", True):
            font = auto_detect_font(raw)
            if font not in PASSTHROUGH:
                font = "english"

    profile = auto_detect_font(raw) if font == "auto" else font

    if profile in PASSTHROUGH:
        # Nothing to convert, so nothing is protected either.
        return clean_lines(raw, drop_patterns), profile, warnings

    # Ask the source PDF which words it drew in a Latin font before guessing.
    try:
        spans = latin_spans(pdf_path)
    except Exception:
        spans = []

    protected, preserved = protect_non_hindi_syntax(raw, latin_spans=spans)
    if font == "auto":
        profile = auto_detect_font(protected)
    converted = convert_legacy_text(protected, profile)
    restored = restore_non_hindi_syntax(converted, preserved)
    return clean_lines(restored, drop_patterns), profile, warnings
