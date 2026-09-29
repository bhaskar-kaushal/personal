"""Tests for enrollment persistence."""

from datetime import datetime, timezone

import numpy as np
import pytest

from face_verification.gallery import EnrollmentSample, FileEnrollmentStore

WHEN = datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc)


def _sample(vector, source="a.jpg"):
    v = np.asarray(vector, np.float32)
    return EnrollmentSample(v / np.linalg.norm(v), WHEN, source)


def test_round_trip_and_append(tmp_path):
    store = FileEnrollmentStore(tmp_path)
    store.add_samples("alice", [_sample([1, 0, 0], "a1.jpg")])
    store.add_samples("alice", [_sample([0, 1, 0], "a2.jpg")])

    record = FileEnrollmentStore(tmp_path).get("alice")

    assert [s.source for s in record.samples] == ["a1.jpg", "a2.jpg"]
    assert record.samples[0].enrolled_at == WHEN
    np.testing.assert_allclose(record.samples[1].embedding, [0, 1, 0])
    assert store.list_ids() == ["alice"]
    assert not list(tmp_path.glob("*.tmp"))


def test_template_is_normalised_mean(tmp_path):
    store = FileEnrollmentStore(tmp_path)
    record = store.add_samples("bob", [_sample([1, 0]), _sample([0, 1])])

    np.testing.assert_allclose(record.template(), [np.sqrt(0.5), np.sqrt(0.5)], atol=1e-6)


def test_unknown_person_returns_none(tmp_path):
    assert FileEnrollmentStore(tmp_path).get("nobody") is None


@pytest.mark.parametrize("bad_id", ["../etc", "a/b", "", ".hidden", "x" * 129])
def test_rejects_unsafe_person_ids(tmp_path, bad_id):
    with pytest.raises(ValueError):
        FileEnrollmentStore(tmp_path).add_samples(bad_id, [_sample([1, 0])])
