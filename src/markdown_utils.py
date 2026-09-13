# -*- coding: utf-8 -*-
"""Shield everything that is not legacy-encoded Hindi from the font converter.

The legacy KrutiDev/Devlys maps use ASCII letters AND ASCII punctuation, so a
naive conversion destroys Markdown structure, URLs, table pipes, decimals and
any embedded English. This module replaces those spans with opaque single
characters before conversion and puts them back afterwards.

Safe tokens are taken from Unicode Plane 15/16 Private Use Areas. That matters:
PUA code points have general category Co, so they are NOT word characters. A
CJK token (the previous choice) *is* a word character, which silently killed
every ``\\b`` boundary next to a token and left the adjacent English word
exposed to the converter.
"""

import math
import re
from typing import List, Optional, Tuple

from .legacy_profile import LEGACY_BIGRAMS, LEGACY_TOTAL

__all__ = [
    "protect_non_hindi_syntax",
    "restore_non_hindi_syntax",
    "is_english_word",
    "is_marker",
    "MarkerOverflow",
]

# --------------------------------------------------------------------------
# English vocabulary (used only to decide whether an ASCII run is English)
# --------------------------------------------------------------------------

_SHORT_WORDS = {
    "the", "and", "for", "of", "to", "in", "is", "it", "on", "as", "at",
    "by", "an", "be", "or", "we", "am", "pm", "no", "vs",
}

_english_vocab = None


def _vocab() -> set:
    """Load the Brown corpus once, tolerating a missing/undownloadable corpus."""
    global _english_vocab
    if _english_vocab is None:
        try:
            import nltk
            try:
                nltk.data.find("corpora/brown")
            except LookupError:
                nltk.download("brown", quiet=True)
            from nltk.corpus import brown
            # Brown (~40k types) rather than `words` (~236k): the big list
            # contains obscure entries that collide with valid legacy strings.
            _english_vocab = {w.lower() for w in brown.words() if w.isalpha()}
        except Exception:
            _english_vocab = set()
    return _english_vocab


# --------------------------------------------------------------------------
# English vs legacy discrimination by character bigrams
# --------------------------------------------------------------------------
#
# A legacy word is a run of ASCII letters, so a dictionary is not sufficient in
# either direction: "thou" is the legacy spelling of जीवन, and "leaching" is a
# real English gloss that a small corpus does not contain. Scoring a token
# against an English bigram model and a legacy bigram model separates them.

_ENGLISH_BIGRAMS = None
_ENGLISH_TOTAL = 0


def _english_bigrams():
    global _ENGLISH_BIGRAMS, _ENGLISH_TOTAL
    if _ENGLISH_BIGRAMS is None:
        counts = {}
        for w in _vocab() or ():
            t = "^" + w + "$"
            for i in range(len(t) - 1):
                b = t[i:i + 2]
                counts[b] = counts.get(b, 0) + 1
        _ENGLISH_BIGRAMS = counts
        _ENGLISH_TOTAL = sum(counts.values())
    return _ENGLISH_BIGRAMS, _ENGLISH_TOTAL


def english_score(word: str) -> float:
    """Log-odds per character that *word* is English rather than legacy.

    Positive favours English. Roughly: real English words score above +1,
    legacy strings below 0.
    """
    eng, eng_total = _english_bigrams()
    if not eng_total:
        return 0.0
    ev, lv = len(eng) + 1, len(LEGACY_BIGRAMS) + 1
    t = "^" + word.lower() + "$"
    total = 0.0
    for i in range(len(t) - 1):
        b = t[i:i + 2]
        pe = (eng.get(b, 0) + 0.5) / (eng_total + 0.5 * ev)
        pl = (LEGACY_BIGRAMS.get(b, 0) + 0.5) / (LEGACY_TOTAL + 0.5 * lv)
        total += math.log(pe) - math.log(pl)
    return total / max(1, len(word))


def is_english_word(word: str) -> bool:
    if not word:
        return False
    lower = word.lower()
    if len(word) < 4:
        return lower in _SHORT_WORDS
    return lower in _vocab()


# --------------------------------------------------------------------------
# Safe tokens
# --------------------------------------------------------------------------

_PLANE15 = 0xF0000          # 65534 usable code points
_PLANE16 = 0x100000         # 65534 more
_PLANE_SIZE = 0xFFFE
MAX_MARKERS = _PLANE_SIZE * 2


class MarkerOverflow(RuntimeError):
    """Raised when a document needs more safe tokens than the PUA provides."""


def _marker(idx: int) -> str:
    if idx < _PLANE_SIZE:
        return chr(_PLANE15 + idx)
    if idx < MAX_MARKERS:
        return chr(_PLANE16 + idx - _PLANE_SIZE)
    raise MarkerOverflow(
        f"document needs more than {MAX_MARKERS} protected spans; "
        "split the input or raise the marker budget"
    )


def is_marker(ch: str) -> bool:
    """True if *ch* is one of our opaque safe tokens."""
    if not ch:
        return False
    cp = ord(ch)
    return (_PLANE15 <= cp < _PLANE15 + _PLANE_SIZE) or (
        _PLANE16 <= cp < _PLANE16 + _PLANE_SIZE
    )


_MARKER_RE = re.compile(r"[\U000F0000-\U000FFFFD\U00100000-\U0010FFFD]")


# --------------------------------------------------------------------------
# Protection passes, in order. Earlier passes win.
# --------------------------------------------------------------------------

_URL_RE = re.compile(
    r"""(?xi)
    \b(?:https?://|www\.|ftp://)[^\s<>"'\)\]]+
    | \b[\w.+-]+@[\w-]+\.[\w.-]+\b
    """
)


def protect_non_hindi_syntax(
    raw_text: str,
    latin_terms: Optional[set] = None,
    latin_spans: Optional[List[str]] = None,
) -> Tuple[str, List[str]]:
    """Return (protected_text, preserved_spans).

    Everything that must survive the legacy font conversion byte-for-byte is
    swapped out for an opaque PUA character.

    *latin_terms* is the set of words the source PDF drew in a non-legacy
    font (see pdf_spans.latin_terms). That is direct evidence from the
    document and outranks every heuristic below, so it is applied first.
    """
    preserved: List[str] = []

    def keep(text: str) -> str:
        preserved.append(text)
        return _marker(len(preserved) - 1)

    def keep_match(m: "re.Match") -> str:
        return keep(m.group(0))

    text = raw_text

    # 0. Runs the PDF itself drew in a Latin font, matched in document order so
    #    that position disambiguates. Ground truth, so it goes first.
    if latin_spans:
        pieces, cursor = [], 0
        for span in latin_spans:
            probe = re.compile(
                r"(?<![A-Za-z0-9])" + re.escape(span) + r"(?![A-Za-z0-9])")
            m = probe.search(text, cursor)
            if m is None:
                continue
            pieces.append(text[cursor:m.start()])
            pieces.append(keep(m.group(0)))
            cursor = m.end()
        pieces.append(text[cursor:])
        text = "".join(pieces)

    if latin_terms:
        ordered = sorted((t for t in latin_terms if t), key=len, reverse=True)
        pattern = "|".join(re.escape(t) for t in ordered)
        text = re.sub(
            rf"(?<![A-Za-z0-9])(?:{pattern})(?![A-Za-z0-9])", keep_match, text)

    # 1. Fenced code blocks, then inline code. Nothing inside is Hindi.
    text = re.sub(r"(?s)```.*?```", keep_match, text)
    text = re.sub(r"(?s)~~~.*?~~~", keep_match, text)
    # No single-backtick inline-code rule: '`' is the ृ matra in every legacy
    # map, so two of them in a paragraph would protect all the Hindi between.

    # 2. Images and links. For links keep the text convertible: shield only the
    #    opening bracket and the "](target)" tail.
    text = re.sub(r"!\[[^\]\n]*\]\([^)\n]*\)", keep_match, text)

    def keep_link(m: "re.Match") -> str:
        return keep("[") + m.group(1) + keep("](" + m.group(2) + ")")

    text = re.sub(r"\[([^\]\n]*)\]\(([^)\n]*)\)", keep_link, text)

    # 3. Bare URLs and e-mail addresses.
    text = _URL_RE.sub(keep_match, text)

    # 4. HTML tags (bounded so a legacy '<' is not swallowed).
    text = re.sub(r"<[^>\n]{1,80}>", keep_match, text)

    # 5. Block structure at start of line: headings, list bullets, block
    #    quotes, horizontal rules. '-', '*', '>' and '#' all carry legacy
    #    meanings, so they must be shielded before conversion.
    text = re.sub(r"(?m)^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", keep_match, text)
    text = re.sub(r"(?m)^(#{1,6}\s+)", keep_match, text)
    text = re.sub(
        r"(?m)^(\s*)([-*+]\s+|\d+\.\s+|>\s+)",
        lambda m: m.group(1) + keep(m.group(2)),
        text,
    )

    # 6. Table structure. A delimiter row (|---|:--:|) is shielded whole,
    #    because '-' maps to '.' in the legacy maps; other rows keep their
    #    pipes shielded but leave the cell text convertible.
    text = re.sub(r"(?m)^(?=[^\n]*\|)[ \t|:\-]+$", keep_match, text)

    def keep_table_line(m: "re.Match") -> str:
        return m.group(0).replace("|", keep("|"))

    # Only a genuine Markdown table row: starts and ends with a pipe and has at
    # least two. A single '|' inside a line is the legacy code for द्य -- e.g.
    # "izkS|ksfxdh" (प्रौद्योगिकी) -- and must stay convertible.
    text = re.sub(r"(?m)^[ \t]*\|.*\|[ \t]*$", keep_table_line, text)

    # 7. Emphasis markers.
    text = re.sub(r"\*\*", keep_match, text)

    def keep_italics(m: "re.Match") -> str:
        return f"{m.group(1)}{keep('_')}{m.group(2)}{keep('_')}{m.group(3)}"

    _EDGE = r"[\U000F0000-\U000FFFFD\U00100000-\U0010FFFD]"
    text = re.sub(
        rf"(^|\s|{_EDGE})_(.+?)_(\s|$|[.,?!\-\]]|{_EDGE})", keep_italics, text)

    # 8. Numbers with internal punctuation, percentages, and ranges. '.' maps to
    #    'ण्' and ':' to 'रू' in the legacy maps, so decimals must be shielded.
    text = re.sub(r"\d+(?:[.,:/]\d+)+\s*%?", keep_match, text)
    text = re.sub(r"\d+\s*%", keep_match, text)
    # "1." in a numbered item that markdown wrapped in emphasis, so it never
    # reached the start-of-line rule above. '.' is ण् in every legacy map.
    text = re.sub(r"(?<=\d)\.(?![0-9])", lambda m: keep("."), text)

    # No bracket rule here. "(" and ")" are profile-dependent -- Walkman keeps
    # them as punctuation, KrutiDev assigns them letters -- so the converter's
    # map decides, and the text inside parentheses stays convertible.

    # 10. Isolated English words, acronyms and plain numbers. Lookarounds, not
    #     \b: a neighbouring safe token must not suppress the match.
    # A legacy word is also a run of ASCII letters, so some of them are real
    # English words: "thou" is the legacy spelling of जीवन. Dictionary
    # membership alone is therefore not enough. An isolated lowercase hit
    # surrounded by legacy text is treated as legacy; English wins when it is
    # capitalised, an acronym, numeric, or part of a run of English tokens.
    token_re = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{2,}(?![A-Za-z0-9])")
    tokens = list(token_re.finditer(text))

    def _dictionary_hit(w: str) -> bool:
        collapsed = re.sub(r"(.)\1+", r"\1", w)
        return is_english_word(w) or (len(collapsed) >= 4 and is_english_word(collapsed))

    def _strong(w: str) -> bool:
        """English beyond reasonable doubt, whatever the neighbours say."""
        if w.isdigit():
            return True
        if len(w) >= 4 and w.isupper() and w.isalpha():
            return True
        return bool(w[:1].isupper() and _dictionary_hit(w))

    def _in_parens(m: "re.Match") -> bool:
        before = text[max(0, m.start() - 1):m.start()]
        after = text[m.end():m.end() + 1]
        return before == "(" and after == ")"

    def _formula_paren(m: "re.Match") -> bool:
        """Inside parentheses that hold a digit and only a few letters."""
        open_i = text.rfind("(", max(0, m.start() - 40), m.start())
        if open_i < 0:
            return False
        close_i = text.find(")", m.end(), m.end() + 40)
        if close_i < 0:
            return False
        inner = text[open_i + 1:close_i]
        if "\n" in inner or not re.search(r"\d", inner):
            return False
        return len(re.findall(r"[A-Za-z]", inner)) <= 4

    hits = [_dictionary_hit(m.group(0)) for m in tokens]
    strong = [_strong(m.group(0)) for m in tokens]
    scores = [english_score(m.group(0)) for m in tokens]

    protect_flags = []
    for i, m in enumerate(tokens):
        w = m.group(0)
        if strong[i]:
            protect_flags.append(True)
            continue
        if hits[i]:
            # In the dictionary, but "thou" is also legacy for जीवन. Require
            # the bigram model to agree, or an English word right next to it.
            # Two- and three-letter hits never qualify on the score alone:
            # "aM" in ",aM" (ऐंड) scores like the English word "am".
            if len(w) >= 4 and scores[i] > 0.5:
                protect_flags.append(True)
                continue
            near = False
            for j in (i - 1, i + 1):
                if 0 <= j < len(tokens) and (hits[j] or strong[j]):
                    gap = text[min(tokens[i].end(), tokens[j].end()):
                               max(tokens[i].start(), tokens[j].start())]
                    if len(gap) <= 3:
                        near = True
                        break
            protect_flags.append(near)
            continue
        # Not in the dictionary. A parenthesised gloss that looks strongly
        # English is still English: "(leaching)", "(pH<6.0)".
        if _in_parens(m) and scores[i] > 1.0:
            protect_flags.append(True)
            continue
        if _formula_paren(m):
            protect_flags.append(True)
            continue
        protect_flags.append(False)

    pieces = []
    last = 0
    for m, flag in zip(tokens, protect_flags):
        pieces.append(text[last:m.start()])
        pieces.append(keep(m.group(0)) if flag else m.group(0))
        last = m.end()
    pieces.append(text[last:])
    text = "".join(pieces)

    # 11. A full stop or colon hanging off a protected English span belongs to
    #     that span, not to Hindi ('.' -> 'ण्', ':' -> 'रू').
    text = re.sub(
        r"(?<=[\U000F0000-\U000FFFFD\U00100000-\U0010FFFD])([.:])(?=\s|$)",
        lambda m: keep(m.group(1)), text)

    return text, preserved


def restore_non_hindi_syntax(text: str, preserved: List[str]) -> str:
    """Put every preserved span back. Reverse order handles nesting."""
    for i in range(len(preserved) - 1, -1, -1):
        text = text.replace(_marker(i), preserved[i])
    # Defensive: drop any token that outlived its span, plus legacy $$$n$$$.
    text = _MARKER_RE.sub("", text)
    text = re.sub(r"\$\$\$\d+\$\$\$", "", text)
    return text
