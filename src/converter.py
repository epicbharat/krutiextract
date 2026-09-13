# -*- coding: utf-8 -*-
"""Legacy Hindi encoding -> Devanagari Unicode.

Three legacy encodings are supported, and they are genuinely different fonts
with conflicting rules, not dialects of one map:

  krutidev  KrutiDev 010 / DevLys 010.  `=k` is त्रा, `osQ` is वेफ.
  walkman   Walkman-Chanakya 905.  `=k` is त्र, `osQ` is के, `¼` is द्ध.
            This is the font NCERT uses for its Hindi textbooks.
  chanakya  Chanakya (see chanakya_map.py).

Applying walkman rules to a krutidev document corrupts it and vice versa, so
the profile is detected per document rather than hard-coded.

Both Latin-mapped profiles run the same three stages:
  1. profile pre-rules   (visual keyboard hacks that combine two keys)
  2. ordered map replace (array_one[i] -> array_two[i])
  3. structural passes   (short-i matra, reph reordering, cleanup)
"""

import re
import unicodedata
from typing import Dict, List, Sequence, Tuple

from .aps_converter import aps_to_unicode
from .chanakya_converter import chanakya_to_unicode
from .krutidev_map import array_one, array_two
from .markdown_utils import is_marker

__all__ = [
    "convert_legacy_text",
    "normalise_legacy_encoding",
    "krutidev_to_unicode",
    "walkman_to_unicode",
    "aps_to_unicode",
    "auto_detect_font",
    "PROFILES",
]

PROFILES = ("krutidev", "devlys", "walkman", "ncert", "chanakya", "aps",
            "priyanka", "unicode", "english", "hinglish")

_ALIASES = {"devlys": "krutidev", "ncert": "walkman", "priyanka": "aps"}

#: Profiles that need no conversion at all. For these the whole
#: protect/convert/restore cycle is skipped, so nothing can be damaged.
PASSTHROUGH = ("unicode", "english", "hinglish")

# --------------------------------------------------------------------------
# Devanagari character classes used by the structural passes
# --------------------------------------------------------------------------

HALANT = "्"          # ्
NUKTA = "़"           # ़

# Dependent signs only. Independent vowels are deliberately excluded: a reph
# never attaches across one. A space is NOT a matra -- treating it as one made
# 'jke ksZ' come out as 'रार्म ो'.
MATRAS = frozenset(
    "ािीुूृॄॢॣ"   # ा ि ी ु ू ृ ॄ ॢ ॣ
    "ॅॆेै"                                   # ॅ ॆ े ै
    "ॉॊोौ"                                   # ॉ ॊ ो ौ
    "ँंः"                                         # ँ ं ः
    + NUKTA
)

# --------------------------------------------------------------------------
# Profile definitions
# --------------------------------------------------------------------------

# Keys that can sit between the two halves of a Walkman two-key letter.
_WALKMAN_MEDIALS = r"[sSqwkah`‚¡]{0,2}"

_WALKMAN_PRE: Sequence[Tuple[str, str]] = (
    # In Walkman-Chanakya 905 the code 'Q' is a hook glyph that reshapes the
    # letter before it, so two keys make one letter. Rewrite to the canonical
    # single-letter spelling before the map runs.
    (rf"o({_WALKMAN_MEDIALS})Q", r"d\1"),     # o..Q -> क..   (osQ के, oqQ कु)
    (rf"i({_WALKMAN_MEDIALS})Q", r"Q\1"),     # i..Q -> फ..   (iQ फ, lkiQ साफ)
    (r"mQ", "Å"),                         # mQ   -> ऊ
)

# Spelling variants, normalised first so that _WALKMAN_PRE can then apply.
_WALKMAN_PRE0: Sequence[Tuple[str, str]] = (
    # An alternate spelling of "i" (प): I+kqQy and iqQy both render फुल.
    (r"I\+k", "i"),
)

# Map entries where Walkman assigns a different letter from KrutiDev.
# 'find' must already exist in array_one; 'insert_after' adds a new entry.
_WALKMAN_OVERRIDES: Dict[str, str] = {
    "=kk": "त्रा",   # त्रा  (was an intermediate "=k")
    "f=k": "fत्र",        # fत्र  (was an intermediate "f=")
    "¼": "द्ध",      # ¼ -> द्ध   (KrutiDev: "(" )
    "½": "ऋ",                  # ½ -> ऋ     (KrutiDev: ")" )
    "/": "ध",                  # /  -> ध     (KrutiDev: ध् )
    "/k": "धा",           # /k -> धा    (KrutiDev: ध  )
    # Punctuation. Walkman keeps ASCII brackets and quotes as punctuation
    # where KrutiDev assigns them letters. Verified against the embedded
    # font: "(d)" is "(क)", "lqy>k,¡_" is "सुलझाएँ;", "^x*" is "‘ग’".
    "\u00df": "\u0939\u094d\u0930",   # ß -> ह्र  (ßkl ह्रास; KrutiDev gives a quote)
    "(": "(",
    ")": ")",
    "^": "\u2018",
    "*": "\u2019",
}

# New entries, inserted immediately after the named existing key.
_WALKMAN_INSERTS: Sequence[Tuple[str, str, str]] = (
    ("f=k", "=k", "त्र"),  # =k -> त्र, after the =kk/f=k pair
)

# Entries with no KrutiDev counterpart, tried before everything else.
_WALKMAN_PREPEND: Sequence[Tuple[str, str]] = (
    # Decomposed nukta (ज + ़), matching the rest of the map. The precomposed
    # U+095B is not NFC-stable, so emitting it would give two spellings of the
    # same word depending on the code path.
    ("\u201dk", "\u091c\u093c"),           # ”k -> ज़   (rs”k तेज़)
    ("\u201d", "\u091c\u093c\u094d"),      # ”  -> ज़्  (”;knk ज़्यादा)
)

# Entries that must run last, because their replacement is a character an
# earlier entry would otherwise consume ("_" -> ";" and ";" -> य).
_WALKMAN_APPEND: Sequence[Tuple[str, str]] = (
    ("_", ";"),
)


def _build_map(profile: str) -> Tuple[List[str], List[str]]:
    one, two = list(array_one), list(array_two)
    if profile != "walkman":
        return one, two
    for key, val in _WALKMAN_OVERRIDES.items():
        two[one.index(key)] = val
    for after, key, val in _WALKMAN_INSERTS:
        pos = one.index(after) + 1
        one.insert(pos, key)
        two.insert(pos, val)
    for key, val in reversed(_WALKMAN_PREPEND):
        one.insert(0, key)
        two.insert(0, val)
    for key, val in _WALKMAN_APPEND:
        if key in one:
            idx = one.index(key)
            one.pop(idx)
            two.pop(idx)
        one.append(key)
        two.append(val)
    return one, two


_COMPILED: Dict[str, List[Tuple["re.Pattern", str]]] = {}


def _compiled(profile: str) -> List[Tuple["re.Pattern", str]]:
    if profile not in _COMPILED:
        one, two = _build_map(profile)
        _COMPILED[profile] = [
            (re.compile(re.escape(a)), b.replace("\\", "\\\\")) for a, b in zip(one, two)
        ]
    return _COMPILED[profile]


# --------------------------------------------------------------------------
# Structural passes
# --------------------------------------------------------------------------

def _apply_short_i(text: str, trigger: str = "f", matra: str = "ि") -> str:
    """Move the pre-posed short-i matra to after the letter it belongs to.

    Left to right, index-safe. The previous implementation used a global
    str.replace inside a find() loop, so every edit invalidated the cursor.
    A safe token is never treated as a letter: attaching a matra to a
    protected English word is always wrong.
    """
    step = len(trigger)
    out: List[str] = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith(trigger, i) and i + step < n:
            nxt = text[i + step]
            if is_marker(nxt):
                out.append(text[i:i + step])
                i += step
                continue
            out.append(nxt)
            out.append(matra)
            i += step + 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _repair_matra_halant(text: str, matra: str = "ि") -> str:
    """Fix `<matra><halant><consonant>` into `<halant><consonant><matra>`.

    Produced when the short-i pass lands on the first half of a conjunct.
    """
    out = list(text)
    i = 0
    while i < len(out) - 2:
        if out[i] == matra and out[i + 1] == HALANT:
            cons = out[i + 2]
            out[i:i + 3] = [HALANT, cons, matra]
            i += 3
            continue
        i += 1
    return "".join(out)


def _apply_reph(text: str, trigger: str = "Z") -> str:
    """Move the reph mark to the front of the cluster it belongs to.

    Rewritten from the original find/replace loop, which had three defects:
    a `Z` at index 0 aborted the whole pass, str.replace applied every edit
    globally, and the matra set was a space-separated string so a space
    counted as a matra and the scan ran into the previous word.
    """
    out: List[str] = []
    for ch in text:
        if ch != trigger:
            out.append(ch)
            continue
        j = len(out)
        while j > 0 and out[j - 1] in MATRAS:
            j -= 1
        if j == 0:
            continue                       # nothing to attach to; drop it
        k = j - 1                          # last letter of the cluster
        while k - 1 >= 1 and out[k - 1] == HALANT:
            k -= 2                         # step to the head of the conjunct
        if k < 0 or is_marker(out[k]):
            continue
        out[k:k] = ["र", HALANT]      # र्
    return "".join(out)


_CLEANUP = (
    ("ंे", "ें"),      # ंे -> ें
    ("ंो", "ों"),      # ंो -> ों
    ("ाे", "ो"),            # ाे -> ो
    ("ाॅ", "ॉ"),       # ा + ॅ -> ॉ  (the fonts compose ॉ from two marks)
    ("आॅ", "ऑ"),       # आ + ॅ -> ऑ
    ("एॅ", "ऍ"),       # ए + ॅ -> ऍ
)


def _convert_latin(text: str, profile: str) -> str:
    if not text:
        return ""

    s = text
    if profile == "walkman":
        for pat, rep in _WALKMAN_PRE0:
            s = re.sub(pat, rep, s)
        for pat, rep in _WALKMAN_PRE:
            s = re.sub(pat, rep, s)
    # No 'osQ -> के' shortcut here: KRDEV010 renders osQ as वेफ. Documents that
    # really mean के are Walkman-Chanakya and are routed to that profile.

    for pattern, repl in _compiled(profile):
        s = pattern.sub(repl, s)

    s = re.sub(r"±", "Zं", s)      # ± -> reph + anusvara
    s = re.sub(r"Æ", "Zf", s)           # Æ -> reph + short-i
    s = re.sub(r"£", "Zf", s)           # £ -> reph + short-i
    # NOTE: £ used to be expanded after the short-i pass, which left a bare
    # 'f' in the output for every word that used it.

    s = _apply_short_i(s, "f")

    s = re.sub(r"Ç", "fa", s)
    s = re.sub(r"É", "Zfa", s)
    s = re.sub(r"¯", "fa", s)
    s = s.replace("ð", "")

    s = _apply_short_i(s, "fa", "िं")
    s = re.sub(r"Ê", "ीZ", s)      # Ê -> ी + reph

    s = _repair_matra_halant(s)
    s = _apply_reph(s)

    for a, b in _CLEANUP:
        s = s.replace(a, b)
    # One spelling per word: NFC leaves the decomposed nukta alone but tidies
    # anything else the map may have produced in two forms.
    return unicodedata.normalize("NFC", s)


def krutidev_to_unicode(text: str) -> str:
    """Convert KrutiDev 010 / DevLys 010 text."""
    return _convert_latin(text, "krutidev")


def walkman_to_unicode(text: str) -> str:
    """Convert Walkman-Chanakya 905 text (NCERT Hindi textbooks)."""
    return _convert_latin(text, "walkman")


# --------------------------------------------------------------------------
# Byte re-interpretation
# --------------------------------------------------------------------------

# Some producers report a legacy 8-bit stream through a MacRoman ToUnicode
# map, so the same font bytes surface as different characters. These appear in
# a MacRoman reading and in neither legacy map, so they identify the case
# without false positives: measured at 23% of the non-ASCII characters in one
# such book and zero occurrences across the Windows-encoded ones.
_MACROMAN_HINT = re.compile("[\u2044\u2211\u25ca\ufb02\u02dd\u220f\u00f8\u03c0\uf8ff]")


def _build_macroman_table():
    """MacRoman character -> the Windows-1252 character for the same byte.

    A translation table rather than encode/decode, because the string may hold
    safe tokens and Devanagari that MacRoman cannot encode. Round-tripping
    through bytes dropped those silently and corrupted the text around them.
    Byte values below 0x80 are identical in both, so they are left alone.
    """
    table = {}
    for byte in range(0x80, 0x100):
        raw = bytes([byte])
        try:
            mac = raw.decode("mac_roman")
            win = raw.decode("cp1252")
        except UnicodeDecodeError:
            continue
        if mac != win:
            table[ord(mac)] = win
    return table


_MACROMAN_TABLE = _build_macroman_table()


# The Markdown extractor expands the fi/fl ligatures to plain letter pairs
# before this module sees them, and in MacRoman those two code points are the
# bytes 0xDE and 0xDF -- which carry letters, not ligatures, in a legacy font.
# Recomposing is safe here: under the Chanakya map "fl" and "fi" would decode
# to द्घद्य and द्घद्ब, two half-conjuncts in a row, which Devanagari never has.
_LIGATURES = (("fi", "\ufb01"), ("fl", "\ufb02"))


def normalise_legacy_encoding(text: str) -> str:
    """Re-read a MacRoman-reported legacy stream as Windows-1252.

    A no-op for everything else, and idempotent: the marker characters cannot
    survive the translation.
    """
    if not text:
        return text
    if len(_MACROMAN_HINT.findall(text)) < max(8, len(text) * 0.005):
        return text
    for plain, ligature in _LIGATURES:
        text = text.replace(plain, ligature)
    return text.translate(_MACROMAN_TABLE)


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")

# Two-key sequences that only make sense in Walkman-Chanakya. In KrutiDev they
# would spell वेफ / वुफ / पफ, which are not Hindi words.
_WALKMAN_SIG = re.compile(r"o[sSqwkah`]{0,2}Q|i[sSqwkah`]{0,2}Q|mQ")

# Multi-character Chanakya signatures. Single characters like Ü or ß are not
# usable: they occur in KrutiDev too.
_CHANAKYA_SIG = re.compile(r"ãñ|¥æ|·¤|ðU|Ð|Áè|ãè|æ¢")

# APS-DV-Priyanka. "eâ" is its shaping pair and "Deeb"/"kesâ"/"efJe" are
# everyday words; none of them mean anything in the other encodings.
_APS_SIG = re.compile(r"eâ|kesâ|efJe|Deeb|ceW|Ùeg")

# Whole tokens only. Without the boundaries these matched inside ordinary
# English ("also", "these", "worlds"), which made a plain English document
# look like KrutiDev.
_KRUTI_SIG = re.compile(
    r"\b(vkSj|gS|gSa|gSaA|ds|dh|dk|dks|esa|ls|ij|fd|;g|og|ugha|Fkk|Fks|gks|dj|"
    r"ftl|bl|ml|;s|oS|ijarq|rFkk)\b"
)

_TOKEN = re.compile(r"\b[A-Za-z;'\"]+\b")

#: Legacy signatures per Latin token needed to claim a legacy profile.
#: Measured: real legacy documents run 0.089-0.165; English prose and
#: unsupported encodings score 0.000.
_LEGACY_RATIO = 0.02


def auto_detect_font(text: str) -> str:
    """Return the encoding profile for *text*.

    Order matters. A document that is already Devanagari must never be pushed
    through a legacy map: the old detector counted the substrings 'ds' and 'dh'
    anywhere, so a Unicode Hindi page containing the English words 'kids' or
    'and the' was classified as KrutiDev and destroyed.
    """
    if not text:
        return "unicode"

    text = normalise_legacy_encoding(text)
    deva = len(_DEVANAGARI.findall(text))
    latin = len(_LATIN.findall(text))
    tokens = len(_TOKEN.findall(text)) or 1

    walkman = len(_WALKMAN_SIG.findall(text))
    chanakya = len(_CHANAKYA_SIG.findall(text))
    kruti = len(_KRUTI_SIG.findall(text))

    # Already mostly Devanagari: nothing to convert, whatever stray legacy
    # sequences appear. This covers a Hindi article that merely quotes "osQ"
    # as an example. Measured on real files, documents needing conversion sit
    # at a Devanagari/Latin ratio of 0.00 and documents needing passthrough at
    # 2.5 and above, so the boundary is not delicate.
    if deva > latin:
        return "hinglish" if latin > deva * 0.25 else "unicode"

    # Otherwise legacy evidence is weighed before the script census. A book can carry a
    # Unicode heading or an OCR'd caption over pages of KrutiDev; letting a
    # handful of Devanagari characters veto that left the whole file
    # unconverted. Devanagari already in the text is unaffected by conversion,
    # since none of it appears in the legacy maps.
    aps = len(_APS_SIG.findall(text))
    if aps > max(kruti, walkman, chanakya):
        return "aps"
    if chanakya > max(kruti, walkman):
        return "chanakya"
    if walkman:
        # These two-key sequences spell वेफ / पफ / उफ under KrutiDev, so they
        # are decisive rather than merely suggestive.
        return "walkman"
    if kruti / tokens >= _LEGACY_RATIO:
        return "krutidev"

    # No usable legacy evidence. An unsupported encoding lands here too, which
    # is the safe outcome: no conversion beats a confidently wrong one.
    if deva:
        return "hinglish" if latin > deva * 0.25 else "unicode"
    return "english" if latin else "unicode"


def convert_legacy_text(text: str, font: str = "auto") -> str:
    font = (font or "auto").lower()
    if font == "auto":
        font = auto_detect_font(text)
    font = _ALIASES.get(font, font)

    if font in PASSTHROUGH:
        return text
    text = normalise_legacy_encoding(text)
    if font == "chanakya":
        return chanakya_to_unicode(text)
    if font == "aps":
        return aps_to_unicode(text)
    if font == "walkman":
        return _convert_latin(text, "walkman")
    return _convert_latin(text, "krutidev")
