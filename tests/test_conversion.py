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
from tests.corpus_aps import APS_WORDS
from tests.corpus_chanakya import CHANAKYA_WORDS
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


# --- pipeline edge cases -------------------------------------------------

def _pdf(tmp_path, name, text=None, **save_kw):
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    path = tmp_path / name
    doc.save(str(path), **save_kw)
    doc.close()
    return str(path)


def test_missing_file_raises_extraction_error(tmp_path):
    from src.extractor import ExtractionError
    from src.pipeline import convert_pdf
    with pytest.raises(ExtractionError):
        convert_pdf(str(tmp_path / "absent.pdf"))


def test_non_pdf_raises_extraction_error(tmp_path):
    from src.extractor import ExtractionError
    from src.pipeline import convert_pdf
    junk = tmp_path / "junk.pdf"
    junk.write_text("not a pdf")
    with pytest.raises(ExtractionError):
        convert_pdf(str(junk))


def test_encrypted_pdf_says_so(tmp_path):
    import pymupdf

    from src.extractor import ExtractionError
    from src.pipeline import convert_pdf
    path = _pdf(tmp_path, "enc.pdf", "hello",
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw="o", user_pw="u")
    with pytest.raises(ExtractionError, match="password protected"):
        convert_pdf(path)


def test_blank_pdf_warns_instead_of_silently_writing_nothing(tmp_path):
    from src.pipeline import convert_pdf
    md, _, warnings = convert_pdf(_pdf(tmp_path, "blank.pdf"))
    assert md.strip() == ""
    assert any("no text recovered" in w for w in warnings)


def test_english_pdf_is_passed_through(tmp_path):
    from src.pipeline import convert_pdf
    path = _pdf(tmp_path, "eng.pdf",
                "This is a plain English document about soil and water.")
    md, profile, _ = convert_pdf(path)
    assert profile == "english"
    assert "English document" in md


def test_protect_restore_is_identity_without_conversion():
    text = "plain ASCII 123 **bold** text (with) a [link](http://x.io/y)"
    protected, preserved = protect_non_hindi_syntax(text)
    assert restore_non_hindi_syntax(protected, preserved) == text


def test_every_profile_runs():
    from src.converter import PROFILES, convert_legacy_text
    for profile in PROFILES:
        assert isinstance(convert_legacy_text("vkSj gS", profile), str)


def test_marker_budget_is_enforced():
    from src.markdown_utils import MAX_MARKERS, MarkerOverflow, _marker
    assert _marker(MAX_MARKERS - 1)
    with pytest.raises(MarkerOverflow):
        _marker(MAX_MARKERS)


# --- passthrough integrity ------------------------------------------------
#
# A document that is already Unicode must come back exactly as the extractor
# produced it. Conversion is the only thing skipped; nothing may be "repaired".

@pytest.mark.parametrize("profile", ["unicode", "english", "hinglish"])
def test_passthrough_is_byte_identical(tmp_path, profile):
    import pymupdf

    from src.extractor import extract_raw_markdown
    from src.pipeline import clean_lines, convert_pdf, strip_extractor_scaffolding

    doc = pymupdf.open()
    doc.new_page().insert_htmlbox(
        pymupdf.Rect(50, 50, 520, 300),
        "<p>भारत में संसाधन नियोजन एक जटिल प्रक्रिया है। See the report.</p>",
    )
    path = str(tmp_path / "u.pdf")
    doc.save(path)
    doc.close()

    expected = clean_lines(strip_extractor_scaffolding(extract_raw_markdown(path)))
    assert convert_pdf(path, font=profile)[0] == expected


@pytest.mark.parametrize("text,expected_profile", [
    ("यह पूरी तरह यूनिकोड हिंदी दस्तावेज़ है। " * 10, "unicode"),
    ("Yeh ek mixed दस्तावेज़ hai jisme English और हिंदी dono हैं। " * 6, "hinglish"),
    ("A plain English document about soil and water resources. " * 6, "english"),
])
def test_unicode_documents_are_never_converted(text, expected_profile):
    from src.converter import PASSTHROUGH, auto_detect_font, convert_legacy_text
    assert auto_detect_font(text) == expected_profile
    assert expected_profile in PASSTHROUGH
    assert convert_legacy_text(text, "auto") == text


def test_hindi_document_quoting_legacy_sequences_is_not_converted():
    """A Hindi article *about* KrutiDev contains osQ and oqQN as examples."""
    from src.converter import convert_legacy_text
    text = "यह लेख KrutiDev के बारे में है। उदाहरण: osQ और oqQN जैसे अनुक्रम। " * 6
    assert convert_legacy_text(text, "auto") == text


def test_legacy_repairs_do_not_touch_ordinary_english():
    """These rules join words across markup; only legacy text may see them."""
    from src.pipeline import strip_extractor_scaffolding
    for text in [
        "vitamin **a** deficiency",
        "The word **s** appears here",
        "x<sup>2</sup> + y<sup>2</sup>",
    ]:
        assert strip_extractor_scaffolding(text) == text


def test_unicode_devanagari_fonts_are_not_treated_as_legacy():
    from src.pdf_spans import LEGACY_FONT_RE
    for family in ("mangal", "nirmala ui", "aparajita", "kokila",
                   "noto sans devanagari", "sanskrit text"):
        assert not LEGACY_FONT_RE.search(family), family
    for family in ("kruti dev 010", "devlys 010", "walkman-chanakya905"):
        assert LEGACY_FONT_RE.search(family), family


# --- font evidence (pdf_spans) -------------------------------------------

def _legacy_pdf(tmp_path, name="legacy.pdf"):
    """A PDF whose body font name looks legacy, with a Latin-font gloss."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "dks;ys osQ izpqj HkaMkj gSaA", fontname="helv")
    page.insert_text((72, 130), "(leaching)", fontname="tiro")
    path = str(tmp_path / name)
    doc.save(path)
    doc.close()
    return path


def test_font_report_on_a_latin_document(tmp_path):
    from src.pdf_spans import font_report
    report = font_report(_legacy_pdf(tmp_path))
    assert report["families"]
    assert report["dominant"]
    assert report["legacy_chars"] + report["latin_chars"] == sum(
        report["families"].values())


def test_font_report_and_spans_survive_a_broken_file(tmp_path):
    from src.pdf_spans import font_report, latin_spans, latin_terms
    junk = tmp_path / "junk.pdf"
    junk.write_text("not a pdf")
    assert font_report(str(junk)) == {}
    assert latin_spans(str(junk)) == []
    assert latin_terms(str(junk)) == set()


def test_font_report_and_spans_on_a_missing_file():
    from src.pdf_spans import font_report, latin_spans, latin_terms
    assert font_report("/no/such/file.pdf") == {}
    assert latin_spans("/no/such/file.pdf") == []
    assert latin_terms("/no/such/file.pdf") == set()


def test_latin_spans_are_returned_in_document_order(tmp_path):
    """Order is what separates "(i)" the numeral from "(v)" the letter अ."""
    import pymupdf

    from src.pdf_spans import latin_spans
    doc = pymupdf.open()
    page = doc.new_page()
    # The dominant font stands in for legacy body text; spans in any other
    # font are the ones reported back.
    for i in range(12):
        page.insert_text((72, 80 + i * 14), "body text " * 6, fontname="helv")
    for i, word in enumerate(["first", "second", "third"]):
        page.insert_text((72, 300 + i * 20), word, fontname="tiro")
    path = str(tmp_path / "ordered.pdf")
    doc.save(path)
    doc.close()
    spans = latin_spans(path)
    assert [s for s in spans if s in {"first", "second", "third"}] == [
        "first", "second", "third"]


@pytest.mark.parametrize("raw,expected", [
    ("ZQYALE+APS-DV-PriyankaRoman,Bold", "aps-dv-priyankaroman"),
    ("HYGCJZ+APS-DV-Priyanka", "aps-dv-priyanka"),
    ("OXSMKS+Walkman-Chanakya905Normal", "walkman-chanakya905"),
    ("UDVFPN+Walkman-Chanakya905BoldItalic", "walkman-chanakya905"),
    ("XWCAQQ+TimesNewRoman", "timesnewroman"),
    ("ArialMT", "arial"),
    ("AAANMJ+Calibri-Bold", "calibri"),
    ("NotoSerifDevanagari-Regular", "notoserifdevanagari"),
])
def test_font_family_normalisation(raw, expected):
    """APS-DV-Priyanka once normalised to "a", which hid a legacy font."""
    from src.pdf_spans import _family
    assert _family(raw) == expected


def test_unsupported_legacy_font_is_flagged():
    from src.pdf_spans import LEGACY_FONT_RE, SUPPORTED_FONT_RE
    for family in ("shree-lipi", "akruti", "shusha"):
        assert LEGACY_FONT_RE.search(family)
        assert not SUPPORTED_FONT_RE.search(family), family
    for family in ("kruti dev 010", "devlys 010", "walkman-chanakya905",
                   "chanakya", "aps-dv-priyanka"):
        assert SUPPORTED_FONT_RE.search(family), family


# --- extractor ------------------------------------------------------------

def test_ocr_available_returns_a_bool():
    from src.extractor import ocr_available
    assert isinstance(ocr_available(), bool)


def test_extractor_reports_page_selection(tmp_path):
    import pymupdf

    from src.extractor import extract_raw_markdown
    doc = pymupdf.open()
    for word in ("alpha", "beta", "gamma"):
        doc.new_page().insert_text((72, 100), word)
    path = str(tmp_path / "pages.pdf")
    doc.save(path)
    doc.close()
    only_second = extract_raw_markdown(path, pages=[1], ocr=False)
    assert "beta" in only_second
    assert "alpha" not in only_second


def test_extraction_error_is_raised_for_a_directory(tmp_path):
    from src.extractor import ExtractionError, extract_raw_markdown
    with pytest.raises(ExtractionError):
        extract_raw_markdown(str(tmp_path))


# --- pipeline -------------------------------------------------------------

def test_drop_patterns_remove_matching_lines():
    from src.pipeline import clean_lines
    text = "keep me\nReprint 2024-25\nChapter 7\nkeep me too"
    out = clean_lines(text, drop_patterns=[r"^Chapter \d+$"])
    assert "Reprint" not in out
    assert "Chapter 7" not in out
    assert out.count("keep me") == 2


def test_enhance_ocr_without_opencv_is_a_warning_not_a_crash(tmp_path, monkeypatch):
    import src.image_cleaner as cleaner
    from src.pipeline import convert_pdf

    def boom(*a, **k):
        raise cleaner.OpenCVMissing("no opencv")

    monkeypatch.setattr(cleaner, "enhance_pdf_images", boom)
    _, _, warnings = convert_pdf(_pdf(tmp_path, "x.pdf", "hello"),
                                 enhance_ocr=True, ocr=False)
    assert any("image enhancement skipped" in w for w in warnings)


# --- detection regressions from real documents ----------------------------
#
# Each case below was a wrong answer on a real PDF before it was fixed.

def test_english_prose_is_not_mistaken_for_legacy():
    """Unanchored signatures matched inside "also", "these", "worlds"."""
    from src.converter import auto_detect_font
    text = ("The world's diseases also fall under these categories. "
            "Children worldwide need shelters and food supplies. " * 40)
    assert auto_detect_font(text) == "english"


def test_a_unicode_heading_does_not_veto_legacy_body_text():
    """A Unicode caption over pages of KrutiDev left whole books unconverted."""
    from src.converter import auto_detect_font
    text = "अध्याय 1\n" + ("jktLFkku dh fLFkfr vkSj foLrkj ds lUnHkZ esa " * 40)
    assert auto_detect_font(text) == "krutidev"


def test_a_mostly_devanagari_document_is_left_alone():
    from src.converter import auto_detect_font, convert_legacy_text
    text = "यह लेख KrutiDev के बारे में है। उदाहरण: osQ और oqQN जैसे। " * 6
    assert auto_detect_font(text) in {"unicode", "hinglish"}
    assert convert_legacy_text(text, "auto") == text


def test_an_unsupported_encoding_is_not_claimed_as_krutidev():
    """APS-DV-Priyanka scored 24 false signature hits before anchoring."""
    from src.converter import auto_detect_font
    aps = "efJeJejCeelcekeâ meeceevÙe DeOÙeÙeve ØeLece ØeMve-he$e " * 30
    assert auto_detect_font(aps) not in {"krutidev", "walkman"}


def test_walkman_signatures_still_win_over_krutidev():
    from src.converter import auto_detect_font
    assert auto_detect_font("dks;ys osQ izpqj HkaMkj gSaA oqQN " * 20) == "walkman"


# --- OCR defaults ---------------------------------------------------------

def test_ocr_language_defaults_to_hindi_plus_english():
    """"hin" alone renders a scanned English page as Devanagari nonsense:
    measured 909 Devanagari characters against 18 Latin on a UPSC paper."""
    import inspect

    from src.extractor import extract_raw_markdown
    from src.pipeline import convert_pdf
    for fn in (extract_raw_markdown, convert_pdf):
        assert inspect.signature(fn).parameters["ocr_language"].default == "hin+eng"


def test_cli_passes_ocr_options_through(tmp_path, monkeypatch):
    import src.cli as cli
    seen = {}

    def fake(path, **kwargs):
        seen.update(kwargs)
        return "out", "english", []

    monkeypatch.setattr(cli, "convert_pdf", fake)
    out = tmp_path / "o.md"
    assert cli.main(["-q", "--input", "x.pdf", "--output", str(out),
                     "--ocr-dpi", "600", "--ocr-language", "hin"]) == 0
    assert seen["ocr_dpi"] == 600
    assert seen["ocr_language"] == "hin"
    assert out.read_text(encoding="utf-8") == "out"


def test_cli_reports_failure_with_a_nonzero_exit(tmp_path, monkeypatch):
    import src.cli as cli
    from src.extractor import ExtractionError

    def boom(path, **kwargs):
        raise ExtractionError("nope")

    monkeypatch.setattr(cli, "convert_pdf", boom)
    assert cli.main(["-q", "--input", "x.pdf", "--output",
                     str(tmp_path / "o.md")]) == 1


def test_cli_with_no_arguments_prints_help():
    import src.cli as cli
    assert cli.main([]) == 1


def test_cli_batch_mode_reports_an_empty_directory(tmp_path):
    import src.cli as cli
    assert cli.main(["-q", "--dir", str(tmp_path)]) == 1


def test_colour_is_disabled_when_not_a_terminal():
    """Escape codes used to land in redirected output files."""
    import io

    from src.cli import _Style
    assert _Style(io.StringIO()).cyan("x") == "x"


# --- Chanakya, and legacy streams reported through MacRoman ---------------

@pytest.mark.parametrize("source,expected", CHANAKYA_WORDS)
def test_chanakya_real_words(source, expected):
    from src.chanakya_converter import chanakya_to_unicode
    assert chanakya_to_unicode(source) == expected


def test_macroman_stream_is_re_read_as_windows_1252():
    """One publisher's PDFs report legacy bytes through a MacRoman map."""
    from src.converter import normalise_legacy_encoding
    mac = "⁄UÊ¡SÕÊŸ ‚Ê◊Êãÿ ôÊÊŸ ∑§ Á‹∞ •Ê¡ „UË " * 3
    assert normalise_legacy_encoding(mac).startswith("ÚUæÁSÍæÙ âæ×æ‹Ø")


def test_macroman_normalisation_is_idempotent():
    from src.converter import normalise_legacy_encoding as norm
    mac = "⁄UÊ¡SÕÊŸ ‚Ê◊Êãÿ ôÊÊŸ ∑§ Á‹∞ •Ê¡ „UË " * 3
    once = norm(mac)
    assert norm(once) == once


def test_macroman_normalisation_leaves_other_text_alone():
    from src.converter import normalise_legacy_encoding as norm
    for text in ["dks;ys osQ izpqj HkaMkj gSaA", "यह सामान्य हिंदी है।",
                 "Plain English text with a fine flat file."]:
        assert norm(text) == text


def test_macroman_normalisation_keeps_safe_tokens_intact():
    """Round-tripping through bytes dropped the markers and shifted the text."""
    from src.converter import normalise_legacy_encoding as norm
    from src.markdown_utils import _marker
    token = _marker(0)
    mac = "⁄UÊ¡SÕÊŸ ‚Ê◊Êãÿ ôÊÊŸ ∑§ Á‹∞ •Ê¡ „UË " * 3 + token
    assert token in norm(mac)


def test_ligature_expansion_is_recomposed():
    """The Markdown extractor expands the fl ligature to two letters, and in
    MacRoman that byte carries व."""
    from src.chanakya_converter import chanakya_to_unicode
    from src.converter import normalise_legacy_encoding as norm
    ligature = "\ufb02"
    word = "\u2044U\u00ca" + ligature + "\u2039"          # रावल, MacRoman
    mac = "⁄UÊ¡SÕÊŸ ‚Ê◊Êãÿ ôÊÊŸ ∑§ Á‹∞ •Ê¡ „UË " * 3
    assert "रावल" in chanakya_to_unicode(norm(mac + word))
    expanded = word.replace(ligature, "fl")               # as the extractor gives it
    assert "रावल" in chanakya_to_unicode(norm(mac + expanded))


def test_thin_output_is_flagged_as_probably_scanned(tmp_path):
    """A file of nothing but watermarks used to be written out silently."""
    import pymupdf

    from src.pipeline import convert_pdf
    doc = pymupdf.open()
    for _ in range(6):
        doc.new_page().insert_text((72, 72), "Join for more @channel")
    path = str(tmp_path / "thin.pdf")
    doc.save(path)
    doc.close()
    _, _, warnings = convert_pdf(path, ocr=False)
    assert any("characters recovered" in w for w in warnings)


def test_a_normal_document_is_not_flagged_as_thin(tmp_path):
    import pymupdf

    from src.pipeline import convert_pdf
    doc = pymupdf.open()
    for _ in range(4):
        page = doc.new_page()
        for row in range(40):
            page.insert_text((50, 60 + row * 16),
                             "This is an ordinary line of body text on the page.")
    path = str(tmp_path / "full.pdf")
    doc.save(path)
    doc.close()
    _, _, warnings = convert_pdf(path, ocr=False)
    assert not any("characters recovered" in w for w in warnings)


# --- APS-DV-Priyanka ------------------------------------------------------

@pytest.mark.parametrize("source,expected", APS_WORDS)
def test_aps_real_words(source, expected):
    from src.aps_converter import aps_to_unicode
    assert aps_to_unicode(source) == expected


def test_aps_stem_rule():
    """'e' is the vertical stem: it completes a stem-less letter, and reads as
    ा after one that already has its own."""
    from src.aps_converter import aps_to_unicode
    assert aps_to_unicode("veeje") == "नारा"        # ve is one letter, je is र + ा
    assert aps_to_unicode("Deeboesueve") == "आंदोलन"
    assert aps_to_unicode("jne~") == "रहा।"


def test_aps_is_detected_over_the_other_legacy_profiles():
    from src.converter import auto_detect_font
    text = "ØeLece efJeÕe Ùegæ kesâ yeeo cepeotjeW kesâ DeeboesueveeW ceW " * 6
    assert auto_detect_font(text) == "aps"


def test_aps_reph_moves_to_the_front_of_its_cluster():
    from src.aps_converter import aps_to_unicode
    assert aps_to_unicode("keâeÙe&keâeefjCeer") == "कार्यकारिणी"
