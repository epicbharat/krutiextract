# -*- coding: utf-8 -*-
"""One PDF in, one Markdown string out."""

import os
import re
import tempfile
from typing import List, Optional, Sequence, Tuple

from .converter import (
    PASSTHROUGH,
    auto_detect_font,
    convert_legacy_text,
    normalise_legacy_encoding,
)
from .extractor import extract_raw_markdown
from .markdown_utils import protect_non_hindi_syntax, restore_non_hindi_syntax
from .pdf_spans import SUPPORTED_FONT_RE, font_report, latin_spans

__all__ = [
    "convert_pdf",
    "clean_lines",
    "normalize_extracted_markdown",
    "strip_extractor_scaffolding",
    "repair_legacy_fragments",
]

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


def strip_extractor_scaffolding(text: str) -> str:
    """Remove markup that is never document content. Safe for any language."""
    return _HTML_COMMENT.sub("", text)


def repair_legacy_fragments(text: str) -> str:
    """Rejoin words the extractor split with inline markup.

    Only safe on legacy-encoded text. These rules delete emphasis markers and
    the space beside them, which is right when the extractor has split
    "C;wVhI+kqQy" across a <sup>, and wrong in a document that simply
    contains the bolded English word "a".
    """
    text = text.replace(_TAG_SENTINEL, "")
    text = _SPLIT_SUP.sub(lambda m: m.group(1) + m.group(5) + m.group(8), text)
    text = _INLINE_TAG.sub(_TAG_SENTINEL, text)
    text = _TAG_DEBRIS.sub("", text)
    text = text.replace(_TAG_SENTINEL, "")
    return _BOLD_SIGN.sub(r"\1", text)


def normalize_extracted_markdown(text: str, legacy: bool = True) -> str:
    """Scaffolding removal, plus legacy fragment repair when *legacy*."""
    if legacy:
        text = repair_legacy_fragments(text)
    return strip_extractor_scaffolding(text)


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


def _page_count(pdf_path: str) -> int:
    try:
        import pymupdf
        with pymupdf.open(pdf_path) as doc:
            return doc.page_count
    except Exception:
        return 0


def _warn_if_empty(text: str, warnings: List[str], pdf_path: str = "",
                   pages: Optional[Sequence[int]] = None) -> None:
    """Flag a result that is empty, or so thin the PDF is likely a scan."""
    if not text.strip():
        warnings.append(
            "no text recovered: the PDF is probably image-only. Check that "
            "Tesseract and its language pack are installed, or raise --ocr-dpi."
        )
        return

    count = len(pages) if pages else _page_count(pdf_path)
    if count >= 3 and len(text) / count < 400:
        warnings.append(
            f"only {len(text)} characters recovered from {count} pages. The "
            "PDF is probably scanned and OCR found little; check the Tesseract "
            "language pack and try a higher --ocr-dpi."
        )


def convert_pdf(
    pdf_path: str,
    font: str = "auto",
    enhance_ocr: bool = False,
    ocr: bool = True,
    ocr_language: str = "hin+eng",
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

    # Scaffolding removal is safe for any document. The legacy repairs are
    # not, so they wait until the profile is known.
    raw = strip_extractor_scaffolding(raw)
    # Re-read a MacRoman-reported legacy stream before anything else looks at
    # it, so detection, protection and conversion all see the same bytes.
    raw = normalise_legacy_encoding(raw)

    # The body font settles the profile far more reliably than character
    # statistics: a PDF whose text is drawn in a normal Latin font has nothing
    # to convert, whatever its characters look like.
    if font == "auto":
        try:
            report = font_report(pdf_path)
        except Exception:
            report = {}
        dominant = (report or {}).get("dominant", "")
        if report.get("legacy") and dominant and not SUPPORTED_FONT_RE.search(dominant):
            warnings.append(
                f"the body font '{dominant}' is a legacy Devanagari encoding "
                "this build has no mapping for; the converted text will be "
                "wrong. Supported: KrutiDev, DevLys, Walkman-Chanakya, "
                "Chanakya. See docs/GUIDE.md section 9."
            )

    # The font name warns, it does not decide. A legacy font under a custom
    # name ("rajpurohit") is common, and forcing such a document to English
    # left all of it unconverted.
    profile = auto_detect_font(raw) if font == "auto" else font

    if profile in PASSTHROUGH:
        # Nothing to convert, so nothing is protected either.
        out = clean_lines(raw, drop_patterns)
        _warn_if_empty(out, warnings, pdf_path, pages)
        return out, profile, warnings

    raw = repair_legacy_fragments(raw)

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
    out = clean_lines(restored, drop_patterns)
    _warn_if_empty(out, warnings, pdf_path, pages)
    return out, profile, warnings
