"""Tests for enrollment and verification orchestration."""

from datetime import datetime, timezone

import numpy as np
import pytest

from face_verification.encoder import FaceEncoder
from face_verification.gallery import FileEnrollmentStore
from face_verification.pipeline import NoFaceDetectedError, VerificationPipeline
from face_verification.verification import ThresholdVerifier, VerificationStatus
from tests.conftest import PixelEmbedder, StubDetector, face_at

WHEN = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _image(bgr):
    return np.full((300, 300, 3), bgr, np.uint8)


def _pipeline(tmp_path, detector, threshold=0.99):
    return VerificationPipeline(
        FaceEncoder(detector, PixelEmbedder()),
        FileEnrollmentStore(tmp_path),
        ThresholdVerifier(threshold),
        clock=lambda: WHEN,
    )


def test_same_appearance_matches_and_different_does_not(tmp_path):
    pipeline = _pipeline(tmp_path, StubDetector([face_at(50, 50)]))
    pipeline.enroll("alice", [("a.jpg", _image((200, 20, 20)))])

    same = pipeline.verify("alice", _image((200, 20, 20)))
    other = pipeline.verify("alice", _image((20, 20, 200)))

    assert same.status is VerificationStatus.MATCH and same.score == pytest.approx(1.0)
    assert other.status is VerificationStatus.NO_MATCH and other.score < 0.99


def test_not_enrolled_is_reported(tmp_path):
    result = _pipeline(tmp_path, StubDetector([face_at(50, 50)])).verify("ghost", _image(0))

    assert result.status is VerificationStatus.NOT_ENROLLED and result.score is None


def test_no_face_is_reported(tmp_path):
    enrolled = _pipeline(tmp_path, StubDetector([face_at(50, 50)]))
    enrolled.enroll("alice", [("a.jpg", _image(100))])

    result = _pipeline(tmp_path, StubDetector([])).verify("alice", _image(100))

    assert result.status is VerificationStatus.NO_FACE and result.score is None


def test_enrollment_without_face_stores_nothing(tmp_path):
    pipeline = _pipeline(tmp_path, StubDetector([]))

    with pytest.raises(NoFaceDetectedError):
        pipeline.enroll("alice", [("a.jpg", _image(100))])
    assert FileEnrollmentStore(tmp_path).get("alice") is None


def test_largest_face_is_used(tmp_path):
    image = np.zeros((400, 400, 3), np.uint8)
    image[0:60, 0:60] = (0, 0, 255)
    image[100:400, 100:400] = (255, 0, 0)
    small, large = face_at(0, 0, size=60), face_at(100, 100, size=300)
    pipeline = _pipeline(tmp_path, StubDetector([small, large]))
    pipeline.enroll("alice", [("blue.jpg", np.full((400, 400, 3), (255, 0, 0), np.uint8))])

    assert pipeline.verify("alice", image).status is VerificationStatus.MATCH
