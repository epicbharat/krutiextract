# -*- coding: utf-8 -*-
"""PDF -> Markdown, preserving the logical character stream.

pymupdf4llm has two back ends. The layout back end accepts OCR options; the
legacy back end takes ``**kwargs`` and silently discards them. The original
code passed ``ocr_language="hin"`` unconditionally, so on any install without
the layout engine OCR simply never ran and nothing said so.
"""

import contextlib
import inspect
import io
import warnings as _warnings
from typing import List, Optional, Sequence

__all__ = ["extract_raw_markdown", "ocr_available", "ExtractionError"]


class ExtractionError(RuntimeError):
    """Raised when a PDF cannot be read. Never swallowed into None."""


_OCR_KWARGS = ("use_ocr", "ocr_language", "ocr_dpi")


@contextlib.contextmanager
def _captured_messages(buffer):
    """Send PyMuPDF's message channel to *buffer* for the duration."""
    try:
        import pymupdf
    except ImportError:
        yield
        return
    set_messages = getattr(pymupdf, "set_messages", None)
    if set_messages is None:
        with contextlib.redirect_stdout(buffer):
            yield
        return
    try:
        set_messages(stream=buffer)
        with contextlib.redirect_stdout(buffer), _warnings.catch_warnings():
            # pymupdf4llm's OCR feature code divides by an empty slice on
            # blank regions. Its warning, not ours, and it is harmless.
            _warnings.simplefilter("ignore", RuntimeWarning)
            yield
    finally:
        try:
            set_messages(fd=2)
        except Exception:
            pass


def _layout_backend_active() -> bool:
    """True when the pymupdf4llm back end in use honours the OCR options."""
    try:
        import pymupdf4llm
    except ImportError as exc:                      # pragma: no cover
        raise ExtractionError("pymupdf4llm is not installed") from exc

    if getattr(pymupdf4llm, "_use_layout", None):
        return True

    # Older releases: the OCR options are real parameters, not **kwargs.
    try:
        import pymupdf4llm.helpers.pymupdf_rag as rag
        params = inspect.signature(rag.to_markdown).parameters
        return "ocr_language" in params
    except Exception:
        return False


def ocr_available() -> bool:
    """Whether this install can OCR image-only pages."""
    try:
        return _layout_backend_active()
    except ExtractionError:
        return False


def extract_raw_markdown(
    pdf_path: str,
    ocr: bool = True,
    ocr_language: str = "hin",
    ocr_dpi: int = 400,
    pages: Optional[Sequence[int]] = None,
    warnings: Optional[List[str]] = None,
) -> str:
    """Extract *pdf_path* as Markdown.

    Raises ExtractionError rather than returning None, so a failed file is
    never silently written out as an empty document.
    """
    try:
        import pymupdf4llm
    except ImportError as exc:
        raise ExtractionError("pymupdf4llm is not installed") from exc

    kwargs = {"force_text": True}
    if pages is not None:
        kwargs["pages"] = list(pages)

    if ocr:
        if _layout_backend_active():
            kwargs.update(use_ocr=True, ocr_language=ocr_language, ocr_dpi=ocr_dpi)
        elif warnings is not None:
            warnings.append(
                "OCR requested but this pymupdf4llm build has no layout back end; "
                "image-only pages will come out empty. Install a build that "
                "provides pymupdf_layout, or pass --no-ocr to silence this."
            )

    # pymupdf4llm writes a "Document parser messages" block through PyMuPDF's
    # own message channel, which bypasses sys.stdout. Point that channel at a
    # buffer so it does not land in the middle of the CLI output, and surface
    # it only if it mentions a problem.
    chatter = io.StringIO()

    try:
        with _captured_messages(chatter):
            text = pymupdf4llm.to_markdown(pdf_path, **kwargs)
    except TypeError:
        # Back end older than the OCR options: retry without them.
        for key in _OCR_KWARGS:
            kwargs.pop(key, None)
        try:
            with _captured_messages(chatter):
                text = pymupdf4llm.to_markdown(pdf_path, **kwargs)
        except Exception as exc:
            raise ExtractionError(f"{pdf_path}: {exc}") from exc
    except Exception as exc:
        raise ExtractionError(f"{pdf_path}: {exc}") from exc

    if warnings is not None:
        noise = chatter.getvalue()
        for line in noise.splitlines():
            if any(w in line.lower() for w in ("error", "warning", "cannot", "fail")):
                warnings.append(line.strip())

    if text is None:
        raise ExtractionError(f"{pdf_path}: extractor returned no text")
    return text
