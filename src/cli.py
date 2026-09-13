import argparse
import os
import sys
import re
from .extractor import extract_raw_markdown
from .converter import convert_legacy_text
from .markdown_utils import protect_non_hindi_syntax, restore_non_hindi_syntax
from .image_cleaner import enhance_pdf_images
import tempfile

def clean_lines(text: str) -> str:
    """Removes common footers/headers found in NCERT books."""
    final_lines = []
    lines = text.split('\n')
    for line in lines:
        l = line.strip()
        if not l:
            final_lines.append(line)
            continue
            
        if "Reprint 2024" in l:
            continue
        if re.search(r'\d+\s+समकालीन भारत', l) or re.search(r'समकालीन भारत\s*-\s*\d+', l):
            continue
        if re.search(r'\d+\s+आर्थिक विकास', l) or re.search(r'आर्थिक विकास\s*-\s*\d+', l):
            continue
        if re.search(r'\d+\s+लोकतांत्रिक राजनीति', l) or re.search(r'लोकतांत्रिक राजनीति\s*-\s*\d+', l):
            continue
            
        final_lines.append(line)
    return '\n'.join(final_lines)

def process_file(pdf_path: str, out_md_path: str, font: str = "auto", enhance_ocr: bool = False):
    print(f"Extracting {pdf_path}...")
    
    target_pdf = pdf_path
    temp_pdf_path = None
    if enhance_ocr:
        print("  -> Enhancing blurry images for OCR...")
        fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        try:
            enhance_pdf_images(pdf_path, temp_pdf_path)
            target_pdf = temp_pdf_path
        except Exception as e:
            print(f"  -> Warning: Image enhancement failed ({e}). Proceeding without enhancement.")
            target_pdf = pdf_path
            
    raw_text = extract_raw_markdown(target_pdf)
    
    if temp_pdf_path and os.path.exists(temp_pdf_path):
        os.remove(temp_pdf_path)
        
    if not raw_text:
        return

    # Protect formatting and English words
    protected_text, preserved_tokens = protect_non_hindi_syntax(raw_text)

    # Convert Hindi text
    converted_text = convert_legacy_text(protected_text, font)

    # Restore formatting
    restored_text = restore_non_hindi_syntax(converted_text, preserved_tokens)

    # Clean header/footer lines
    final_text = clean_lines(restored_text)

    with open(out_md_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    print(f"Saved {out_md_path}")

def main():
    parser = argparse.ArgumentParser(description="Universal Legacy Hindi PDF to Markdown Extractor")
    parser.add_argument("--input", help="Path to a single PDF file to process.")
    parser.add_argument("--output", help="Path to save the output markdown file.")
    parser.add_argument("--dir", help="Path to a directory of PDFs to batch process.")
    parser.add_argument("--out-dir", help="Path to the directory where markdown files should be saved (defaults to --dir).")

    parser.add_argument("--font", help="Legacy font encoding: krutidev, chanakya, auto, unicode, english", default="auto", choices=["krutidev", "chanakya", "auto", "unicode", "english"])
    parser.add_argument("--enhance-ocr", help="Upscale and sharpen images in the PDF before extraction for better OCR accuracy.", action="store_true")
    args = parser.parse_args()

    if args.input:
        if not args.output:
            args.output = os.path.splitext(args.input)[0] + '.md'
        process_file(args.input, args.output, args.font, args.enhance_ocr)
    
    elif args.dir:
        out_dir = args.out_dir if args.out_dir else args.dir
        os.makedirs(out_dir, exist_ok=True)

        for root, _, files in os.walk(args.dir):
            for f in files:
                if f.endswith('.pdf'):
                    pdf_path = os.path.join(root, f)
                    
                    # Maintain relative structure if needed, or just flat
                    rel_path = os.path.relpath(root, args.dir)
                    target_dir = os.path.join(out_dir, rel_path) if rel_path != "." else out_dir
                    os.makedirs(target_dir, exist_ok=True)
                    
                    out_md_path = os.path.join(target_dir, os.path.splitext(f)[0] + '.md')
                    process_file(pdf_path, out_md_path, args.font, args.enhance_ocr)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
