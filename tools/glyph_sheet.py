# -*- coding: utf-8 -*-
"""Read a legacy font's mapping off a real page instead of guessing it.

    python tools/glyph_sheet.py sample.pdf FONT_SUBSTRING [page] [--words]

Crops every distinct code point (or every word, with --words) from a rendered
page and lays them out labelled, so the Devanagari each byte actually draws can
be read directly. This is how the Walkman-Chanakya and Chanakya profiles were
built; see docs/APS-DV-PRIYANKA.md for the method applied to a new encoding.

Needs the [ocr] extra for OpenCV.
"""

import sys

import cv2
import numpy as np
import pymupdf


def crops_by_char(page, gray, zoom, font_match):
    found = {}
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                if font_match not in span["font"]:
                    continue
                for char in span["chars"]:
                    code = char["c"]
                    if code.isspace() or code in found:
                        continue
                    x0, y0, x1, y1 = char["bbox"]
                    box = gray[max(0, int(y0 * zoom) - 2):int(y1 * zoom) + 2,
                               max(0, int(x0 * zoom) - 2):int(x1 * zoom) + 2]
                    if box.size and box.min() < 200:
                        found[code] = box
    return [(c, found[c]) for c in sorted(found, key=ord)]


def crops_by_word(page, gray, zoom, limit=40):
    out = []
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        if len(text.strip()) < 3:
            continue
        box = gray[max(0, int(y0 * zoom) - 3):int(y1 * zoom) + 3,
                   max(0, int(x0 * zoom) - 2):int(x1 * zoom) + 2]
        if box.size:
            out.append((text, box))
        if len(out) >= limit:
            break
    return out


def sheet(items, cell_w, cell_h, cols, label_index=False):
    rows = (len(items) + cols - 1) // cols
    canvas = np.full((rows * cell_h + 8, cols * cell_w + 8), 255, np.uint8)
    for i, (label, box) in enumerate(items):
        row, col = divmod(i, cols)
        h, w = box.shape
        scale = min((cell_h - 26) / h, (cell_w - 46) / w, 2.5)
        box = cv2.resize(box, (max(1, int(w * scale)), max(1, int(h * scale))),
                         interpolation=cv2.INTER_CUBIC)
        h, w = box.shape
        y = row * cell_h + 22 + (cell_h - 26 - h) // 2
        x = col * cell_w + 42
        canvas[y:y + h, x:x + w] = box
        text = str(i + 1) if label_index else label
        cv2.putText(canvas, text, (col * cell_w + 6, row * cell_h + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (80,), 1, cv2.LINE_AA)
        cv2.line(canvas, (col * cell_w + 2, row * cell_h + 2),
                 (col * cell_w + 2, row * cell_h + cell_h - 2), (205,), 1)
    return canvas


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    path, font_match = argv[1], argv[2]
    page_no = int(argv[3]) if len(argv) > 3 and argv[3].isdigit() else 0
    by_words = "--words" in argv

    doc = pymupdf.open(path)
    page = doc[page_no]
    dpi = 300
    zoom = dpi / 72
    pix = page.get_pixmap(dpi=dpi)
    image = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, pix.n)
    gray = cv2.cvtColor(
        image, cv2.COLOR_RGB2GRAY if pix.n == 3 else cv2.COLOR_RGBA2GRAY)

    if by_words:
        items = crops_by_word(page, gray, zoom)
        out = sheet(items, 300, 70, 4, label_index=True)
        for i, (text, _) in enumerate(items):
            print(f"{i + 1:3}. {text}")
    else:
        items = crops_by_char(page, gray, zoom, font_match)
        out = sheet(items, 84, 96, 10)
        print(f"{len(items)} distinct code points: " + "".join(c for c, _ in items))

    name = "glyph_sheet_words.png" if by_words else "glyph_sheet.png"
    cv2.imwrite(name, out)
    print(f"wrote {name}")
    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
