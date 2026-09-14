# Shusha

Supported since 1.5.0, as the `shusha` profile (alias `susha`). Detected
automatically.

Anchored to the font. The mapping was read from `Shusha.ttf` and every rule
below was checked by rendering it, which is the same standard the KrutiDev,
Walkman, Chanakya and APS profiles are held to.

## Structure

`a` is the **vertical stem**. Most consonants are stored stem-less and `a`
completes them, which means the stem-less code doubles as the half form:

| code | letter | code | letter |
|---|---|---|---|
| `m` | म् | `ma` | म |
| `s` | स् | `sa` | स |
| `x` | क्ष् | `xa` | क्ष |

Letters that carry their own stem shape are stored whole — क `k`, ख `K`,
त `t`, द `d`, ट `T`, ठ `z`, ड `D`, ढ `Z`, प `p`, फ `f`, र `r`, ह `h`,
छ `C`, ळ `L`, ङ `=` — and take a dedicated half form (क् `@`, त् `%`,
प् `P`, ह् `*`) or an explicit virama `\` (ट् `T\`, द् `d\`, ख् `K\`).

Once a consonant is complete, a further `a` is the ा matra, `ao` is ो and
`aO` is ौ. Longest-match tokenising is what keeps these apart: म is `ma`, so
मो is `maao`; क is `k`, so को is `kao`.

`i` is the pre-posed ि, written before its cluster — किसी is `iksaI`, and
सम्मिलित is `saimmailat`, which carries two of them.

`-` is reph, written after the cluster it precedes, matras included: कर्म is
`kma-` and वर्गीकरण is `vagaI-krNa`.

`,` is the nukta, written after its letter (छोड़ is `CaoD,`). `` ` `` and `/`
are the two rakar forms.

## Where the font overruled a converter

The mapping was cross-checked against a third-party Unicode-to-Shusha
converter. Where the two disagreed the font decided, and it was right to:

- The converter renders दक्षिण as `daixaNa`. Rendered in Shusha that reads
  दाक्षिण, with a matra the word does not have. The correct encoding is
  `dixaNa`, which is what `tests/corpus_shusha.py` records.
- The converter also emitted a stray leading `-` for हा in one probe. `ha` is
  correct.

This is the reason the profile is anchored to the font rather than to a
converter: a converter can be wrong, and a rendered page cannot.

## Verified

201 word pairs in `tests/corpus_shusha.py`, and a round-trip over 1,099
characters of running Hindi at 99.4% character accuracy before the two
punctuation codes (`¸` comma, `Æ` question mark) were added, 100% after.
