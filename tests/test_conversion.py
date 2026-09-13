# -*- coding: utf-8 -*-
"""Regression suite. Every pair is anchored to a font or a rendered page."""

import pytest

from src.converter import (
    auto_detect_font,
    convert_legacy_text,
    krutidev_to_unicode,
    walkman_to_unicode,
)
from src.markdown_utils import (
    protect_non_hindi_syntax,
    restore_non_hindi_syntax,
)
from tests.corpus import WORDS
from tests.corpus_walkman import WALKMAN_WORDS


@pytest.mark.parametrize("source,expected", WORDS)
def test_krutidev(source, expected):
    assert krutidev_to_unicode(source) == expected


@pytest.mark.parametrize("source,expected", WALKMAN_WORDS)
def test_walkman(source, expected):
    assert walkman_to_unicode(source) == expected


def roundtrip(text, font="auto"):
    protected, preserved = protect_non_hindi_syntax(text)
    return restore_non_hindi_syntax(convert_legacy_text(protected, font), preserved)


@pytest.mark.parametrize("text,expected", [
    ("**Committee** dk;Z", "**Committee** कार्य"),
    ("## Committee", "## Committee"),
    ("- igyk fcanq", "- पहला बिंदु"),
    ("1. igyk", "1. पहला"),
    ("eku 3.5 izfr'kr gS", "मान 3.5 प्रतिशत है"),
    ("50% yksx", "50% लोग"),
    ("<b>vkSj</b>", "<b>और</b>"),
    ("izkS|ksfxdh", "प्रौद्योगिकी"),
])
def test_markdown_survives(text, expected):
    assert roundtrip(text, "krutidev" if "izkS" not in text else "walkman") == expected


def test_table_structure_survives():
    src = "| uke | vk;q |\n|---|---|\n| jke | 30 |"
    out = roundtrip(src, "krutidev")
    assert out.splitlines()[1] == "|---|---|"
    assert "नाम" in out and "राम" in out


def test_link_target_survives():
    src = "[ns[ksa](https://www.ujiyari.com/current-affairs/september-2026)"
    assert roundtrip(src, "krutidev") == (
        "[देखें](https://www.ujiyari.com/current-affairs/september-2026)")


def test_unicode_document_is_not_mangled():
    text = "यह आधुनिक हिंदी है। " * 30 + "kids and the report"
    assert auto_detect_font(text) == "unicode"
    assert convert_legacy_text(text, "auto") == text


def test_walkman_is_detected_over_krutidev():
    assert auto_detect_font("dks;ys osQ izpqj HkaMkj gSaA") == "walkman"


def test_reph_does_not_cross_a_space():
    assert krutidev_to_unicode("jke ksZ") != "रार्म ो"


def test_leading_reph_does_not_abort_the_pass():
    assert "Z" not in krutidev_to_unicode("Z dk;Z ppkZ fuekZ.k")


def test_backtick_is_a_matra_not_inline_code():
    """'`' is the ृ matra. Treating a backtick pair as inline code would
    protect every Hindi word between two of them, which is what used to
    leave whole paragraphs unconverted."""
    assert krutidev_to_unicode("i`Foh") == "पृथ्वी"
    assert "`" not in roundtrip("izo`fÙk vkSj lLo`fr", "krutidev")


def test_marker_is_not_a_word_character():
    import re
    from src.markdown_utils import _marker
    assert not re.match(r"\w", _marker(0))


@pytest.mark.parametrize("source,expected", [
    ("ãñ", "है"),
    ("¥æñÚU", "और"),
    ("·¤æ", "का"),
    ("çß·¤æâ", "विकास"),
    ("ÖæÚUÌ", "भारत"),
    ("â¢âæÏÙ", "संसाधन"),
])
def test_chanakya(source, expected):
    from src.chanakya_converter import chanakya_to_unicode
    assert chanakya_to_unicode(source) == expected


def test_chanakya_is_detected():
    assert auto_detect_font("ÖæÚUÌ ×ð´ â¢âæÏÙ ãñ ¥æñÚU çß·¤æâ") == "chanakya"
