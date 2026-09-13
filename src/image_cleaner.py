import pymupdf
import cv2
import numpy as np
import os

def enhance_pdf_images(input_path: str, output_path: str):
    """
    Scans a PDF for all images, extracts them, applies OpenCV text-sharpening 
    and adaptive thresholding, and replaces the blurry images with the enhanced ones.
    """
    doc = pymupdf.open(input_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        
        for img_info in image_list:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            # Convert bytes to numpy array for OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                continue
                
            # --- OpenCV Enhancement Pipeline ---
            # 1. Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. Resize (upscale by 2x) to give Tesseract more pixels
            gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            
            # 2.5 Erase Watermarks: Push all light gray pixels (> 180 brightness) to pure white
            # This perfectly deletes solid gray diagonal watermarks like "BSER"
            gray[gray > 180] = 255
            
            # 3. Unsharp Masking (Sharpen)
            gaussian = cv2.GaussianBlur(gray, (9,9), 10.0)
            sharpened = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0, gray)
            
            # 4. Adaptive Thresholding to handle uneven lighting on scanned documents
            thresh = cv2.adaptiveThreshold(
                sharpened, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 31, 2
            )
            
            # Convert back to bytes
            is_success, buffer = cv2.imencode(f".png", thresh)
            if is_success:
                enhanced_bytes = buffer.tobytes()
                
                # We need to find the bounding box of the image on the page to replace it safely
                rects = page.get_image_rects(xref)
                if rects:
                    # PyMuPDF doesn't have a direct "replace_image" that works reliably for all PDFs,
                    # so we insert the new image exactly over the old rects.
                    for rect in rects:
                        page.insert_image(rect, stream=enhanced_bytes, keep_proportion=False)
                    
                    # We cannot safely delete the xref in some PDFs without corrupting the page stream,
                    # but inserting the new image perfectly over the old one ensures OCR sees the new one.

    doc.save(output_path, garbage=3, deflate=True)
    doc.close()
