# -*- coding: utf-8 -*-
"""Chanakya -> Devanagari Unicode.

Shares the structural passes with converter.py. The original had its own copy
of the reph and short-i loops, carrying the same three defects: a marker at
index 0 aborted the pass, edits were applied with a global str.replace while a
stale index kept walking, and the matra set was a space-separated string so a
space counted as a matra.
"""

from .chanakya_map import array_one, array_two

__all__ = ["chanakya_to_unicode"]


def chanakya_to_unicode(text: str) -> str:
    if not text:
        return ""

    # Imported here to avoid a circular import at module load.
    from .converter import _CLEANUP, _apply_reph, _apply_short_i, _repair_matra_halant

    s = text
    for a, b in zip(array_one, array_two):
        if a:
            s = s.replace(a, b)

    s = s.replace("Z", "üं")          # Z -> reph marker + anusvara

    s = _apply_short_i(s, "ç")            # ç is the pre-posed short-i
    s = _repair_matra_halant(s)
    s = _apply_reph(s, trigger="ü")       # ü is the reph marker

    for a, b in _CLEANUP:
        s = s.replace(a, b)
    return s
