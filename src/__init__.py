# -*- coding: utf-8 -*-
"""KrutiExtract - legacy Hindi PDF to Markdown."""

__version__ = "1.3.0"

from .aps_converter import aps_to_unicode
from .chanakya_converter import chanakya_to_unicode
from .converter import (
    auto_detect_font,
    convert_legacy_text,
    krutidev_to_unicode,
    walkman_to_unicode,
)
from .extractor import ExtractionError, extract_raw_markdown, ocr_available
from .markdown_utils import protect_non_hindi_syntax, restore_non_hindi_syntax

__all__ = [
    "__version__",
    "auto_detect_font",
    "convert_legacy_text",
    "krutidev_to_unicode",
    "walkman_to_unicode",
    "chanakya_to_unicode",
    "aps_to_unicode",
    "extract_raw_markdown",
    "ocr_available",
    "ExtractionError",
    "protect_non_hindi_syntax",
    "restore_non_hindi_syntax",
    "convert_pdf",
]

from .pipeline import convert_pdf
