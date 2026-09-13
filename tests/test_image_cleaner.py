# -*- coding: utf-8 -*-
"""Tests for the image measurements that drive the OCR decisions.

Each heuristic is checked against an image whose defect is known by
construction, because these numbers decide whether a page gets upscaled,
denoised or left alone.
"""

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from src.image_cleaner import (  # noqa: E402
    OpenCVMissing,
    _blockiness,
    _blur_score,
    _deskew,
    _estimate_text_height,
    _noise_score,
    _remove_background,
    _sauvola,
    _uneven_lighting,
    enhance_image,
    enhance_pdf_images,
    opencv_available,
)

WORDS = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dogs",
    "while", "reading", "many", "books", "today", "near", "a", "river",
]


def text_page(height=300, width=620, scale=0.7, rows=8):
    """A page of anti-aliased rendered words.

    Hard black bars are not a usable stand-in: their sharp edges land on the
    8-pixel JPEG grid and give a blockiness of 7 against 1.0 for real text,
    which would defeat the very gate under test.
    """
    img = np.full((height, width), 255, np.uint8)
    y = 30
    for r in range(rows):
        line = " ".join(WORDS[(r * 3) % len(WORDS):][:7]) or "sample text"
        cv2.putText(img, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, scale,
                    (0,), 1, cv2.LINE_AA)
        y += int(34 * scale) + 10
    return img


def small_page():
    return text_page(height=150, width=310, scale=0.32, rows=6)


def test_opencv_is_available_here():
    assert opencv_available() is True


def test_blur_score_drops_when_blurred():
    page = text_page()
    assert _blur_score(cv2.GaussianBlur(page, (0, 0), 3)) < _blur_score(page) / 10


def test_noise_score_rises_with_noise():
    page = text_page()
    rng = np.random.default_rng(0)
    noisy = np.clip(page.astype(float) + rng.normal(0, 25, page.shape), 0, 255)
    assert _noise_score(noisy.astype(np.uint8)) > _noise_score(page)


def test_uneven_lighting_rises_with_a_gradient():
    page = text_page()
    _, xx = np.mgrid[0:page.shape[0], 0:page.shape[1]]
    washed = np.clip(page.astype(float) * (0.4 + 0.6 * xx / page.shape[1]), 0, 255)
    assert _uneven_lighting(washed.astype(np.uint8)) > _uneven_lighting(page)


def test_blockiness_rises_with_jpeg_compression():
    page = text_page()
    _, buf = cv2.imencode(".jpg", page, [cv2.IMWRITE_JPEG_QUALITY, 10])
    jpeg = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
    assert _blockiness(jpeg) > _blockiness(page)


def test_blockiness_is_zero_for_a_sliver():
    assert _blockiness(np.full((4, 8), 255, np.uint8)) == 0.0


def test_estimate_text_height_matches_the_drawn_glyphs():
    assert 8 <= _estimate_text_height(text_page()) <= 22


def test_estimate_text_height_on_a_blank_page():
    assert _estimate_text_height(np.full((50, 50), 255, np.uint8)) == 0.0


def test_remove_background_flattens_a_wash_but_keeps_the_text():
    page = text_page()
    _, xx = np.mgrid[0:page.shape[0], 0:page.shape[1]]
    washed = np.clip(page.astype(float) * (0.4 + 0.6 * xx / page.shape[1]),
                     0, 255).astype(np.uint8)
    fixed = _remove_background(washed)
    assert _uneven_lighting(fixed) < _uneven_lighting(washed)
    assert fixed.min() < 128          # the strokes survive


def test_deskew_finds_a_known_rotation():
    page = text_page()
    h, w = page.shape
    matrix = cv2.getRotationMatrix2D((w / 2, h / 2), 3.0, 1.0)
    tilted = cv2.warpAffine(page, matrix, (w, h), borderValue=255)
    _, angle = _deskew(tilted)
    assert abs(angle) > 0.25


def test_deskew_leaves_straight_text_alone():
    _, angle = _deskew(text_page())
    assert angle == 0.0


def test_deskew_ignores_an_almost_empty_image():
    out, angle = _deskew(np.full((40, 40), 255, np.uint8))
    assert angle == 0.0 and out.shape == (40, 40)


def test_sauvola_returns_two_tone_output():
    assert set(np.unique(_sauvola(text_page()))) <= {0, 255}


def test_enhance_image_returns_grayscale_by_default():
    """Binarising measured worse for Tesseract, so it is not the default."""
    out = enhance_image(text_page())
    assert out.ndim == 2
    assert len(np.unique(out)) > 2


def test_enhance_image_can_binarise_on_request():
    assert set(np.unique(enhance_image(text_page(), binarise=True))) <= {0, 255}


def test_enhance_image_accepts_colour():
    colour = cv2.cvtColor(text_page(), cv2.COLOR_GRAY2RGB)
    assert enhance_image(colour).ndim == 2


def test_small_sharp_text_is_upscaled():
    small = small_page()
    assert enhance_image(small, deskew=False).shape[0] > small.shape[0]


def test_blurred_text_is_not_upscaled():
    """Enlarging a soft scan magnifies the halo: measured CER 0.702 -> 0.724."""
    blurred = cv2.GaussianBlur(small_page(), (0, 0), 3)
    assert enhance_image(blurred, deskew=False).shape == blurred.shape


def test_explicit_flags_override_the_measurements():
    """A caller can force a stage on, or off, against the measurement."""
    page = text_page()
    _, xx = np.mgrid[0:page.shape[0], 0:page.shape[1]]
    washed = np.clip(page.astype(float) * (0.4 + 0.6 * xx / page.shape[1]),
                     0, 255).astype(np.uint8)

    # Forced off: the wash survives even though the measurement asks for it.
    left_alone = enhance_image(washed, remove_background=False, denoise=False,
                               deskew=False)
    # Forced on: the wash is flattened.
    cleaned = enhance_image(washed, remove_background=True, denoise=False,
                            deskew=False)
    assert _uneven_lighting(cleaned) < _uneven_lighting(left_alone)


def test_enhance_pdf_images_replaces_images(tmp_path):
    import pymupdf
    page_img = text_page()
    ok, buf = cv2.imencode(".png", page_img)
    assert ok
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_image(pymupdf.Rect(20, 20, 300, 200), stream=buf.tobytes())
    src = str(tmp_path / "img.pdf")
    doc.save(src)
    doc.close()

    out = str(tmp_path / "out.pdf")
    assert enhance_pdf_images(src, out) >= 1
    assert pymupdf.open(out).page_count == 1


def test_enhance_pdf_images_on_a_pdf_with_no_images(tmp_path):
    import pymupdf
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "text only")
    src = str(tmp_path / "plain.pdf")
    doc.save(src)
    doc.close()
    out = str(tmp_path / "plain_out.pdf")
    assert enhance_pdf_images(src, out) == 0


def test_missing_opencv_raises_a_helpful_error(monkeypatch):
    import builtins

    import src.image_cleaner as cleaner
    real_import = builtins.__import__

    def no_cv2(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("no cv2")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_cv2)
    with pytest.raises(OpenCVMissing, match="krutiextract\\[ocr\\]"):
        cleaner._cv()
    assert cleaner.opencv_available() is False
