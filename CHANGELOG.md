# Changelog

All notable changes to this project are documented here. Versions follow
[Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-09-14

### Added
- **APS-DV-Priyanka**, as the `aps` profile (alias `priyanka`), detected
  automatically. Derived by rendering the font itself: code 101 `e` is the
  vertical stem, which completes a stem-less consonant and otherwise reads as
  the ा matra. That one rule resolved the structure. Verified against 72 word
  pairs read off rendered pages, with 0.235% unmapped characters across 140
  held-out pages.
- `tools/glyph_sheet.py`, which crops every code point and word from a real
  page so a new encoding can be read off the document rather than guessed.

## [1.2.0] - 2026-09-13

Rebuilt around a finding: the tool had been treating two incompatible
encodings as one. NCERT Hindi textbooks are set in **Walkman-Chanakya 905**,
not KrutiDev, and the rules conflict — `=k` is त्र in one and त्रा in the
other, `osQ` is के in one and वेफ in the other.

### Added
- Separate `krutidev`, `walkman` and `chanakya` profiles, detected per
  document. Each mapping is anchored to its font file, and the Walkman tables
  were checked against the font embedded in an NCERT PDF and its rendered
  pages.
- `english`, `hinglish` and `unicode` profiles that convert nothing. The
  protect/convert/restore cycle is skipped for these, so it cannot damage them.
- Profile routing from the PDF's own fonts: text drawn in a Latin body font
  has nothing to convert, whatever its characters look like.
- Latin-font spans are matched **in document order**, so position
  disambiguates — `(v)` is the Hindi letter अ while `(i)` is a Roman numeral
  on the same page.
- A character-bigram model to separate English from legacy where a dictionary
  cannot: `thou` is the legacy spelling of जीवन, `leaching` is a real gloss.
- Repair pass for extractor artefacts: `<sup>`/`<mark>` tags that split a word,
  emphasis around a single matra, HTML comment scaffolding.
- Regression suite (270 tests) built from font glyph tables and rendered pages.
- `tools/benchmark_ocr.py`, which measures OCR character error rate against
  degraded renders of a known page.
- `--ocr-dpi`, `--no-deskew`, `--binarise`, `--drop-pattern`, `--version`.

### Changed
- **Image enhancement now applies only what a measurement of each image
  indicates.** Binarising before Tesseract measured *worse* (mean CER 0.178 →
  0.216) and is off by default; sharpening a blurred scan measured worse
  (0.702 → 0.724). Kept: background division for washes (0.042 → 0.011),
  denoise for real noise (0.060 → 0.023), Lanczos upscale for small sharp text
  (0.018 → 0.005), deskew.
- **Default OCR language is now `hin+eng`, not `hin`.** Forced to Hindi alone,
  Tesseract maps Latin shapes onto Devanagari: a scanned UPSC paper came back
  with 909 Devanagari characters and 18 Latin ones. The cost is 0.006 CER
  against 0.026 on a Hindi-only column, which is worth paying. Pass
  `--ocr-language hin` for Hindi-only batches.
- Default OCR resolution raised to 400 dpi. Resolution dominates every other
  factor: at an effective 300 dpi Tesseract reached ~0.5% CER on every
  degradation tested.
- Safe tokens moved from CJK to Plane-15 private use. CJK code points are word
  characters, which silently broke every `\b` boundary next to a token and left
  the adjacent English word exposed to the converter.
- Colour is emitted only to a terminal, and honours `NO_COLOR`.
- Header and footer stripping is driven by `--drop-pattern` instead of three
  hard-coded NCERT book titles.

### Documentation
- `docs/GUIDE.md`: install, first conversion, choosing a profile, batch runs,
  OCR tuning, an output-checking routine, a troubleshooting table, the library
  API, and how to add a new encoding from its font.
- `CHANGELOG.md`, a CI workflow, a `ruff` configuration and `MANIFEST.in`.

### Added
- **MacRoman-reported legacy streams.** Some producers report legacy 8-bit
  bytes through a MacRoman map, so the same font surfaces as different
  characters and nothing converted. Detected by marker characters that appear
  in a MacRoman reading and in neither legacy map (23% of the non-ASCII in one
  such book, zero across the Windows-encoded ones) and re-read through a
  translation table.
- The Chanakya profile is now anchored to a real 216-page book: 24 verified
  word pairs in `tests/corpus_chanakya.py`. It previously shipped on unit
  tests alone.
- A warning when a document yields very little text per page, which is what a
  scan of nothing but watermarks looks like.

### Fixed
- The Markdown extractor expands the fi/fl ligatures before conversion sees
  them, and in MacRoman those are the bytes for two letters. "रावल" was coming
  out as "राद्घद्यल". Recomposed before the byte translation.
- Image enhancement decoded through `cv2.imdecode`, which has no JPEG2000
  support in the headless wheel and logged a C++ error to stderr for every
  JPX image. Decoding now goes through PyMuPDF, which is codec-independent.
- An encrypted PDF surfaced as `'NoneType' object is not subscriptable`
  instead of "password protected".
- A PDF with no recoverable text was written out as an empty file with no
  explanation.
- **The legacy fragment repairs ran on every document, including ones needing
  no conversion.** Those rules delete emphasis markers and the space beside
  them, which is right for a word the extractor split across a `<sup>` and
  wrong everywhere else: `vitamin **a** deficiency` became
  `vitaminadeficiency`. They now run only for a legacy profile, and a
  `unicode`, `hinglish` or `english` document is returned byte-identical to
  what the extractor produced.
- **Detection was wrong on four of six real documents.** Fixed by, in order:
  anchoring the KrutiDev signatures to whole tokens (unanchored, they matched
  inside "also", "these" and "worlds", so English prose scored as legacy);
  requiring a signature density rather than a single hit; weighing legacy
  evidence before the script census, so a Unicode heading over pages of
  KrutiDev no longer leaves a whole book unconverted; and treating a document
  with more Devanagari than Latin as needing no conversion.
- The font name no longer decides the profile, only warns. A legacy font under
  a custom name (one book used "Rajpurohit") was being forced to English and
  left entirely unconverted.
- `_family()` turned "APS-DV-Priyanka" into "a", because it split on "-" and
  stripped a trailing "PS". A legacy font was therefore read as an ordinary
  Latin one.
- `SUPPORTED_FONT_RE` matched "akruti" via "kruti", so an unsupported family
  was treated as supported and no warning was raised.
- A legacy Devanagari font with no mapping in this build now produces an
  explicit warning naming the font, instead of silently converting to nonsense.
- Aparajita was listed as a legacy font. It is a Unicode OpenType Devanagari
  font, so text drawn in it needs no conversion.
- Packaging: the console script pointed at `hindi_pdf_extractor.src.cli`, which
  never existed, and setuptools installed the modules flat as `cli`, `converter`
  and `extractor`. Version 1.0.7 could not run at all.
- `converter._get_english_words()` always returned an empty set: `nltk` was
  never imported and the `NameError` was swallowed by a bare `except`.
- Reph reordering: a `Z` at index 0 aborted the pass for the whole document; a
  space counted as a matra so `र्` crossed word boundaries; edits used a global
  `str.replace` under a stale cursor.
- Markdown tables, list bullets, decimals, percentages and link targets were
  destroyed by the converter (`|` → द्य, `.` → ण्, `:` → रू).
- Backticks were treated as inline code, but `` ` `` is the ृ matra, so two of
  them protected every Hindi word in between.
- `£` expanded after the short-i pass, leaving a bare `f` in the output.
- Nukta letters `”k` → ज़ and `ß` → ह्र in the Walkman profile, written in the
  decomposed form the rest of the map uses (`U+095B` is not NFC-stable).
- OCR arguments were silently discarded on the legacy pymupdf4llm back end.
- Extraction failures returned `None` and wrote an empty file.
- Watermark removal forced every pixel above brightness 180 to white, erasing
  light grey text as readily as a watermark.
- `enhance_pdf_images` stacked a second image over the first instead of
  replacing it, inflating the file.
- Batch mode missed files ending in `.PDF`.

## [1.0.7] - 2026-09

Initial published release.
