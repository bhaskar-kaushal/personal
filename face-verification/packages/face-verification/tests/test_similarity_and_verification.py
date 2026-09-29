"""Tests for similarity metrics and threshold decisions."""

import numpy as np
import pytest

from face_verification.similarity import cosine_similarity, l2_normalize
from face_verification.verification import (
    IdentificationResult,
    IdentificationStatus,
    ThresholdVerifier,
    VerificationResult,
    VerificationStatus,
)


def test_cosine_similarity_bounds():
    v = np.array([1.0, 2.0, 3.0])

    assert cosine_similarity(v, 5 * v) == pytest.approx(1.0)
    assert cosine_similarity(v, -v) == pytest.approx(-1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_similarity_rejects_dimension_mismatch():
    with pytest.raises(ValueError):
        cosine_similarity([1, 0], [1, 0, 0])


def test_l2_normalize_rejects_zero_vector():
    with pytest.raises(ValueError):
        l2_normalize(np.zeros(4))


def test_threshold_is_inclusive():
    verifier = ThresholdVerifier(0.4)

    assert verifier.decide(0.4) is VerificationStatus.MATCH
    assert verifier.decide(0.3999) is VerificationStatus.NO_MATCH
    assert verifier.accepts(0.4) and not verifier.accepts(0.3999)


@pytest.mark.parametrize("threshold", [-1.1, 1.01])
def test_threshold_out_of_range_rejected(threshold):
    with pytest.raises(ValueError):
        ThresholdVerifier(threshold)


def test_result_serialises():
    result = VerificationResult("alice", VerificationStatus.MATCH, 0.71234567, 0.4)

    assert result.is_verified
    assert result.to_dict() == {
        "person_id": "alice",
        "status": "match",
        "verified": True,
        "score": 0.712346,
        "threshold": 0.4,
    }


def test_identification_result_serialises():
    match = IdentificationResult(IdentificationStatus.MATCH, "alice", 0.9123456, 0.4, 5)
    empty = IdentificationResult(IdentificationStatus.EMPTY_GALLERY, None, None, 0.4, 0)

    assert match.is_identified
    assert match.to_dict() == {
        "status": "match",
        "identified": True,
        "person_id": "alice",
        "score": 0.912346,
        "threshold": 0.4,
        "num_candidates": 5,
    }
    assert not empty.is_identified
    assert empty.to_dict()["person_id"] is None and empty.to_dict()["score"] is None
