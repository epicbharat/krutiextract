# APS-DV-Priyanka

Supported since 1.3.0, as the `aps` profile (alias `priyanka`). Detected
automatically.

Measured against the 336-page compilation it was derived from: every pair in
`tests/corpus_aps.py`, and **0.235% unmapped characters across 140 held-out
pages** (892 of 379,834). What remains is a handful of rare conjuncts.

## What is established

The font is **APS-DV-Priyanka** (and `APS-DV-PriyankaRoman`), used by several
North Indian exam-guide publishers. It is a legacy 8-bit Devanagari font whose
bytes surface as Latin text, but it shares nothing with KrutiDev, Walkman or
Chanakya — none of those maps produce anything sensible from it.

The PDF offers no shortcut: the embedded subsets carry a symbolic cmap with
`uniF0xx` glyph names, and the `/ToUnicode` map only restates the byte values
as Latin characters. There is no `/Differences` array with meaningful names.
The mapping has to be read off the glyphs.

## Structure observed

Consonants are digraphs ending in `e`: `ce` म, `ve` न, `me` स, `le` त,
`ye` ब, `Ye` भ, `Je` व, `Oe` ध, `ie` ग, `ne` ह, `pe` ज, `Ùe` य, `ue` ल.

The क-family takes a trailing killer `â`, with any left- or above-matra typed
*inside* the body, exactly as KrutiDev pre-poses ि:

| typed | renders |
|---|---|
| `keâ` | क |
| `kesâ` | के |
| `keâe` | का |
| `keâes` | को |

`ef` is the pre-posed short-i, `B` is ँ, `b` is ं, `~` is ।, `g` is ु,
`t` is ू, `er` is ी, `w` is ै, `=` is ृ. Conjuncts seen so far: `æ` द्ध,
`É` द्व, `Õe` श्व, `°^` ष्ट्र, `Ø` प्र.

The rule that resolves it: **code 101 `e` is the vertical stem.** A consonant
is stored stem-less and `e` completes it; where the letter already carries its
own stem (र, ह, द, ट, ड, ढ, छ) a following `e` is the ा matra instead. So
`jne~` is रहा। (र + ह + ा) and `Deeboesueve` is आंदोलन, where `ve` is one
letter. `W` is ें, and ों falls out of `e` + `W` through the same `ाे` -> `ो`
cleanup the other profiles use.

## Verified corpus

Read off the rendered page 65 of an IASPCS Mains compilation. Any candidate
map must reproduce all of these before it ships.

| typed | renders |
|---|---|
| `ØeLece` | प्रथम |
| `efJeÕe` | विश्व |
| `Ùegæ` | युद्ध |
| `kesâ` | के |
| `yeeo` | बाद |
| `cepeotjeW` | मजदूरों |
| `DeeboesueveeW` | आंदोलनों |
| `ceW` | में |
| `DeeÙeer` | आयी |
| `lespeer` | तेजी |
| `keâe` | का |
| `otmeje` | दूसरा |
| `keâejCe` | कारण |
| `YeejleerÙe` | भारतीय |
| `je°^erÙe` | राष्ट्रीय |
| `Deeboesueve` | आंदोलन |
| `ieeBOeerJeeoer` | गाँधीवादी |
| `Ùegie` | युग |
| `Deeieceve` | आगमन |
| `jne~` | रहा। |
| `ieeBOeerpeer` | गाँधीजी |
| `ves` | ने |
| `Deheves` | अपने |
| `DeeOeej` | आधार |
| `keâes` | को |
| `keâjves` | करने |
| `ØeÙelve` | प्रयत्न |
| `efkeâÙee~` | किया। |
| `cepeotj` | मजदूर |
| `Deewj` | और |
| `Ùener` | यही |
| `nw` | है |
| `Éeje` | द्वारा |
| `ieS` | गए |
| `ØecegKe` | प्रमुख |
| `Yeejle` | भारत |
| `keâer` | की |
| `yengle` | बहुत |
| `Lee` | था |
| `efkeâ` | कि |
| `mes` | से |
| `leLee` | तथा |
| `Skeâ` | एक |
| `hej` | पर |
| `Ùen` | यह |
| `nes` | हो |
| `veeje` | नारा |
| `efoÙee` | दिया |
| `nce` | हम |
| `keân` | कह |
| `Øekeâej` | प्रकार |
| `efueS` | लिए |
| `Yeer` | भी |
| `Oegjer` | धुरी |
| `Deesj` | ओर |
| `oyeeJe` | दबाव |
| `mebmeej` | संसार |
| `efceue` | मिल |
| `Yetefcekeâe` | भूमिका |

## Method

`tools/glyph_sheet.py` crops every distinct code point and every word from a
real page, so the mapping is read from the document rather than guessed. The
decisive step here was rendering the font file itself at a legible size: the
stem rule was invisible in the extracted text and obvious in the glyphs.

The same route works for any new encoding. Read the glyphs, build a corpus of
word pairs from a rendered page, fit a map against it, then measure the
unmapped residue on pages the map was not fitted to.
