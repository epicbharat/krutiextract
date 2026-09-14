"""Shree-Lipi (Shree Dev) 8-bit Devanagari -> Unicode.

Structure, read off the encoding rather than guessed:

* A consonant is stored as a bare code plus a **stem glyph** -- ``$`` for most
  letters, ``>`` for the retroflex group (ङ छ ट ठ ड ढ).  The stem always
  trails the cluster, and matras that sit on the letter body are written
  *between* the letter and its stem: क is ``H$`` but कु is ``Hw$``.  Both stem
  glyphs are decoration and are dropped on the way in.
* Every consonant also has a dedicated **half form** in the Latin-1 range
  (क् ``Š``, म् ``å``, स् ``ñ``).  Letters without one take the generic
  virama ``²``.
* ``{`` and ``p`` are the pre-posed ि, written before the cluster it belongs
  to.  ``p`` is the variant used where the cluster opens with a half form.
* ``©`` is reph, written *after* the consonant it precedes, and it fuses with
  a following matra into one code: ``u`` is ी + reph, ``}`` े + reph,
  ``£`` ै + reph, ``ª`` ं + reph.
* ``µ`` and ``‹`` are the nukta, written *before* their letter.

Known collisions in the encoding itself, resolved here by frequency:

* ``–`` is both ह्न and an en dash.  Read as the dash when it is flanked by
  whitespace, as the conjunct otherwise.
* ``–`` is also ड्ढ.  ह्न wins; ड्ढ is rare in Hindi.
* ``~`` is ब, and some producers also use it for a word-final virama.  ब
  wins -- स्ब is not a word, but सब is.

Not yet checked against a Shree-Lipi PDF or the font itself.  See
docs/SHREE-LIPI.md.
"""

from __future__ import annotations

import unicodedata

HALANT = "्"
NUKTA = "़"
REPH = "\x01"
PRE_I = "\x02"

_CONS = {
    "H": "क", "I": "ख", "J": "ग", "K": "घ", "L": "ङ", "M": "च", "N": "छ",
    "O": "ज", "P": "झ", "Q": "ट", "R": "ठ", "S": "ड", "T": "ढ", "U": "ण",
    "V": "त", "W": "थ", "X": "द", "Y": "ध", "Z": "न", "n": "प", "\\": "फ",
    "~": "ब", "^": "भ", "_": "म", "`": "य", "a": "र", "b": "ल", "d": "व",
    "e": "श", "f": "ष", "g": "स", "h": "ह", "i": "ळ",
}

_HALF = {
    "Š": "क", "»": "ख", "½": "ग", "¿": "घ", "À": "च", "Á": "ज", "Â": "झ",
    "Ä": "ञ", "Ê": "ण", "Ë": "त", "Ï": "थ", "Ü": "ध", "Ý": "न", "ß": "प",
    "â": "फ", "ã": "ब", "ä": "भ", "å": "म", "æ": "य", "ë": "ल", "ì": "व",
    "í": "श", "î": "ष", "ñ": "स", "ô": "ह", "ù": "ळ",
}

_UNITS = [
    ("Am°", "ऑ"), ("Am¡", "औ"), ("Amo", "ओ"), ("E°", "ऍ"), ("Äm", "ञ"),
    ("Am", "आ"), ("B©", "ई"), ("Eo", "ऐ"), ("D$", "ऊ"), ("F$", "ऋ"),
    ("A", "अ"), ("B", "इ"), ("C", "उ"), ("E", "ए"), ("G", "ॠ"),
    ("j", "क्ष"), ("k", "ज्ञ"), ("l", "श्र"), ("Ì", "त्र"), ("à", "प्र"),
    ("Ú", "द्य"), ("Û", "द्व"), ("Õ", "द्ध"), ("Ô", "द्द"), ("Ù", "द्म"),
    ("Ò", "द्ग"), ("×", "द्ब"), ("Ð", "द्र"), ("Ø", "द्भ"),
    ("÷", "ह्म"), ("ø", "ह्य"), ("õ", "ह्र"), ("ˆ", "ह्व"), ("‡", "ह्ल"),
    ("Å", "ट्ट"), ("Æ", "ट्ठ"), ("È", "ड्ड"), ("Þ", "न्न"), ("„", "ल्ल"),
    ("ï", "ष्ट"), ("ð", "ष्ठ"), ("œ", "श्व"), ("ü", "श्च"), ("”", "ङ्ग"),
    ("Îm", "त्त"), ("Î", "त्त्"), ("ƒ", "च्च"), ("¸", "क्क"), ("º", "क्त"),
    ("á", "प्त"), ("ý", "श्न"), ("ò", "स्र"),
    ("é", "रु"), ("ê", "रू"), ("ö", "हृ"), ("Ñ", "दृ"), ("›", "ॐ"),
    ("u", "ी" + REPH), ("}", "े" + REPH), ("£", "ै" + REPH), ("ª", "ं" + REPH),
]
_UNIT_MAP = dict(_UNITS)
_TOKENS = sorted(_UNIT_MAP, key=len, reverse=True)

_SIGNS = {
    "m": "ा", "r": "ी", "w": "ु", "y": "ू", "¥": "ृ", "o": "े", "¡": "ै",
    "§": "ं", "±": "ँ", "…": "ः", "°": "ॅ", "²": HALANT,
    "«": HALANT + "र", "´": HALANT + "र", "&": "।",
    "¢": "ैं", "t": "ीं", "|": "ें",
    "©": REPH, "{": PRE_I, "p": PRE_I,
}

_STEMS = "$>"
_NUKTA_BEFORE = "µ‹"
_EN_DASH = "–"

_FIX = (
    ("ाे", "ो"), ("ेा", "ो"),
    ("ाै", "ौ"), ("ैा", "ौ"),
    ("ाॅ", "ॉ"), ("ॅा", "ॉ"),
)


def _read_one(text: str, i: int) -> tuple[int, str]:
    for token in _TOKENS:
        if text.startswith(token, i):
            return i + len(token), _UNIT_MAP[token]
    ch = text[i]
    if ch == _EN_DASH:
        before = text[i - 1] if i else " "
        after = text[i + 1] if i + 1 < len(text) else " "
        if before.isspace() or after.isspace():
            return i + 1, _EN_DASH
        return i + 1, "ह" + HALANT + "न"
    if ch in _HALF:
        return i + 1, _HALF[ch] + HALANT
    if ch in _CONS:
        return i + 1, _CONS[ch]
    if ch in _SIGNS:
        return i + 1, _SIGNS[ch]
    return i + 1, ch


def _tokenise(text: str):
    i, n = 0, len(text)
    while i < n:
        if text[i] in _STEMS:
            i += 1
            continue
        if text[i] in _NUKTA_BEFORE:
            i += 1
            if i >= n:
                yield NUKTA
                break
            i, piece = _read_one(text, i)
            yield piece + NUKTA
            continue
        i, piece = _read_one(text, i)
        if REPH in piece and piece != REPH:
            yield piece.replace(REPH, "")
            yield REPH
        else:
            yield piece


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


def shreelipi_to_unicode(text: str) -> str:
    """Convert Shree-Lipi bytes to Unicode Devanagari."""
    converted = _reorder(list(_tokenise(text)))
    for old, new in _FIX:
        converted = converted.replace(old, new)
    return unicodedata.normalize("NFC", converted)
