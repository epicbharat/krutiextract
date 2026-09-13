<div align="center">
  <img src="https://raw.githubusercontent.com/epicbharat/krutiextract/main/assets/logo.png" alt="KrutiExtract Logo" width="250"/>
  
  <h1>KrutiExtract</h1>
  <p><strong>A Universal Legacy Hindi PDF to Markdown Extractor</strong></p>

  [![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/epicbharat)
</div>

<hr/>

Extracting legacy Hindi fonts (like **KrutiDev**, **Devlys**, or **Chanakya**) from PDF documents has traditionally been a nightmare. Standard OCR and PDF text extractors read characters based on visual coordinates. Because Hindi matras (vowel marks like `ि` or `े`) overlap with consonants, this visual sorting scrambles the text (e.g., typing `vkSj` for 'और' gets extracted as `vkjS`, breaking the conversion into the nonsense word 'आरै'). 

**KrutiExtract** solves this problem by bypassing visual coordinate sorting and extracting the **logical character stream** directly from the PDF.

## ✨ Core Features

- **Perfect Character Order:** Preserves the original typist's keystrokes, completely avoiding spatial scrambling of matras.
- **Smart Auto-Detect Engine:** Automatically mathematically calculates text frequencies to detect whether the typist used **KrutiDev / Devlys** or **Chanakya**, instantly routing the text to the correct translation engine!
- **English / Hinglish Bypass Mode:** If the engine detects that the document contains modern Unicode Hindi, standard English, or Hinglish, it automatically bypasses legacy conversion entirely—perfectly preserving your modern texts!
- **Dynamic English Preservation:** Uses NLTK's English corpus to proactively detect and protect English words, numbers, acronyms, and HTML tags interspersed within mixed-font Hindi texts.
- **Collision-Free Safe-Tokens:** Markdown syntax elements (like `#` or `*`) clash with KrutiDev maps. KrutiExtract shields these structural elements using a unique `$$$INDEX$$$` safe-token system during font conversion.

## 👁️ Advanced OCR & Image Cleaning

When the toolkit encounters text trapped inside a scanned image, it seamlessly hands it over to **Tesseract OCR** in the background.

- **Native Hindi OCR:** The toolkit hardcodes `ocr_language="hin"` into the internal pipeline. This permanently stops Tesseract from trying to hallucinate English letters onto Hindi image shapes, ensuring natively output Unicode Devanagari.
- **OpenCV Image Cleaning (`--enhance-ocr`):** Pass this flag to activate our built-in computer vision pipeline. The toolkit will automatically intercept blurry images in the PDF, upscale the resolution, apply unsharp masking, and run adaptive thresholding to perfectly reconstruct the text shapes *before* OCR scans it!

## 🚀 Installation

Ensure you have Python 3.8+ installed.

```bash
# Clone the repository
git clone https://github.com/epicbharat/krutiextract.git
cd krutiextract

# Create and activate a virtual environment (Recommended)
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Download the required NLTK English word corpus
python -c "import nltk; nltk.download('words')"
```

### Note on Tesseract (Required for OCR)
If you are parsing scanned PDFs or PDFs with embedded images, you must have [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system.
- **Windows:** Download the installer and ensure you check the **"Hindi"** language pack during installation. Add Tesseract to your PATH.
- **Linux:** `sudo apt-get install tesseract-ocr tesseract-ocr-hin`

## 💻 CLI Usage Guide

KrutiExtract provides a powerful Command Line Interface (CLI).

### 1. Process a Single File
```bash
python -m src.cli --input "path/to/document.pdf" --output "path/to/output.md"
```

### 2. Batch Process a Directory
Recursively process an entire folder of PDFs:
```bash
python -m src.cli --dir "path/to/pdf/folder" --out-dir "path/to/markdown/folder"
```

### 3. Force a Specific Font Encoding
By default, the font is set to `auto`. You can force a specific bypass or mapping:
```bash
# Available options: krutidev, chanakya, auto, unicode, english
python -m src.cli --input "doc.pdf" --font chanakya
```

### 4. Enable OpenCV OCR Enhancement
Use this flag for old, blurry, or low-resolution scanned PDFs to artificially sharpen the text before extraction:
```bash
python -m src.cli --input "blurry_scan.pdf" --enhance-ocr
```

## 🤝 Contributing

Contributions are welcome! If you find a PDF that breaks the extraction logic or a rare character combination we missed, please open an issue and attach the sample PDF.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
**Author:** Bharat Choudhary (Lecturer, Department of Secondary Education, Govt. of Rajasthan)  
**Email:** epicbharat@gmail.com  
**GitHub:** [https://github.com/epicbharat](https://github.com/epicbharat)
