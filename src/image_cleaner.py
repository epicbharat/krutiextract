# -*- coding: utf-8 -*-
"""Clean up page and figure images so Tesseract has a better chance.

OpenCV and NumPy are optional and imported lazily, so the CLI still runs with
only the core dependencies installed.

**What the measurements say.** Benchmarked against a Hindi text column from an
NCERT page, rendered at several resolutions and degraded in six ways
(low resolution, blur, Gaussian noise, heavy JPEG, uneven wash, skew), scored
as character error rate against the converted text of that same block:

* Source resolution dominates everything else. At an effective 300 dpi,
  Tesseract reached ~0.5% CER on *every* degradation tested. Below ~100 dpi
  the error rate jumps to 18-27% and no amount of pre-processing recovers it.
* **Binarising before Tesseract makes things worse** (0.216 vs 0.178 mean CER
  at 100 dpi). Modern LSTM Tesseract does its own adaptive thresholding and
  wants grayscale. The previous version of this module handed it a hard
  black-and-white image.
* Sharpening a blurred scan makes it worse (0.702 -> 0.724).
* Upscaling small text helps a little (0.272 -> 0.258 at 75 dpi), denoising
  helps a noisy scan (0.056 -> 0.014), and background division helps a washed
  one (0.042 -> 0.006).

So this module now applies only the operations a measurement of the specific
image indicates, returns grayscale rather than a binary image, and does
nothing at all to an image that is already in good shape. If OCR quality
matters more than anything, raise ``--ocr-dpi`` before reaching for this.
"""

import contextlib
from typing import Optional

__all__ = [
    "enhance_pdf_images",
    "enhance_image",
    "opencv_available",
    "OpenCVMissing",
]


class OpenCVMissing(RuntimeError):
    pass


def _cv():
    try:
        import cv2
        import numpy as np
        with contextlib.suppress(Exception):
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_SILENT)
        return cv2, np
    except ImportError as exc:
        raise OpenCVMissing(
            "image enhancement needs OpenCV and NumPy: "
            "pip install 'krutiextract[ocr]'"
        ) from exc


def opencv_available() -> bool:
    try:
        _cv()
        return True
    except OpenCVMissing:
        return False


# --------------------------------------------------------------------------
# Measurements that drive the automatic decisions
# --------------------------------------------------------------------------

def _blur_score(gray) -> float:
    cv2, _ = _cv()
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _noise_score(gray) -> float:
    """Median absolute deviation between the image and a median-filtered copy."""
    cv2, np = _cv()
    med = cv2.medianBlur(gray, 3)
    return float(np.median(np.abs(gray.astype("int16") - med.astype("int16"))))


def _uneven_lighting(gray) -> float:
    """Spread of local background levels across the page."""
    cv2, _ = _cv()
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    return float(small.std())


def _blockiness(gray) -> float:
    """How much stronger the gradient is across 8-pixel boundaries than within.

    JPEG compresses in 8x8 blocks, so a heavily compressed image has a visible
    grid. Upscaling one magnifies the block edges along with the strokes, which
    measured worse for OCR, so this gates the upscale.
    """
    _, np = _cv()
    g = gray.astype("float32")
    dx = np.abs(np.diff(g, axis=1))
    if dx.shape[1] < 16:
        return 0.0
    on = dx[:, 7::8]
    off = np.delete(dx, np.s_[7::8], axis=1)
    denom = float(off.mean()) or 1.0
    return float(on.mean()) / denom


def _estimate_text_height(binary) -> float:
    """Median height of connected components that look like glyphs."""
    cv2, np = _cv()
    inv = 255 - binary
    n, _, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)
    if n <= 1:
        return 0.0
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    areas = stats[1:, cv2.CC_STAT_AREA]
    keep = heights[(areas > 8) & (heights > 3) & (heights < binary.shape[0] // 4)]
    return float(np.median(keep)) if keep.size else 0.0


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------

def _remove_background(gray, strength: int = 31):
    """Divide out a smooth background: shading, bleed-through, watermarks."""
    cv2, _ = _cv()
    k = max(3, strength | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    background = cv2.GaussianBlur(background, (0, 0), k / 3.0)
    normalised = cv2.divide(gray, background, scale=255)
    return normalised


def _deskew(binary, max_angle: float = 8.0):
    cv2, np = _cv()
    coords = np.column_stack(np.where(binary < 128))
    if coords.shape[0] < 50:
        return binary, 0.0
    angle = cv2.minAreaRect(coords.astype("float32"))[-1]
    if angle < -45:
        angle += 90
    if angle > 45:
        angle -= 90
    if abs(angle) < 0.25 or abs(angle) > max_angle:
        return binary, 0.0
    h, w = binary.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    rotated = cv2.warpAffine(binary, matrix, (w, h),
                             flags=cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REPLICATE)
    return rotated, angle


def _sauvola(gray, window: int = 31, k: float = 0.2):
    """Local thresholding for pages with uneven lighting."""
    cv2, np = _cv()
    win = max(3, window | 1)
    img = gray.astype("float32")
    mean = cv2.boxFilter(img, cv2.CV_32F, (win, win))
    sq = cv2.boxFilter(img * img, cv2.CV_32F, (win, win))
    std = cv2.sqrt(cv2.max(sq - mean * mean, 0))
    threshold = mean * (1.0 + k * ((std / 128.0) - 1.0))
    return np.where(img > threshold, 255, 0).astype("uint8")


def enhance_image(
    image,
    target_text_height: int = 34,
    min_text_height: int = 13,
    max_scale: float = 4.0,
    remove_background: Optional[bool] = None,
    denoise: Optional[bool] = None,
    deskew: bool = True,
    binarise: bool = False,
):
    """Enhance one image for OCR. Returns **grayscale** unless binarise=True.

    Each stage is applied only when a measurement of this image indicates it.
    Pass an explicit True/False to override a decision.

    binarise defaults to False on purpose: measured over six degradations it
    raised mean CER from 0.178 to 0.216. It is kept as an option for callers
    feeding something other than Tesseract.
    """
    cv2, _ = _cv()

    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    if remove_background is None:
        remove_background = _uneven_lighting(gray) > 28
    if remove_background:
        gray = _remove_background(gray)

    if denoise is None:
        # Mild noise does not bother Tesseract, and denoising it measured
        # worse (0.006 -> 0.018). Only act on noise that actually damages.
        denoise = _noise_score(gray) > 4.0
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, None, h=7,
                                        templateWindowSize=7, searchWindowSize=21)

    # Otsu here only to measure glyph height, not as output.
    _, probe = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text_height = _estimate_text_height(probe)
    # Upscale only genuinely small *and* sharp text. Enlarging a soft scan
    # magnifies the halo with the stroke and measured worse (0.545 -> 0.595).
    # A Laplacian variance this low means the detail is already gone.
    sharp_enough = _blur_score(gray) > 400 and _blockiness(gray) < 1.20
    if sharp_enough and text_height and text_height < min_text_height:
        scale = min(max_scale, target_text_height / text_height)
        if scale > 1.05:
            gray = cv2.resize(gray, None, fx=scale, fy=scale,
                              interpolation=cv2.INTER_LANCZOS4)

    # No unsharp mask. Measured on a blurred scan it made OCR worse
    # (CER 0.702 -> 0.724): it amplifies the halo as readily as the stroke.

    if deskew:
        _, probe = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, angle = _deskew(probe)
        if angle:
            h, w = gray.shape
            matrix = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            gray = cv2.warpAffine(gray, matrix, (w, h), flags=cv2.INTER_CUBIC,
                                  borderMode=cv2.BORDER_REPLICATE)

    if binarise:
        if _uneven_lighting(gray) > 28:
            return _sauvola(gray)
        _, out = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return out

    return gray


def _image_array(doc, xref, np):
    """One embedded image as an HxW or HxWx3 uint8 array, or None."""
    import pymupdf

    try:
        pix = pymupdf.Pixmap(doc, xref)
    except Exception:
        return None
    try:
        if pix.alpha or pix.n > 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        if pix.n not in (1, 3):
            return None
        data = np.frombuffer(pix.samples, dtype=np.uint8)
        expected = pix.height * pix.width * pix.n
        if data.size != expected:
            return None
        shape = (pix.height, pix.width) if pix.n == 1 else (pix.height, pix.width, 3)
        return data.reshape(shape)
    except Exception:
        return None


def enhance_pdf_images(
    input_path: str,
    output_path: str,
    **options,
) -> int:
    """Rewrite *input_path* to *output_path* with every image enhanced.

    Returns the number of images replaced.
    """
    import pymupdf

    cv2, np = _cv()
    doc = pymupdf.open(input_path)
    replaced = 0

    try:
        for page in doc:
            for info in page.get_images(full=True):
                xref = info[0]
                # Decode through PyMuPDF, not cv2.imdecode: OpenCV has no
                # JPEG2000 support in the headless wheel and logs a C++ error
                # straight to stderr for every JPX image in the file.
                img = _image_array(doc, xref, np)
                if img is None or min(img.shape[:2]) < 16:
                    continue

                try:
                    out = enhance_image(img, **options)
                except Exception:
                    continue

                ok, buf = cv2.imencode(".png", out)
                if not ok:
                    continue
                stream = buf.tobytes()

                # replace_image swaps the object in place. Inserting a second
                # image over the first, as the old code did, left both in the
                # file and inflated it.
                try:
                    page.replace_image(xref, stream=stream)
                    replaced += 1
                    continue
                except Exception:
                    pass

                for rect in page.get_image_rects(xref):
                    page.insert_image(rect, stream=stream, keep_proportion=False)
                    replaced += 1

        doc.save(output_path, garbage=3, deflate=True)
    finally:
        doc.close()

    return replaced
