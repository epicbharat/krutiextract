# -*- coding: utf-8 -*-
"""Command line interface."""

import argparse
import os
import sys
import time

from . import __version__
from .converter import PROFILES
from .extractor import ExtractionError, ocr_available
from .pipeline import convert_pdf

BANNER = r"""  _  __          _   _ ______      _                  _
 | |/ /         | | (_)  ____|    | |                | |
 | ' / _ __ _   | |_ _| |__  __  _| |_ _ __ __ _  ___| |_
 |  < | '__| | | | __| |  __| \ \/ / __| '__/ _` |/ __| __|
 | . \| |  | |_| | |_| | |____ >  <| |_| | | (_| | (__| |_
 |_|\_\_|   \__,_|\__|_|______/_/\_\\__|_|  \__,_|\___|\__|"""


class _Style:
    """ANSI codes, but only when stdout is a terminal.

    The previous version wrote escape codes unconditionally, so redirecting
    output to a file filled it with \\033[96m.
    """

    def __init__(self, stream):
        self.on = (
            hasattr(stream, "isatty")
            and stream.isatty()
            and os.environ.get("NO_COLOR") is None
        )

    def _wrap(self, code, text):
        return f"\033[{code}m{text}\033[0m" if self.on else text

    def cyan(self, t): return self._wrap("96", t)
    def green(self, t): return self._wrap("32", t)
    def red(self, t): return self._wrap("31", t)
    def dim(self, t): return self._wrap("2", t)
    def bold(self, t): return self._wrap("1", t)


def _human(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds // 60)}m{seconds % 60:02.0f}s"


def _process(pdf_path, out_md_path, args, style, label=""):
    name = os.path.basename(pdf_path)
    print(f"{style.dim(label)}{name}")
    started = time.monotonic()
    try:
        md, profile, warnings = convert_pdf(
            pdf_path,
            font=args.font,
            enhance_ocr=args.enhance_ocr,
            ocr=not args.no_ocr,
            ocr_language=args.ocr_language,
            ocr_dpi=args.ocr_dpi,
            enhance_options={
                "deskew": not args.no_deskew,
                "binarise": args.binarise,
            },
            drop_patterns=args.drop_pattern or (),
        )
    except ExtractionError as exc:
        print(f"      {style.red('failed')}  {exc}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"      {style.red('failed')}  {type(exc).__name__}: {exc}",
              file=sys.stderr)
        return False

    for w in warnings:
        print(f"      {style.dim('note')}    {w}", file=sys.stderr)

    parent = os.path.dirname(os.path.abspath(out_md_path))
    os.makedirs(parent, exist_ok=True)
    with open(out_md_path, "w", encoding="utf-8") as fh:
        fh.write(md)

    elapsed = _human(time.monotonic() - started)
    print(f"      {style.green('saved')}   {out_md_path}")
    print(f"      {style.dim('encoding')} {profile}   "
          f"{style.dim('chars')} {len(md):,}   {style.dim('took')} {elapsed}")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="krutiextract",
        description="Legacy Hindi PDF (KrutiDev / DevLys / Walkman-Chanakya / "
                    "Chanakya) to Markdown.",
        epilog="Encodings are detected per document; --profile only overrides "
               "that. Raising --ocr-dpi does more for scan quality than "
               "--enhance-ocr does.",
    )
    source = parser.add_argument_group("input")
    source.add_argument("--input", metavar="PDF", help="a single PDF to process")
    source.add_argument("--output", metavar="MD", help="where to write the Markdown")
    source.add_argument("--dir", metavar="DIR", help="a directory of PDFs to batch process")
    source.add_argument("--out-dir", metavar="DIR", help="output directory (default: --dir)")

    conv = parser.add_argument_group("conversion")
    conv.add_argument(
        "--font", "--profile", dest="font", default="auto",
        choices=("auto", *PROFILES), metavar="NAME",
        help="auto (default), " + ", ".join(PROFILES),
    )
    conv.add_argument("--drop-pattern", action="append", metavar="REGEX",
                      help="drop lines matching this regex; repeatable")

    ocr = parser.add_argument_group("ocr")
    ocr.add_argument("--ocr-dpi", type=int, default=400, metavar="N",
                     help="render resolution for OCR (default: 400). The "
                          "single biggest lever on OCR accuracy")
    ocr.add_argument(
        "--ocr-language", default="hin+eng", metavar="LANG",
        help="Tesseract languages (default: hin+eng). Use 'hin' alone for "
             "Hindi-only scans: it measured 0.006 character error rate "
             "against 0.026 for hin+eng. Use it for a mixed or English "
             "document and the English is rendered as Devanagari nonsense.")
    ocr.add_argument("--no-ocr", action="store_true",
                     help="never OCR image-only pages")
    ocr.add_argument("--enhance-ocr", action="store_true",
                     help="clean up images first (needs the [ocr] extra)")
    ocr.add_argument("--no-deskew", action="store_true",
                     help="with --enhance-ocr, do not straighten pages")
    ocr.add_argument("--binarise", action="store_true",
                     help="with --enhance-ocr, output black and white. Off by "
                          "default: it measured worse for Tesseract")

    parser.add_argument("--quiet", "-q", action="store_true", help="no banner")
    parser.add_argument("--version", action="version",
                        version=f"krutiextract {__version__}")
    args = parser.parse_args(argv)

    style = _Style(sys.stdout)
    if not args.quiet:
        has_ocr = ocr_available()
        print(style.cyan(BANNER))
        print(f"  {style.bold('KrutiExtract ' + __version__)}   "
              f"OCR {style.green('available') if has_ocr else style.red('unavailable')}\n")

    started = time.monotonic()
    done = failed = 0

    if args.input:
        out = args.output or os.path.splitext(args.input)[0] + ".md"
        if _process(args.input, out, args, style):
            done += 1
        else:
            failed += 1

    elif args.dir:
        out_dir = args.out_dir or args.dir
        pdfs = [
            (root, name)
            for root, _, files in os.walk(args.dir)
            for name in sorted(files)
            if name.lower().endswith(".pdf")
        ]
        if not pdfs:
            print(f"No PDFs found under {args.dir}", file=sys.stderr)
            return 1
        total = len(pdfs)
        width = len(str(total))
        for i, (root, name) in enumerate(pdfs, 1):
            rel = os.path.relpath(root, args.dir)
            target_dir = out_dir if rel == "." else os.path.join(out_dir, rel)
            out = os.path.join(target_dir, os.path.splitext(name)[0] + ".md")
            label = f"[{i:>{width}}/{total}] "
            if _process(os.path.join(root, name), out, args, style, label):
                done += 1
            else:
                failed += 1
    else:
        parser.print_help()
        return 1

    if not args.quiet and (done + failed) > 1:
        summary = f"{done + failed} files   {done} converted"
        if failed:
            summary += f"   {style.red(str(failed) + ' failed')}"
        print(f"\n{summary}   {_human(time.monotonic() - started)}")
    if failed:
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
