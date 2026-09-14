# Aakriti

Supported since 1.6.0, as the `aakriti` profile (alias `akruti`). Detected
automatically.

Anchored to the font. There is no public Aakriti converter to cross-check
against, so the whole mapping was read off `Aakriti.ttf` and every rule
confirmed by rendering it back.

## Structure

Aakriti is the simplest encoding in this toolkit, because it has **no stem
glyph at all**. Where APS uses `e`, Shree-Lipi uses `$` and Shusha uses `a`,
Aakriti just gives each letter two codes:

**Lowercase is the full letter, uppercase is its half form.**

| letter | full | half |
|---|---|---|
| क | `s` | `S` |
| न | `g` | `G` |
| व | `j` | `J` |
| प | `k` | `K` |
| म | `d` | `D` |

Letters with no dedicated half code take the explicit virama `\` instead, so
द् is `b\` and ट् is `6\`.

The retroflex row and a few others sit on the ASCII digits — `6` ट, `7` ठ,
`8` ड, `9` ढ, `0` ण, `5` छ, `3` घ, `1` ञ — and the Devanagari digits move to
the shifted number row, `!` through `)`. Those decode back to ASCII digits,
the convention the other profiles follow.

Matras: `f` ा, `l` ि (pre-posed), `L` ी, `'` ु, `"` ू, `[` ृ, `]` े,
`}` ै, `+` ं, `M` ः, `F` ँ. ो and ौ are `f]` and `f}`.

`{` is reph, written after the cluster it precedes, and `|` is rakar (्र).

## Verified

88 word pairs in `tests/corpus_aakriti.py`. Each was encoded from Unicode,
rendered in `Aakriti.ttf`, read back off the rendered page, and only then
recorded — so the corpus is anchored to what the font actually draws rather
than to anyone's description of the keyboard.

Two codes needed the font to settle:

- `+` is the anusvara, not `m`. `m` is an alternate ू.
- द् is `b\`, not `B`. `B` and `W` both draw ध्.

## Not covered

"Akruti" is a different family name from "Aakriti", and this profile has only
been checked against the Aakriti font. The `akruti` alias is accepted when you
select the profile by hand, but a font *named* Akruti is not treated as
supported by the automatic font check, because that has not been verified.
