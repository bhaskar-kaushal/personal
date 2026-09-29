"""Cross-check Pillow-based resize/warp against the OpenCV defaults they replace."""

import cv2
import numpy as np
import pytest

from face_verification.alignment import (
    ARCFACE_TEMPLATE_112,
    align_face,
    estimate_similarity_transform,
    warp_affine_with_cv2,
)
from face_verification.detection import resize_with_cv2
from face_verification.pillow_ops import resize_with_pillow, warp_affine_with_pillow


def _photo_like_image(height=200, width=300):
    # Smooth gradients, like a real photo, rather than per-pixel noise: bilinear
    # resamplers only agree closely when neighbouring pixels are correlated, and
    # comparing them on adversarial noise would just measure that, not correctness.
    y, x = np.mgrid[0:height, 0:width]
    r = (x * 255 / width).astype(np.uint8)
    g = (y * 255 / height).astype(np.uint8)
    b = (((x + y) * 255 / (width + height))).astype(np.uint8)
    return np.stack([b, g, r], axis=-1)


def test_pillow_resize_matches_cv2_closely():
    image = _photo_like_image()

    cv2_result = resize_with_cv2(image, (120, 80))
    pillow_result = resize_with_pillow(image, (120, 80))

    assert pillow_result.shape == cv2_result.shape
    # Different bilinear implementations (edge handling, rounding) won't match
    # exactly; a small mean absolute difference confirms it's the same resize.
    assert np.abs(pillow_result.astype(np.int32) - cv2_result.astype(np.int32)).mean() < 5.0


def test_pillow_warp_matches_cv2_closely():
    image = _photo_like_image(400, 400)
    landmarks = ARCFACE_TEMPLATE_112 * 2.0 + np.array([50.0, 30.0], np.float32)

    cv2_result = align_face(image, landmarks, warp=warp_affine_with_cv2)
    pillow_result = align_face(image, landmarks, warp=warp_affine_with_pillow)

    assert pillow_result.shape == cv2_result.shape == (112, 112, 3)
    assert np.abs(pillow_result.astype(np.int32) - cv2_result.astype(np.int32)).mean() < 5.0


def test_pillow_warp_recovers_known_transform():
    matrix = estimate_similarity_transform(
        ARCFACE_TEMPLATE_112 * 2.0 + np.array([50.0, 30.0], np.float32), ARCFACE_TEMPLATE_112
    )
    image = np.zeros((400, 400, 3), np.uint8)
    src_point = (ARCFACE_TEMPLATE_112[2] * 2.0 + np.array([50.0, 30.0])).round().astype(int)
    image[src_point[1] - 3 : src_point[1] + 4, src_point[0] - 3 : src_point[0] + 4] = 255

    warped = warp_affine_with_pillow(image, matrix, (112, 112))

    template_x, template_y = np.round(ARCFACE_TEMPLATE_112[2]).astype(int)
    assert warped[template_y, template_x].min() > 200
