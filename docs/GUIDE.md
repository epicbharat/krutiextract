# KrutiExtract — How-To Guide

A practical walkthrough: getting a legacy Hindi PDF out as clean Markdown,
knowing when the result is trustworthy, and what to do when it is not.

- [1. Install](#1-install)
- [2. First conversion](#2-first-conversion)
- [3. Understanding encodings](#3-understanding-encodings)
- [4. Batch work](#4-batch-work)
- [5. Scanned PDFs and OCR](#5-scanned-pdfs-and-ocr)
- [6. Checking the output](#6-checking-the-output)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Using it as a library](#8-using-it-as-a-library)
- [9. Adding a new encoding](#9-adding-a-new-encoding)

---

## 1. Install

```bash
pip install krutiextract
```

For scanned documents, add the optional image dependencies:

```bash
pip install "krutiextract[ocr]"
```

Two external pieces are needed only for scans:

| Piece | Why | Windows | Linux |
|---|---|---|---|
| Tesseract + Hindi pack | reads text out of page images | installer, tick **Hindi**, add to PATH | `sudo apt install tesseract-ocr tesseract-ocr-hin` |
| NLTK Brown corpus | helps tell English words from legacy ones | `python -c "import nltk; nltk.download('brown')"` | same |

Neither is required for a PDF that already has a text layer, which is most
typeset books. Run `krutiextract --version` and the banner reports whether OCR
is available.

---

## 2. First conversion

```bash
krutiextract --input "chapter1.pdf" --output "chapter1.md"
```

```
[1/1] chapter1.pdf
      saved   chapter1.md
      encoding walkman   chars 26,002   took 18.3s
```

The `encoding` line is the important one. It names the legacy font profile the
tool decided on. If that value looks wrong, everything downstream will be
wrong, so check it before reading the output.

Omit `--output` and the Markdown lands beside the PDF with the same stem.

---

## 3. Understanding encodings

Legacy Hindi fonts put Devanagari into 8-bit slots meant for Latin letters.
Different fonts made different choices, and those choices contradict each
other. The same bytes mean different words:

| Typed | KrutiDev 010 | Walkman-Chanakya 905 |
|---|---|---|
| `=k` | त्रा | त्र |
| `osQ` | वेफ | के |
| `¼` | ( | द्ध |
| `/` | ध् | ध |

**NCERT Hindi textbooks use Walkman-Chanakya 905.** This is the single most
common source of confusion, because the text looks like KrutiDev and is
usually described as KrutiDev.

Detection runs in this order:

1. **Devanagari dominance.** More Devanagari than Latin means the document is
   already Unicode; nothing is converted, whatever stray legacy sequences it
   quotes.
2. **Two-key signatures.** Sequences like `osQ`, `oqQ`, `iQ` and `mQ` are
   meaningless under KrutiDev — they would spell वेफ, वुफ, पफ, उफ — so their
   presence is decisive for Walkman-Chanakya.
3. **Signature density.** Whole-token matches such as `ds`, `dh`, `esa`, `ls`
   against the Latin token count. Real legacy documents measure 0.09 to 0.17;
   English prose and unsupported encodings measure 0.00.
4. **Script census.** Whatever is left is `unicode`, `hinglish` or `english`.

The PDF's fonts inform two other things but never decide the profile: which
spans are Latin and must be protected, and whether to warn that the body font
is a legacy encoding with no mapping in this build. A legacy font under a
custom name is common — one book used "Rajpurohit" — so the font name is not
trusted to rule conversion out.

Override it only when you know better:

```bash
krutiextract --input doc.pdf --profile krutidev
```

| Profile | Use for |
|---|---|
| `auto` | default; decides per document |
| `krutidev`, `devlys` | KrutiDev 010 / DevLys 010 |
| `walkman`, `ncert` | Walkman-Chanakya 905, including NCERT textbooks |
| `chanakya` | Chanakya |
| `unicode` | already Devanagari; copied through untouched |
| `hinglish` | Devanagari mixed with a lot of Latin |
| `english` | no Hindi at all |

The last three convert nothing, and "nothing" is meant literally: the output
is byte-identical to what the extractor produced. No repair pass, no
normalisation, no cleanup beyond removing HTML comment scaffolding and any
`--drop-pattern` lines you asked for. Forcing one of these is the safe way to
extract a PDF you do not want touched.

A document that is already Unicode Devanagari is detected as `unicode`
automatically, including text recovered by OCR, and a Hindi document that
merely quotes legacy sequences as examples is not converted either. If such a
document still looks wrong, the problem is upstream in the PDF or the
extractor, not in conversion — compare against `pymupdf4llm` output directly
to confirm.

---

## 4. Batch work

```bash
krutiextract --dir "NCERT/Class10/Hindi" --out-dir "markdown/Class10"
```

Subfolders are mirrored into the output directory. Files ending `.PDF` are
picked up as well as `.pdf`. One failure does not stop the run:

```
[1/3] ch01.pdf
      saved   markdown/Class10/ch01.md
      encoding walkman   chars 26,002   took 18.3s
[2/3] ch02.pdf
      failed  ch02.pdf: password protected
[3/3] ch03.pdf
      saved   markdown/Class10/sub/ch03.md

3 files   2 converted   1 failed   41.2s
```

The exit code is 1 if anything failed, so this works in a script:

```bash
krutiextract --dir books --out-dir out || echo "some files need attention"
```

Textbooks repeat a header or footer on every page. Strip them with a regex,
repeatable for more than one pattern:

```bash
krutiextract --dir books --out-dir out \
    --drop-pattern "^\s*Reprint \d{4}" \
    --drop-pattern "^\s*समकालीन भारत"
```

`Reprint YYYY` lines are dropped by default.

---

## 5. Scanned PDFs and OCR

If a page is an image, the text has to be recognised rather than read. The
order of attack, most effective first:

**1. Raise the render resolution.** This matters more than everything else
combined. Measured on a Hindi text column, Tesseract reached about 0.5%
character error rate at an effective 300 dpi on every degradation tested —
blur, noise, heavy JPEG, an uneven wash. Below roughly 100 dpi the error rate
jumps to 18–27%.

```bash
krutiextract --input scan.pdf --ocr-dpi 600
```

**2. Rescan the source if you can.** No software puts back detail the scan
never captured.

**3. Then try image cleaning.**

```bash
krutiextract --input scan.pdf --enhance-ocr
```

This applies only what a measurement of each image indicates:

| Condition detected | Action | Measured effect |
|---|---|---|
| uneven lighting or a smooth watermark | divide out the background | CER 0.042 → 0.011 |
| genuinely noisy | non-local-means denoise | 0.060 → 0.023 |
| small **and** sharp text | Lanczos upscale | 0.018 → 0.005 |
| skewed | rotate to the dominant text angle | — |

Three things it deliberately does not do, because each measured worse:
binarise before Tesseract (0.178 → 0.216 — modern Tesseract wants grayscale
and does its own thresholding), sharpen a blurred scan (0.702 → 0.724), and
upscale a heavily JPEG-compressed image.

Reproduce the whole measurement on your own material:

```bash
python tools/benchmark_ocr.py sample.pdf 2 100 75
```

### Choosing the OCR language

The default is `hin+eng`, and the reason is that the cost is lopsided.

| Document | `--ocr-language hin` | `hin+eng` |
|---|---|---|
| Hindi text column | 0.006 CER | 0.026 CER |
| Scanned English page (UPSC paper) | 909 Devanagari chars, 18 Latin — unusable | reads correctly |

Forced to Hindi alone, Tesseract maps Latin letter shapes onto Devanagari and
an English page comes back as nonsense. Two points of Hindi accuracy is a fair
price for not destroying English and bilingual papers.

If you are batch-converting Hindi-only scans and want the extra accuracy:

```bash
krutiextract --dir scans --out-dir out --ocr-language hin
```

### A note on resolution

Rendering above the scan's own resolution adds nothing. A UPSC paper whose
embedded page images are 2649x3680 works out at about 321 dpi; `--ocr-dpi 400`
and `--ocr-dpi 600` produced identical output. Raise the setting when the
source is high-resolution, rescan when it is not.

Other switches: `--no-ocr` to skip image pages entirely, `--no-deskew` and
`--binarise` to override the automatic decisions.

---

## 6. Checking the output

Three quick checks catch most problems.

**Does the encoding line match the book?** An NCERT Hindi textbook reporting
`krutidev` means detection went wrong.

**Search for the tell-tale wrong words.** These are what a
KrutiDev map applied to Walkman-Chanakya text produces:

```bash
grep -c "वेफ\|वुफ\|पफ\|उफ" chapter1.md      # expect 0
```

**Look for leftover Latin.** Some is legitimate — English terms, HTML tags:

```bash
grep -o -E "\b[a-zA-Z]{3,}\b" chapter1.md | sort | uniq -c | sort -rn | head
```

Long runs of consonant-heavy nonsense mean a block was not converted.

---

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `वुफल` instead of `कुल`, `क्षेत्रापफल` instead of `क्षेत्रफल` | Walkman text converted with the KrutiDev map | `--profile walkman` |
| `वेफ` where `के` belongs | same | `--profile walkman` |
| Output is empty, warning about no text recovered | image-only PDF, OCR unavailable | install Tesseract and the Hindi pack |
| `password protected` | encrypted PDF | remove the password first |
| Whole paragraphs left as Latin | wrong profile, or an encoding not supported | check the encoding line; see section 9 |
| English words mangled into Devanagari | no font evidence, usually OCR output | force `--profile english` for that file |
| Markdown tables broken | report it with the PDF; pipes are protected and this is a bug |
| `image enhancement needs OpenCV` | optional extra missing | `pip install "krutiextract[ocr]"` |
| Escape codes in a redirected file | fixed in 1.2.0 | upgrade, or set `NO_COLOR=1` |

---

## 8. Using it as a library

```python
from krutiextract import convert_pdf

markdown, profile, warnings = convert_pdf("chapter1.pdf")
print(profile)        # 'walkman'
for w in warnings:
    print(w)
```

Converting a string you already have:

```python
from krutiextract import auto_detect_font, convert_legacy_text

text = "dks;ys osQ izpqj HkaMkj gSaA"
auto_detect_font(text)                    # 'walkman'
convert_legacy_text(text, "auto")         # 'कोयले के प्रचुर भंडार हैं।'
```

Direct access to one profile, skipping detection:

```python
from krutiextract import krutidev_to_unicode, walkman_to_unicode

walkman_to_unicode("{ks=k")     # 'क्षेत्र'
krutidev_to_unicode("{ks=")     # 'क्षेत्र'
```

`convert_pdf` accepts the same options as the CLI: `font`, `ocr`,
`ocr_dpi`, `ocr_language`, `enhance_ocr`, `drop_patterns`, `pages`.

---

## 9. Adding a new encoding

Shree-Lipi, Shusha, APS, Akruti, ISM and several KrutiDev variants are not
supported. Adding one is mechanical, and the method matters more than the
table: **never guess a mapping, read it off the font.**

1. Get the font. A PDF that uses it already embeds a subset:

   ```python
   import pymupdf
   doc = pymupdf.open("sample.pdf")
   for f in doc[0].get_fonts(full=True):
       print(f)                       # xref, type, and the font name
   name, ext, _, buf = doc.extract_font(xref)
   open("embedded." + ext, "wb").write(buf)
   ```

2. Render every code point and read the glyphs. Draw `chr(c)` for `c` in
   32–255 in that font, rasterise, and look at the grid. That is ground truth;
   character-frequency guesses are not.

3. Build a word list from the real document. Take the raw text of one page,
   render that page, and write down the pairs you can read off the image. This
   becomes the test corpus, as `tests/corpus_walkman.py` was.

4. Add a profile in `src/converter.py`. Start from the KrutiDev map and record
   only the differences, as `_WALKMAN_OVERRIDES` does, plus any two-key
   keyboard rules in `_WALKMAN_PRE`.

5. Add a detection signature in `auto_detect_font`, using multi-character
   sequences that are meaningless in the other encodings.

6. Regenerate the bigram profile so English detection knows the new shapes:

   ```bash
   python tools/build_legacy_profile.py src/legacy_profile.py sample1.pdf sample2.pdf
   ```

7. Run `pytest`. Every existing pair must still pass: a new profile must not
   change an old one.

Issues with a sample PDF attached are welcome, and are the fastest route to
support for an encoding you need.
