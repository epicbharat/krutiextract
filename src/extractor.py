import pymupdf4llm
from typing import Optional

def extract_raw_markdown(pdf_path: str) -> Optional[str]:
    """
    Extracts text from a PDF as Markdown using pymupdf4llm.
    This preserves the logical stream of the text (bypassing visual/spatial 
    scrambling) and extracts basic markdown formatting.
    """
    try:
        raw_text = pymupdf4llm.to_markdown(
            pdf_path, 
            force_text=True, 
            ocr_language="hin", 
            ocr_dpi=300
        )
        return raw_text
    except Exception as e:
        print(f"Error extracting {pdf_path}: {e}")
        return None
