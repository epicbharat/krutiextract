# -*- coding: utf-8 -*-
"""Batch-convert the local NCERT folders.

Edit FOLDERS to taste. Runs the package as a module so it works from a source
checkout without installing.
"""

import os
import subprocess
import sys

FOLDERS = [
    r"D:\GSSS Jethantri\NCERT BOoks\10th\Social Science_Hi",
    r"D:\GSSS Jethantri\NCERT BOoks\10th\Social Science_Eng",
]


def main():
    failures = 0
    for folder in FOLDERS:
        if not os.path.isdir(folder):
            print(f"Directory not found: {folder}")
            continue
        print(f"\n{'=' * 60}\n{folder}\n{'=' * 60}")
        result = subprocess.run(
            [sys.executable, "-m", "src.cli", "--dir", folder, "--enhance-ocr"],
            check=False,
        )
        failures += result.returncode != 0
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
