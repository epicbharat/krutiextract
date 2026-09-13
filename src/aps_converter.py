# -*- coding: utf-8 -*-
"""APS-DV-Priyanka -> Devanagari Unicode.

A different design from the KrutiDev family, so it gets its own converter
rather than a profile of the shared map.

The organising idea, read off the font: **code 101 ``e`` is the vertical
stem.** A consonant is stored as its stem-less shape, and ``e`` completes it.
Where the letter already carries its own stem (र, ह, द, ट, ड, ढ, छ), a
following ``e`` is not part of the letter and reads as the ा matra instead.
That single rule resolves what otherwise looks contradictory: ``veeje`` is
नारा (न + ा + र + ा) while ``Deeboesueve`` is आंदोलन, where ``ve`` is one
letter.

The rest follows the usual legacy conventions: ``ef`` pre-poses the short i,
``&`` is a reph typed after its syllable and moved to the front of the
cluster, ``â`` is a shaping character with no output, and ो is written as
ा + े, so the KrutiDev-style cleanups apply unchanged.

Derived and verified against a 336-page exam compilation set in the font:
every pair in tests/corpus_aps.py, and 0.27% unmapped characters across 110
held-out pages.
"""

__all__ = ["aps_to_unicode"]

HALANT = "्"

#: Stem-less consonants: <base> + "e" is the full letter, <base> alone is the
#: half form.
_STEM = {
    "k": "क", "K": "ख", "i": "ग", "I": "घ", "Û": "च", "p": "ज", "P": "झ",
    "C": "ण", "l": "त", "L": "थ", "O": "ध", "v": "न", "h": "प", "H": "फ",
    "Ò": "फ", "y": "ब", "Y": "भ", "c": "म", "Ù": "य", "u": "ल", "J": "व",
    "M": "श", "<": "ष", "m": "स", "Õ": "श्व", "Ø": "प्र", "#": "क्ष",
    "$": "त्र", "«": "ग्र", "›": "क्र", "Å": "द्य", "Œ": "क्र",
    "°": "ष्ट", "„": "ष्ट", "…": "ष्ठ", "%": "ज्ञ", "ß": "श्र", "ò": "त्त",
}

#: Letters that already carry their own stem: a following "e" is the ा matra.
_WHOLE = {
    "j": "र", "n": "ह", "o": "द", '"': "ठ", "[": "ड", "I": "ढ", "Ú": "छ",
    "æ": "द्ध", "É": "द्व", "T": "ऊ", "S": "ए", "F": "इ", "G": "उ",
    "\u00a3": "ह्व",
}

#: Tried before a consonant body, longest first.
_UNITS = (
    ("°^", "ष्ट्र"), ("Ì[", "ड़"), ("Ì{", "ढ़"),
    ("heâ", "फ"), ("F&", "ई"),        # h+â is फ, while plain "he" is प
    ("Dees", "ओ"), ("Deew", "औ"), ("Dee", "आ"), ("De", "अ"),
    ("É", "द्व"), ("Ú", "छ"), ("{", "ढ"), ("š", "ट"),
    ("õ", "द्र"), ("™", "रू"),
)

#: Signs written after the body, longest first.
_SIGNS = (
    ("eW", "ों"), ("es", "ो"), ("er", "ी"), ("ew", "ौ"), ("e", "ा"),
    ("s", "े"), ("g", "ु"), ("t", "ू"), ("w", "ै"), ("W", "ें"),
    ("B", "ँ"), ("b", "ं"), ("=", "ृ"), ("Q", "ैं"), ("~", "।"),
    (":", "ः"), ("ä", HALANT), ("@", "ॉ"), ("Ç", "्र"), ("Ì", "़"),
    ("â", ""), ("&", "\x01"),          # \x01 is the reph, placed below
)

_MATRAS = frozenset("ािीुूृॄेैोौंँः़")


def _body(text, i):
    """One consonant cluster at *i*, as (unicode, next_index) or (None, i)."""
    ch = text[i:i + 1]
    if ch in _STEM:
        if text.startswith("e", i + 1):
            return _STEM[ch], i + 2
        return _STEM[ch] + HALANT, i + 1
    if ch in _WHOLE:
        return _WHOLE[ch], i + 1
    # Letters that live in the unit table, so a pre-posed ि still finds them.
    for unit, value in _UNITS:
        if not unit.startswith("De") and text.startswith(unit, i):
            return value, i + len(unit)
    return None, i


def _cluster(text, i):
    """A whole consonant cluster, so a pre-posed ि lands after all of it.

    "meefcceefuele" is सम्मिलित: the ि belongs after म्म, not inside it.
    """
    parts = []
    while True:
        body, j = _body(text, i)
        if body is None:
            break
        parts.append(body)
        i = j
        if not body.endswith(HALANT):
            break
    return ("".join(parts), i) if parts else (None, i)


def _apply_reph(text):
    """Move each reph to the front of the cluster it belongs to."""
    out = []
    for ch in text:
        if ch != "\x01":
            out.append(ch)
            continue
        j = len(out)
        while j > 0 and out[j - 1] in _MATRAS:
            j -= 1
        if j == 0:
            continue
        k = j - 1
        while k - 1 >= 1 and out[k - 1] == HALANT:
            k -= 2
        if k < 0:
            continue
        out[k:k] = ["र", HALANT]
    return "".join(out)


def _cleanup(text):
    text = text.replace("ाे", "ो").replace("ाै", "ौ")
    text = text.replace("ंे", "ें").replace("ंो", "ों")
    # A short i that landed on the first half of a conjunct.
    out = list(text)
    i = 0
    while i < len(out) - 2:
        if out[i] == "ि" and out[i + 1] == HALANT:
            out[i:i + 3] = [HALANT, out[i + 2], "ि"]
            i += 3
            continue
        i += 1
    return "".join(out)


def aps_to_unicode(text: str) -> str:
    """Convert APS-DV-Priyanka text to Devanagari Unicode."""
    if not text:
        return ""

    out = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("ef", i):            # pre-posed short i
            cluster, j = _cluster(text, i + 2)
            if cluster is not None:
                out.append(cluster + "ि")
                i = j
                continue

        for unit, value in _UNITS:
            # "Dee" must not swallow the "e" of a following "ef".
            if unit.startswith("De") and text.startswith(unit + "f", i):
                continue
            if text.startswith(unit, i):
                out.append(value)
                i += len(unit)
                break
        else:
            body, j = _body(text, i)
            if body is not None:
                out.append(body)
                i = j
                continue
            for sign, value in _SIGNS:
                if text.startswith(sign, i):
                    out.append(value)
                    i += len(sign)
                    break
            else:
                out.append(text[i])
                i += 1

    return _cleanup(_apply_reph("".join(out)))
