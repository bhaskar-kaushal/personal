"""Tests for enrollment and verification orchestration."""

from datetime import datetime, timezone

import numpy as np
import pytest

from face_verification.encoder import FaceEncoder
from face_verification.gallery import FileEnrollmentStore
from face_verification.pipeline import NoFaceDetectedError, VerificationPipeline
from face_verification.verification import (
    IdentificationStatus,
    ThresholdVerifier,
    VerificationStatus,
)
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


def test_identify_reports_empty_gallery(tmp_path):
    result = _pipeline(tmp_path, StubDetector([face_at(50, 50)])).identify(_image(100))

    assert result.status is IdentificationStatus.EMPTY_GALLERY
    assert result.person_id is None and result.score is None and result.num_candidates == 0


def test_identify_reports_no_face(tmp_path):
    enrolled = _pipeline(tmp_path, StubDetector([face_at(50, 50)]))
    enrolled.enroll("alice", [("a.jpg", _image((200, 20, 20)))])

    result = _pipeline(tmp_path, StubDetector([])).identify(_image((200, 20, 20)))

    assert result.status is IdentificationStatus.NO_FACE
    assert result.person_id is None and result.num_candidates == 1


def test_identify_finds_best_match_across_gallery(tmp_path):
    detector = StubDetector([face_at(50, 50)])
    pipeline = _pipeline(tmp_path, detector, threshold=0.99)
    pipeline.enroll("alice", [("a.jpg", _image((200, 20, 20)))])
    pipeline.enroll("bob", [("b.jpg", _image((20, 200, 20)))])
    pipeline.enroll("carol", [("c.jpg", _image((20, 20, 200)))])

    result = pipeline.identify(_image((20, 200, 20)))

    assert result.status is IdentificationStatus.MATCH
    assert result.person_id == "bob" and result.score == pytest.approx(1.0)
    assert result.num_candidates == 3


def test_identify_no_match_when_best_score_below_threshold(tmp_path):
    detector = StubDetector([face_at(50, 50)])
    pipeline = _pipeline(tmp_path, detector, threshold=0.99)
    pipeline.enroll("alice", [("a.jpg", _image((200, 20, 20)))])

    result = pipeline.identify(_image((20, 20, 200)))

    assert result.status is IdentificationStatus.NO_MATCH
    assert result.person_id == "alice"  # best (only) candidate is still reported for audit
    assert result.score < 0.99
