# -*- coding: utf-8 -*-
"""Regenerate src/legacy_profile.py from one or more legacy PDFs.

    python tools/build_legacy_profile.py out.py sample1.pdf sample2.pdf ...

Words the PDF drew in a Latin font are excluded automatically, so the counts
describe legacy-encoded text only.
"""

import re
import sys
from collections import Counter

sys.path.insert(0, ".")
from src.pdf_spans import latin_spans

TOKEN = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9]{2,}(?![A-Za-z0-9])")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    out_path, pdfs = argv[1], argv[2:]

    import pymupdf

    counts = Counter()
    for path in pdfs:
        doc = pymupdf.open(path)
        raw = "".join(page.get_text() for page in doc)
        doc.close()
        latin = {t.lower() for span in latin_spans(path) for t in TOKEN.findall(span)}
        for tok in {t for t in TOKEN.findall(raw) if not t.isdigit()}:
            if tok.lower() in latin:
                continue
            padded = "^" + tok.lower() + "$"
            counts.update(padded[i:i + 2] for i in range(len(padded) - 1))

    body = ", ".join(f'"{k}": {v}' for k, v in sorted(counts.items()))
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write('# -*- coding: utf-8 -*-\n"""Character-bigram profile of '
                 'legacy-encoded text. Generated; do not edit."""\n\n')
        fh.write(f"LEGACY_BIGRAMS = {{{body}}}\n\nLEGACY_TOTAL = {sum(counts.values())}\n")
    print(f"wrote {out_path}: {len(counts)} bigrams, {sum(counts.values())} total")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
