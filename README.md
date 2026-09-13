<div align="center">
  <img src="https://raw.githubusercontent.com/epicbharat/krutiextract/main/assets/logo.png" alt="KrutiExtract Logo" width="250"/>

  <h1>KrutiExtract</h1>
  <p><strong>Legacy Hindi PDF to Markdown</strong></p>

  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

<hr/>

Legacy Hindi fonts store Devanagari in 8-bit slots, so a PDF written in one of
them extracts as Latin gibberish. Worse, the usual extractors sort glyphs by
position, which scrambles matras: `vkSj` (और) is read as `vkjS` and converts to
the non-word आरै.

KrutiExtract reads the logical character stream instead of the visual order, so
the typist's keystrokes survive intact, then maps them to Unicode.

## Encodings

These are different fonts with conflicting rules, not dialects of one map.
Applying one profile's rules to another's document corrupts it, so the profile
is detected per document.

| Profile | Font | `=k` | `osQ` | `(` |
|---|---|---|---|---|
| `krutidev` (alias `devlys`) | KrutiDev 010, DevLys 010 | त्रा | वेफ | `;` |
| `walkman` (alias `ncert`) | Walkman-Chanakya 905 | त्र | के | `(` |
| `chanakya` | Chanakya | — | — | — |

Three more profiles convert nothing and are detected the same way:
`unicode` (already Devanagari), `hinglish` (Devanagari mixed with a lot of
Latin) and `english`. For these the protect/convert/restore cycle is skipped
entirely, so there is no way for it to damage the text.

Detection consults the PDF's own fonts first: if the body text is drawn in a
normal Latin font there is nothing to convert, whatever the characters look
like. Only then does it fall back to character statistics.

**NCERT Hindi textbooks use Walkman-Chanakya 905**, not KrutiDev. That is why
the older single-map approach produced वुफल for कुल and क्षेत्रापफल for
क्षेत्रफल: NCERT rules were being applied through a KrutiDev map.

Each profile is anchored to its font. The mapping tables were checked against
the KRDEV010 and DevLys-010 glyph tables and, for Walkman, against the font
embedded in an NCERT PDF plus the rendered pages of that same book.

## What is protected from conversion

Legacy maps claim ASCII punctuation as well as letters, so `.` becomes ण्, `|`
becomes द्य and `` ` `` is the ृ matra. Before conversion the following are
swapped out for opaque Private Use characters and restored afterwards:

- **Text the PDF drew in a Latin font.** The span's font name is direct
  evidence, matched in document order so that position disambiguates: in an
  NCERT book `(v)` is the Hindi letter अ while `(i)` is a Roman numeral.
- Markdown structure: headings, list bullets, table pipes and delimiter rows,
  emphasis markers, fenced code, HTML tags, link targets.
- URLs, e-mail addresses, decimals, percentages.
- English words, gated by both a dictionary and a character-bigram model. The
  dictionary alone is not enough in either direction: `thou` is the legacy
  spelling of जीवन, and `leaching` is a real gloss that a small corpus lacks.

## Install

```bash
pip install krutiextract
```

Image enhancement for scans is optional:

```bash
pip install "krutiextract[ocr]"
```

The English-word gate uses NLTK's Brown corpus. It downloads on first use; if
it cannot, conversion still works and falls back to font evidence:

```bash
python -c "import nltk; nltk.download('brown')"
```

OCR of image-only pages needs [Tesseract](https://github.com/tesseract-ocr/tesseract)
with the Hindi language pack, and a pymupdf4llm build that provides the layout
back end. `krutiextract` prints whether OCR is available at startup.

- Windows: run the installer, tick **Hindi**, add Tesseract to PATH.
- Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-hin`

## Usage

```bash
# one file; the encoding is detected and reported
krutiextract --input document.pdf --output document.md

# a whole tree
krutiextract --dir ./pdfs --out-dir ./markdown

# force a profile
krutiextract --input doc.pdf --profile walkman

# sharpen images first (needs the [ocr] extra)
krutiextract --input scan.pdf --enhance-ocr

# drop running headers
krutiextract --input doc.pdf --drop-pattern "^\s*Chapter \d+\s*$"

# raise OCR resolution (the biggest lever on OCR accuracy)
krutiextract --input scan.pdf --ocr-dpi 600
```

`--profile` accepts `auto` (default), `krutidev`, `devlys`, `walkman`, `ncert`,
`chanakya`, `unicode`, `hinglish`, `english`.

## Library

```python
from krutiextract import convert_pdf, walkman_to_unicode

markdown, profile, warnings = convert_pdf("jhss101.pdf")
walkman_to_unicode("{ks=k")        # 'क्षेत्र'
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The suite is a regression corpus: KrutiDev pairs anchored to the font's glyph
table, and Walkman pairs read off the rendered pages of an NCERT chapter.

## OCR quality

Measured, not asserted. A Hindi text column from an NCERT page was rendered at
several resolutions, degraded six ways, and OCR'd; the score is character error
rate against the converted text of that same block.

**Resolution dominates everything else.** At an effective 300 dpi Tesseract
reached about 0.5% CER on *every* degradation tested — low resolution, blur,
noise, heavy JPEG, an uneven wash. Below roughly 100 dpi the error rate jumps
to 18–27% and no pre-processing recovers it. So `--ocr-dpi` (default 400) is
the lever worth reaching for first.

`--enhance-ocr` is off by default and, when on, applies only what a
measurement of each image indicates:

| Condition | Action | Measured effect (75 dpi source) |
|---|---|---|
| uneven lighting or a smooth watermark | divide out the background | 0.042 → 0.011 |
| genuinely noisy | non-local-means denoise | 0.060 → 0.023 |
| small **and** sharp text | Lanczos upscale | 0.018 → 0.005 |
| skewed | rotate to the dominant text angle | — |

Overall it moved mean CER from 0.272 to 0.259 at a 75 dpi source, with no case
made worse. Three things it deliberately does **not** do, because each measured
worse: binarise before Tesseract (0.178 → 0.216 — modern LSTM Tesseract wants
grayscale and does its own thresholding), sharpen a blurred scan (0.702 →
0.724), and upscale a heavily JPEG-compressed image.

If your scans are poor, the order of attack is: raise `--ocr-dpi`, then rescan
at a higher resolution, then `--enhance-ocr`. The last one cannot put back
detail the scan never captured.

## Known limits

- **Three encodings are verified, not all of them.** KrutiDev 010, DevLys 010,
  Walkman-Chanakya 905 and Chanakya are anchored to their fonts and to a
  rendered book. Shree-Lipi, Shusha, APS, Akruti, ISM and the other KrutiDev
  variants are *not* covered and will not convert correctly. If you have a
  sample, open an issue: adding a profile is mechanical once the font is in
  hand.
- A legacy word is also a run of ASCII letters, so an isolated English word
  with no font evidence can be misread as Hindi, and vice versa. Font evidence
  resolves this whenever the source PDF has it; OCR output does not.
- Text recovered by OCR arrives as Unicode already and bypasses conversion.
- `krutidev` follows KRDEV010 exactly. If your document reads `osQ` as के, it
  is Walkman-Chanakya and will be detected as such.

## Contributing

If a PDF breaks the extraction, please open an issue and attach it. A sample
that uses a fourth encoding is especially useful.

## License

MIT. See [LICENSE](LICENSE).

---
**Author:** Bharat Choudhary
**Email:** epicbharat@gmail.com
**GitHub:** [https://github.com/epicbharat](https://github.com/epicbharat)
