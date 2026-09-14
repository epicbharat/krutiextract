"""Shusha 8-bit Devanagari -> Unicode.

Read off the font (``Shusha.ttf``) and checked against it by rendering.

Structure:

* ``a`` is the **vertical stem**.  Most consonants are stored stem-less, and
  ``a`` completes them: ``m`` is म् and ``ma`` is म.  So the stem-less code is
  also the half form, which is why Shusha needs no separate half-form table
  for those letters.
* Letters that carry their own stem shape are stored whole -- क ``k``, त ``t``,
  ट ``T``, द ``d``, प ``p``, ह ``h``, र ``r`` and the rest -- and take a
  dedicated half form instead (क् ``@``, त् ``%``, प् ``P``, ह् ``*``) or an
  explicit virama ``\\`` (ट् ``T\\``, ड् ``D\\``, द् ``d\\``).
* After a consonant is complete, a further ``a`` is the ा matra, ``ao`` is ो
  and ``aO`` is ौ.  Longest-match tokenising keeps these apart: म is ``ma`` so
  मो is ``maao``, while क is ``k`` so को is ``kao``.
* ``i`` is the pre-posed ि, written before its cluster.
* ``-`` is reph, written after the cluster it precedes, matras included:
  कर्म is ``kma-`` and वर्गीकरण is ``vagaI-krNa``.
* ``,`` is the nukta, written after its letter, and `````` and ``/`` are the
  two rakar forms.
"""

from __future__ import annotations

import unicodedata

HALANT = "्"
NUKTA = "़"
REPH = "\x01"
PRE_I = "\x02"

#: Stored stem-less; the bare code is the half form and code + "a" the letter.
_STEMLESS = {
    "g": "ग", "G": "घ", "c": "च", "j": "ज", "J": "झ", "H": "ञ", "N": "ण",
    "q": "थ", "Q": "ध", "n": "न", "b": "ब", "B": "भ", "m": "म", "y": "य",
    "l": "ल", "v": "व", "S": "श", "Y": "ष", "s": "स", "E": "श्र", "x": "क्ष",
}

#: Stored whole; these have their own stem shape.
_WHOLE = {
    "k": "क", "K": "ख", "T": "ट", "z": "ठ", "D": "ड", "Z": "ढ", "t": "त",
    "d": "द", "p": "प", "f": "फ", "r": "र", "h": "ह", "C": "छ", "L": "ळ",
    "=": "ङ",
}

#: Dedicated half forms for the whole-stored letters.
_HALF = {"@": "क", "%": "त", "P": "प", "*": "ह"}

_UNITS = [
    ("AaO", "औ"), ("Aao", "ओ"), ("Aa", "आ"), ("eo", "ऐ"),
    ("A", "अ"), ("[", "इ"), ("š", "ई"), ("]", "उ"), ("}", "ऊ"),
    ("?", "ऋ"), ("e", "ए"),
    ("~", "त्र"), ("&", "ज्ञ"), ("V", "द्य"), ("W", "द्व"),
    ("w", "द्ध"), ("_", "द्द"), ("<", "त्त्"), ("(", "ह्य"),
    ("œ", "ह्र"), ("+", "ट्ट"), (">", "क्त"), ("Ë", "क्र"),
    ("Ì", "कृ"), ("É", "रु"), ("$", "रू"), (")", "हृ"), ("!", "ॐ"),
    ("Ó", "ख" + NUKTA), ("Ô", "फ" + NUKTA),
]

_SIGNS = {
    "I": "ी", "u": "ु", "U": "ू", "R": "ृ", "o": "े", "O": "ै",
    "M": "ं", "Ð": "ँ", ":": "ः", ".": "।", ",": NUKTA,
    "\u00b8": ",", "\u00c6": "?",
    "\\": HALANT, "`": HALANT + "र", "/": HALANT + "र",
    "i": PRE_I, "-": REPH,
}

# Built once: "ao"/"aO" must beat a bare "a", and a stem-less letter ("ma")
# must beat its own half form ("m").
_TOKENS: dict[str, str] = {}
for _code, _letter in _STEMLESS.items():
    _TOKENS[_code + "a"] = _letter
    _TOKENS[_code] = _letter + HALANT
for _code, _letter in _WHOLE.items():
    _TOKENS[_code] = _letter
for _code, _letter in _HALF.items():
    _TOKENS[_code] = _letter + HALANT
for _code, _letter in _UNITS:
    _TOKENS[_code] = _letter
for _code, _letter in _SIGNS.items():
    _TOKENS[_code] = _letter
_TOKENS["ao"] = "ो"
_TOKENS["aO"] = "ौ"
_TOKENS["a"] = "ा"
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
            while j < n and pieces[j] in (HALANT + "र", NUKTA):
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


def shusha_to_unicode(text: str) -> str:
    """Convert Shusha bytes to Unicode Devanagari."""
    converted = _reorder(list(_tokenise(text)))
    for old, new in _FIX:
        converted = converted.replace(old, new)
    return unicodedata.normalize("NFC", converted)
