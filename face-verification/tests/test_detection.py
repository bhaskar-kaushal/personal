"""Tests for SCRFD decoding and NMS."""

import numpy as np
import pytest

from face_verification.detection import ScrfdDetector, non_max_suppression
from tests.conftest import FakeSession

INPUT_SIZE = (64, 64)
STRIDES = (8, 16, 32)


def _empty_outputs():
    width, height = INPUT_SIZE
    counts = [(height // s) * (width // s) * 2 for s in STRIDES]
    scores = [np.zeros((n, 1), np.float32) for n in counts]
    boxes = [np.zeros((n, 4), np.float32) for n in counts]
    keypoints = [np.zeros((n, 10), np.float32) for n in counts]
    return scores + boxes + keypoints


def test_decodes_single_anchor_into_source_coordinates():
    outputs = _empty_outputs()
    # Stride 8 grid is 8x8; anchor index 2*(row*8+col)+1 -> row=2, col=3, centre (24, 16).
    index = 2 * (2 * 8 + 3) + 1
    outputs[0][index, 0] = 0.95
    outputs[3][index] = [1.0, 1.0, 2.0, 2.0]
    outputs[6][index] = np.tile([0.5, -0.5], 5)
    session = FakeSession(outputs)
    detector = ScrfdDetector(session, input_size=INPUT_SIZE)
    image = np.zeros((128, 128, 3), np.uint8)  # scale factor 0.5 into the 64x64 input

    faces = detector.detect(image)

    assert len(faces) == 1
    np.testing.assert_allclose(faces[0].bbox, [32, 16, 80, 64])
    np.testing.assert_allclose(faces[0].landmarks, np.tile([56.0, 24.0], (5, 1)))
    assert faces[0].score == pytest.approx(0.95)


def test_preprocess_produces_normalised_nchw_blob():
    session = FakeSession(_empty_outputs())
    detector = ScrfdDetector(session, input_size=INPUT_SIZE)

    detector.detect(np.full((32, 64, 3), 255, np.uint8))

    blob = session.inputs_seen[0]["input.1"]
    assert blob.shape == (1, 3, 64, 64)
    assert blob[0, :, 0, 0] == pytest.approx((255 - 127.5) / 128.0)
    assert blob[0, :, -1, 0] == pytest.approx(-127.5 / 128.0)  # letterbox padding


def test_returns_empty_when_nothing_above_threshold():
    detector = ScrfdDetector(FakeSession(_empty_outputs()), input_size=INPUT_SIZE)

    assert detector.detect(np.zeros((64, 64, 3), np.uint8)) == []


def test_rejects_model_without_keypoint_outputs():
    with pytest.raises(ValueError):
        ScrfdDetector(FakeSession([], num_outputs=6))


def test_nms_suppresses_overlapping_lower_score_box():
    boxes = np.array([[0, 0, 10, 10], [1, 1, 11, 11], [50, 50, 60, 60]], np.float32)
    scores = np.array([0.8, 0.9, 0.7], np.float32)

    assert non_max_suppression(boxes, scores, iou_threshold=0.4) == [1, 2]
