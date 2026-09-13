# -*- coding: utf-8 -*-
"""Measure how much image enhancement actually helps OCR.

    python tools/benchmark_ocr.py sample.pdf [page] [dpi ...]

Takes the largest text block on *page*, renders it at each *dpi*, degrades it
six ways, and reports character error rate against the converted text of that
same block -- so the reference needs no manual transcription.

Needs Tesseract with the Hindi pack, plus the [ocr] extra and pytesseract.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import numpy as np
import pymupdf
import pytesseract

from src.converter import convert_legacy_text
from src.image_cleaner import enhance_image
from src.markdown_utils import (
    protect_non_hindi_syntax,
    restore_non_hindi_syntax,
)

DEVANAGARI_ONLY = re.compile(r"[^ऀ-ॿ]+")
TESSERACT_CONFIG = "--oem 1 --psm 6"
CASES = ["clean", "low-res", "blurred", "noisy", "jpeg", "washed"]


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", DEVANAGARI_ONLY.sub(" ", text)).strip()


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate: edit distance over reference length."""
    if not reference:
        return 1.0
    previous = list(range(len(hypothesis) + 1))
    for i, rc in enumerate(reference, 1):
        current = [i] + [0] * len(hypothesis)
        for j, hc in enumerate(hypothesis, 1):
            current[j] = min(previous[j] + 1,
                             current[j - 1] + 1,
                             previous[j - 1] + (rc != hc))
        previous = current
    return previous[-1] / len(reference)


def degrade(case: str, gray, rng):
    h, w = gray.shape
    if case == "clean":
        return gray
    if case == "low-res":
        s = 0.34
        small = cv2.resize(gray, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    if case == "blurred":
        return cv2.GaussianBlur(gray, (0, 0), 2.0)
    if case == "noisy":
        return np.clip(gray.astype(float) + rng.normal(0, 20, gray.shape), 0, 255).astype(np.uint8)
    if case == "jpeg":
        _, buf = cv2.imencode(".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, 15])
        return cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
    if case == "washed":
        yy, xx = np.mgrid[0:h, 0:w]
        wash = 150 + 80 * np.sin(xx / 300.0) * np.cos(yy / 400.0)
        return np.clip(gray.astype(float) * (wash / 255.0) + (255 - wash) * 0.6,
                       0, 255).astype(np.uint8)
    raise ValueError(case)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    pdf_path = argv[1]
    page_no = int(argv[2]) if len(argv) > 2 else 2
    dpis = [int(x) for x in argv[3:]] or [100, 75]

    doc = pymupdf.open(pdf_path)
    page = doc[page_no]
    blocks = [b for b in page.get_text("blocks") if len(b[4]) > 400]
    if not blocks:
        print(f"No text block over 400 characters on page {page_no}.")
        return 1
    block = max(blocks, key=lambda b: len(b[4]))
    rect = pymupdf.Rect(block[:4])

    protected, preserved = protect_non_hindi_syntax(block[4])
    reference = normalise(
        restore_non_hindi_syntax(convert_legacy_text(protected, "auto"), preserved))
    print(f"{pdf_path} page {page_no}: {len(reference)} reference characters\n")

    rng = np.random.default_rng(0)
    for dpi in dpis:
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        buf = np.frombuffer(pix.samples, dtype=np.uint8)
        image = buf.reshape(pix.height, pix.width, pix.n)
        gray = cv2.cvtColor(
            image, cv2.COLOR_RGB2GRAY if pix.n == 3 else cv2.COLOR_RGBA2GRAY)

        print(f"--- source {dpi} dpi ---")
        print(f"{'case':<10}{'raw':>9}{'enhanced':>11}{'delta':>9}")
        raws, enhanced = [], []
        for case in CASES:
            degraded = degrade(case, gray, rng)
            a = cer(reference, normalise(pytesseract.image_to_string(
                degraded, lang="hin", config=TESSERACT_CONFIG)))
            b = cer(reference, normalise(pytesseract.image_to_string(
                enhance_image(degraded), lang="hin", config=TESSERACT_CONFIG)))
            raws.append(a)
            enhanced.append(b)
            print(f"{case:<10}{a:>9.3f}{b:>11.3f}{b - a:>+9.3f}")
        mean_raw, mean_enh = float(np.mean(raws)), float(np.mean(enhanced))
        print(f"{'MEAN':<10}{mean_raw:>9.3f}{mean_enh:>11.3f}"
              f"{mean_enh - mean_raw:>+9.3f}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
