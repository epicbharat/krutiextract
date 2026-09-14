"""Aakriti 8-bit Devanagari -> Unicode.

Read off the font (``Aakriti.ttf``) and checked against it by rendering.

Aakriti is the simplest of the legacy encodings this toolkit covers, because
it has no stem glyph at all:

* **Lowercase is the full letter, uppercase is its half form.** ``s`` is क and
  ``S`` is क्; ``g`` is न and ``G`` is न्; ``j`` is व and ``J`` is व्. Letters
  with no dedicated half code take the explicit virama ``\\`` instead, so द्
  is ``b\\`` and ट् is ``6\\``.
* The retroflex row and a few others sit on the ASCII digits: ``6`` ट,
  ``7`` ठ, ``8`` ड, ``9`` ढ, ``0`` ण, ``5`` छ, ``3`` घ, ``1`` ञ.
* Devanagari digits are on the shifted number row instead -- ``!`` is 1,
  ``@`` 2, ``#`` 3 and so on -- and decode back to ASCII digits, the same
  convention the other profiles follow.
* ``l`` is the pre-posed ि, written before its cluster, and ``{`` is reph,
  written after the cluster it precedes.
* ``|`` is rakar (्र) and ``\\`` the explicit virama.

Checked by rendering: ``ef/t`` is भारत, ``ls;L`` किसी, ``sd{`` कर्म,
``d]+`` में, ``k|s[lt`` प्रकृति and ``;\\jt+t|`` स्वतंत्र.
"""

from __future__ import annotations

import unicodedata

HALANT = "्"
REPH = "\x01"
PRE_I = "\x02"

#: Lowercase and digit codes: the full letter.
_FULL = {
    "s": "क", "v": "ख", "u": "ग", "3": "घ", "r": "च", "5": "छ", "h": "ज",
    "1": "ञ", "6": "ट", "7": "ठ", "8": "ड", "9": "ढ", "0": "ण", "t": "त",
    "y": "थ", "b": "द", "w": "ध", "g": "न", "k": "प", "a": "ब", "e": "भ",
    "d": "म", "o": "य", "/": "र", "n": "ल", "j": "व", "z": "श", "i": "ष",
    ";": "स", "x": "ह",
}

#: Uppercase codes: the half form of the matching lowercase letter.
_HALF = {
    "S": "क", "V": "ख", "U": "ग", "R": "च", "H": "ज", "T": "त", "Y": "थ",
    "W": "ध", "B": "ध", "G": "न", "K": "प", "A": "ब", "E": "भ", "D": "म",
    "N": "ल", "J": "व", "Z": "श", "I": "ष", "X": "ह", "Q": "त",
}

_UNITS = [
    ("cf}", "औ"), ("cf]", "ओ"), ("cf", "आ"), ("c", "अ"),
    ("O", "इ"), ("p", "उ"), ("P", "ए"), ("C", "ऋ"),
    ("q", "त्र"), (">", "श्र"), ("4", "द्ध"), ("?", "रु"),
    ("\u00bf", "\u0930\u0942"), ("\u02c6", "\u092b"),
    ("\uf000", "\u092b"), ("\u02dc", "\u0933"), ("\u00a7", "\u0919"),
    ("\u220f", "\u090a"), ("\u02e7", "\u0950"),
]
_UNIT_MAP = dict(_UNITS)

_SIGNS = {
    "f": "ा", "L": "ी", "'": "ु", '"': "ू", "m": "ू", "[": "ृ",
    "]": "े", "}": "ै", "+": "ं", "M": "ः", "F": "ँ",
    "l": PRE_I, "{": REPH, "|": HALANT + "र", "\\": HALANT,
    ".": "।", "=": ".", ",": ",",
}

#: Devanagari digits live on the shifted number row.
_DIGITS = dict(zip("!@#$%^&*()", "1234567890"))

_TOKENS: dict[str, str] = {}
for _c, _v in _UNITS:
    _TOKENS[_c] = _v
for _c, _v in _FULL.items():
    _TOKENS.setdefault(_c, _v)
for _c, _v in _HALF.items():
    _TOKENS.setdefault(_c, _v + HALANT)
for _c, _v in _SIGNS.items():
    _TOKENS.setdefault(_c, _v)
for _c, _v in _DIGITS.items():
    _TOKENS.setdefault(_c, _v)
_ORDER = sorted(_TOKENS, key=len, reverse=True)

_FIX = (("ाे", "ो"), ("ाै", "ौ"))


def _tokenise(text: str):
    i, n = 0, len(text)
    while i < n:
        for token in _ORDER:
            if text.startswith(token, i):
                yield _TOKENS[token]
                i += len(token)
                break
        else:
            yield text[i]
            i += 1


def _is_half(piece: str) -> bool:
    return len(piece) > 1 and piece.endswith(HALANT)


def _is_sign(piece: str) -> bool:
    return bool(piece) and all(
        unicodedata.category(c) in ("Mn", "Mc") for c in piece
    )


def _reorder(pieces: list[str]) -> str:
    out: list[str] = []
    i, n = 0, len(pieces)
    while i < n:
        piece = pieces[i]
        if piece == PRE_I:
            j = i + 1
            while j < n and _is_half(pieces[j]):
                out.append(pieces[j])
                j += 1
            if j < n and pieces[j] not in (PRE_I, REPH):
                out.append(pieces[j])
                j += 1
            while j < n and pieces[j] == HALANT + "र":
                out.append(pieces[j])
                j += 1
            out.append("ि")
            i = j
        elif piece == REPH:
            k = len(out)
            while k > 0 and _is_sign(out[k - 1]):
                k -= 1
            if k > 0:
                k -= 1
            while k > 0 and _is_half(out[k - 1]):
                k -= 1
            out.insert(k, "र" + HALANT)
            i += 1
        else:
            out.append(piece)
            i += 1
    return "".join(out)


def aakriti_to_unicode(text: str) -> str:
    """Convert Aakriti bytes to Unicode Devanagari."""
    converted = _reorder(list(_tokenise(text)))
    for old, new in _FIX:
        converted = converted.replace(old, new)
    return unicodedata.normalize("NFC", converted)
