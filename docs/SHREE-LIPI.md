# Shree-Lipi / Shree Dev

Supported since 1.4.0, as the `shreelipi` profile (alias `shreedev`). Detected
automatically.

Read this before relying on it: **the mapping has not yet been checked against
a Shree-Lipi PDF or the font file.** That is a real difference from the other
five profiles, and the section at the bottom says what it would take to close.

## Structure

Shree-Lipi stores a consonant as a bare code plus a **stem glyph**. Most
letters take `$`; the retroflex group (ङ छ ट ठ ड ढ) takes `>`. The stem always
trails the cluster, and a matra that sits on the letter body is written
*between* the letter and its stem:

| Unicode | Shree-Lipi | note |
|---|---|---|
| क | `H$` | letter + stem |
| कु | `Hw$` | matra inside the stem |
| का | `H$m` | ा is a full-width matra, so it follows the stem |
| ट | `Q>` | retroflex stem |
| टु | `Qw>` | |

Both stem glyphs are decoration and are dropped on the way in. This is the
same architecture as APS-DV-Priyanka, where code 101 `e` plays the part of `$`.

Every consonant also has a **dedicated half form** in the Latin-1 range —
क् `Š`, म् `å`, स् `ñ`, त् `Ë`. Letters without one take the generic virama
`²`, so ट् is `Q²>`.

`{` and `p` are the pre-posed ि, written before the cluster they belong to.
`p` is the variant used where the cluster opens with a half form: सम्मिलित is
`gpå_{bV`, with both forms in one word.

`©` is reph, written *after* the consonant it precedes, and it fuses with a
following matra into a single code:

| | plain | + reph |
|---|---|---|
| (none) | | `©` |
| ी | `r` | `u` |
| े | `o` | `}` |
| ै | `¡` | `£` |
| ं | `§` | `ª` |

So कर्म is `H$_©` and पदार्थों is `nXmWmoª`.

`µ` and `‹` are the nukta, written *before* their letter: क़ is `µH$`, ड़ is
`‹S>`.

The consonants otherwise run in ASCII order from `H` (क) through `i` (ळ),
with `c` unused and `G` holding ॠ.

## Collisions in the encoding

Three codes are genuinely ambiguous. The profile resolves each by frequency
and says so here rather than hiding it.

- **`–` is both ह्न and an en dash.** Read as the dash when flanked by
  whitespace, as the conjunct otherwise.
- **`–` is also ड्ढ.** ह्न wins. ड्ढ is rare in Hindi.
- **`~` is ब, and some producers also write a word-final virama with it.** ब
  wins: सब is a word and स्ब is not. A document that uses the other convention
  will show a stray ब where a trailing halant belongs.

## Shree-Lipi is a family, not one encoding

This is the most important thing on this page, and it was measured rather than
assumed. The SHREE726 font was compared code by code against the layout this
profile implements. Roughly two thirds agree -- क `H$`, म `_`, reph `©`,
स `g`, ह `h`, ष्ट्र `ï´>` and the matras all hold, and words built only from
those render correctly. But a substantial minority do not:

| code | this profile | SHREE726 |
|---|---|---|
| `a` | र | ष |
| `~` | ब | ग |
| `n` | प | ि |
| `C` | उ | श्र |
| `e` | श | र |
| `f` | ष | श |
| `l` | श्र | उ |
| `O` | ज | ढ |
| `Q` | ट | फ |
| `T` | ढ | ज |

So भारत, encoded `^maV` for the layout here, renders **भाषत** in SHREE726.

Modular InfoTech ships over 1,300 Devanagari faces under the Shree-Lipi name,
numbered 700, 701, 703, 708, 726 and onward. They are not interchangeable at
the byte level. The pipeline now warns whenever this profile is selected, and
the warning is not boilerplate: a document set in the wrong face converts to
plausible-looking but wrong Hindi, which is worse than not converting at all.

If you have a Shree-Lipi document, check a line of the output against the page
before trusting the rest.

## What has been verified, and what has not

186 word pairs in `tests/corpus_shreelipi.py` pass, and a separate round-trip
over 2,780 characters of running Hindi scores 98.9% at character level, with
the residue entirely Markdown and English contamination that the pipeline's
protection layer handles before conversion ever runs.

That measures the profile against the encoding as a converter implements it.
It does **not** measure it against a rendered Shree-Lipi page, which is the
standard the other five profiles are held to. Two things would close the gap:

1. A PDF set in Shree-Lipi, with a real text layer. A specimen catalogue does
   not do it -- those are page images, and show only what the faces look like.
2. The font file for the face the document uses. That is what settled Shusha
   and Aakriti, and what revealed the face problem above.

Until then, treat `shreelipi` output as needing a read-through, and check
which face the document names before believing the conversion.
