# -*- coding: utf-8 -*-
"""Batch-convert one or more folders of PDFs.

    python extract_all.py "/path/to/folder" "/another/folder"

Equivalent to running the CLI once per folder, which is all this does. It
exists so a source checkout can be driven without installing the package.
"""

import os
import subprocess
import sys


def main(argv):
    folders = argv[1:]
    if not folders:
        print(__doc__.strip())
        print("\nNo folders given.")
        return 2

    failures = 0
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"Directory not found: {folder}")
            failures += 1
            continue
        print(f"\n{'=' * 60}\n{folder}\n{'=' * 60}")
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "--dir", folder, "--enhance-ocr"],
            check=False,
        )
        failures += result.returncode != 0
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
