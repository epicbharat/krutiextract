<div align="center">
  <img src="https://raw.githubusercontent.com/epicbharat/krutiextract/main/assets/banner.png" alt="KrutiExtract Banner" width="100%"/>

  <h1>KrutiExtract</h1>
  <p><strong>The Ultimate Legacy Hindi PDF to Markdown Extractor</strong></p>

  [![tests](https://github.com/epicbharat/krutiextract/actions/workflows/ci.yml/badge.svg)](https://github.com/epicbharat/krutiextract/actions/workflows/ci.yml)
  [![PyPI Version](https://img.shields.io/pypi/v/krutiextract.svg)](https://pypi.org/project/krutiextract/)
  [![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
</div>

<hr/>

### 🚀 The Problem with Legacy Hindi PDFs
Legacy Hindi fonts store Devanagari in 8-bit slots, meaning a PDF written in one of them extracts as Latin gibberish. Worse, standard OCR extractors sort glyphs by visual position, which permanently scrambles matras: `vkSj` (और) is read as `vkjS` and incorrectly converts to the non-word `आरै`.

### ✨ The KrutiExtract Solution
KrutiExtract reads the **logical character stream** instead of the visual order, ensuring the typist's original keystrokes survive intact, and mathematically maps them back to flawless Unicode Hindi. 

**New here? Start with the [How-To Guide](docs/GUIDE.md)** — install, first conversion, choosing a profile, batch runs, OCR tuning and troubleshooting.

---

## 🛠️ Supported Encodings

These are different fonts with conflicting rules. Applying one profile's rules to another's document corrupts it, so the profile is automatically detected per document.

| Profile | Font Name | `=k` | `osQ` | `(` |
|:---|:---|:---:|:---:|:---:|
| `krutidev` *(devlys)* | KrutiDev 010, DevLys 010 | त्रा | वेफ | `;` |
| `walkman` *(ncert)* | Walkman-Chanakya 905 | त्र | के | `(` |
| `chanakya` | Chanakya | — | — | — |
| `aps` *(priyanka)* | APS-DV-Priyanka | — | — | — |
| `shreelipi` *(shreedev)* | Shree-Lipi / Shree Dev | — | — | — |
| `shusha` *(susha)* | Shusha | — | — | — |
| `aakriti` *(akruti)* | Aakriti | — | — | — |

> [!NOTE]
> **NCERT Hindi textbooks use Walkman-Chanakya 905**, not KrutiDev. That is why older single-map approaches produced `वुफल` for `कुल` and `क्षेत्रापफल` for `क्षेत्रफल`.

---

## 🛡️ Smart Protection Engine

Before conversion, KrutiExtract swaps out the following elements for opaque Private Use characters to protect them from being corrupted, restoring them perfectly afterward:

- **Standard Latin text** (e.g., Roman numerals or English paragraphs).
- **Markdown structure** (headings, lists, tables, links, bold/italics).
- **Numbers & Web elements** (URLs, e-mail addresses, decimals, percentages).
- **English words**, gated by both a dictionary and a character-bigram model.

---

## 📦 Installation

Install easily via pip:

```bash
pip install krutiextract
```

### Optional OCR Support
For extracting scanned PDFs (image-only pages), install the OCR dependencies:
```bash
pip install "krutiextract[ocr]"
```

*Note: OCR requires [Tesseract](https://github.com/tesseract-ocr/tesseract) to be installed on your system with the Hindi language pack.*
- **Windows**: Run the Tesseract installer, tick **Hindi**, and add it to your PATH.
- **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-hin`

---

## 💻 Usage

KrutiExtract comes with a powerful CLI for processing single files or massive batches.

```bash
# Convert a single file (encoding is auto-detected)
krutiextract --input document.pdf --output document.md

# Batch convert an entire directory tree
krutiextract --dir ./pdfs --out-dir ./markdown

# Force a specific profile override
krutiextract --input doc.pdf --profile walkman

# Sharpen scanned images first (requires [ocr] extra)
krutiextract --input scan.pdf --enhance-ocr

# Drop running headers automatically
krutiextract --input doc.pdf --drop-pattern "^\s*Chapter \d+\s*$"

# Raise OCR resolution (highest impact on accuracy)
krutiextract --input scan.pdf --ocr-dpi 600
```

### 🧩 Python Library Usage

You can also use KrutiExtract directly in your Python code:

```python
from krutiextract import convert_pdf, walkman_to_unicode

# Convert a full PDF to Markdown
markdown, profile, warnings = convert_pdf("jhss101.pdf")

# Convert a single string
print(walkman_to_unicode("{ks=k"))  # Output: 'क्षेत्र'
```

---

## 🔬 OCR Quality & Enhancement

Measured against ground-truth converted text, **resolution dominates everything else.** At an effective 300 DPI, Tesseract reached ~0.5% Character Error Rate (CER) on *every* degradation tested.

If your scans are poor, use `--enhance-ocr`. It applies dynamic computer vision enhancements:
- **Uneven lighting/watermarks**: Divides out the background (0.042 → 0.011 CER).
- **Heavy Noise**: Non-local-means denoising (0.060 → 0.023 CER).
- **Small, sharp text**: Lanczos upscaling (0.018 → 0.005 CER).

If your scans are still failing, raise the `--ocr-dpi` (default 400), or rescan at a higher resolution.

---

## ⚠️ Known Limits

- **Seven of the eight encodings are anchored to a rendered page.** KrutiDev 010, DevLys 010, Walkman-Chanakya 905, Chanakya, APS-DV-Priyanka, Shusha and Aakriti are each checked mathematically against their font tables.
- **Shree-Lipi is a family, not one encoding.** Measured against the SHREE726 font. See `docs/SHREE-LIPI.md`.
- **English/Hindi Ambiguity**: An isolated English word with no font evidence can sometimes be misread as Hindi. Font evidence resolves this in PDFs; OCR output does not.

## 🤝 Contributing & Licensing

If a PDF breaks the extraction, please open an issue and attach it! See the [Changelog](CHANGELOG.md) for recent updates.

**License:** MIT. See [LICENSE](LICENSE).

<div align="center">
  <br/>
  <strong>Author:</strong> Bharat Choudhary<br/>
  <strong>Email:</strong> epicbharat@gmail.com<br/>
  <strong>GitHub:</strong> <a href="https://github.com/epicbharat">epicbharat</a>
</div>
