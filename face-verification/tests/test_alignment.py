"""Tests for landmark alignment."""

import numpy as np
import pytest

from face_verification.alignment import (
    ALIGNED_FACE_SIZE,
    ARCFACE_TEMPLATE_112,
    align_face,
    estimate_similarity_transform,
)


def _apply(matrix: np.ndarray, points: np.ndarray) -> np.ndarray:
    return points @ matrix[:, :2].T + matrix[:, 2]


def test_template_to_itself_is_identity():
    matrix = estimate_similarity_transform(ARCFACE_TEMPLATE_112, ARCFACE_TEMPLATE_112)

    np.testing.assert_allclose(matrix, [[1, 0, 0], [0, 1, 0]], atol=1e-5)


def test_recovers_known_similarity_transform():
    angle = np.deg2rad(17.0)
    scale = 2.3
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    translation = np.array([140.0, -35.0])
    landmarks = (ARCFACE_TEMPLATE_112 @ (scale * rotation).T) + translation

    matrix = estimate_similarity_transform(landmarks, ARCFACE_TEMPLATE_112)

    np.testing.assert_allclose(_apply(matrix, landmarks), ARCFACE_TEMPLATE_112, atol=1e-3)


def test_rejects_degenerate_points():
    with pytest.raises(ValueError):
        estimate_similarity_transform(np.zeros((5, 2)), ARCFACE_TEMPLATE_112)


def test_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        estimate_similarity_transform(ARCFACE_TEMPLATE_112[:4], ARCFACE_TEMPLATE_112)


def test_align_face_moves_marked_landmark_to_template():
    image = np.zeros((400, 400, 3), np.uint8)
    offset = np.array([150.0, 120.0], np.float32)
    landmarks = ARCFACE_TEMPLATE_112 * 2.0 + offset
    nose_x, nose_y = np.round(landmarks[2]).astype(int)
    image[nose_y - 3 : nose_y + 4, nose_x - 3 : nose_x + 4] = 255

    aligned = align_face(image, landmarks)

    assert aligned.shape == (ALIGNED_FACE_SIZE, ALIGNED_FACE_SIZE, 3)
    template_x, template_y = np.round(ARCFACE_TEMPLATE_112[2]).astype(int)
    assert aligned[template_y, template_x].min() > 200
