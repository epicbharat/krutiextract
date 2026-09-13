# Changelog

All notable changes to this project are documented here. Versions follow
[Semantic Versioning](https://semver.org/).

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
- Default OCR resolution raised to 400 dpi. Resolution dominates every other
  factor: at an effective 300 dpi Tesseract reached ~0.5% CER on every
  degradation tested.
- Safe tokens moved from CJK to Plane-15 private use. CJK code points are word
  characters, which silently broke every `\b` boundary next to a token and left
  the adjacent English word exposed to the converter.
- Colour is emitted only to a terminal, and honours `NO_COLOR`.
- Header and footer stripping is driven by `--drop-pattern` instead of three
  hard-coded NCERT book titles.

### Fixed
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
