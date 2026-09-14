# -*- coding: utf-8 -*-
"""KrutiExtract - legacy Hindi PDF to Markdown."""

__version__ = "1.6.0"

from .aakriti_converter import aakriti_to_unicode
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
from .shreelipi_converter import shreelipi_to_unicode
from .shusha_converter import shusha_to_unicode

__all__ = [
    "__version__",
    "auto_detect_font",
    "convert_legacy_text",
    "krutidev_to_unicode",
    "walkman_to_unicode",
    "chanakya_to_unicode",
    "aps_to_unicode",
    "aakriti_to_unicode",
    "shreelipi_to_unicode",
    "shusha_to_unicode",
    "extract_raw_markdown",
    "ocr_available",
    "ExtractionError",
    "protect_non_hindi_syntax",
    "restore_non_hindi_syntax",
    "convert_pdf",
]

from .pipeline import convert_pdf
