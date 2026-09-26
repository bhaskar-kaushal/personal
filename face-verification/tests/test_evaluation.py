"""Tests for evaluation metrics and calibration."""

import numpy as np
import pytest

from face_verification.evaluation import (
    equal_error_rate,
    error_rates,
    evaluate,
    pairwise_scores,
    threshold_for_far,
)

GENUINE = [0.9, 0.8, 0.7, 0.35]
IMPOSTOR = [0.1, 0.2, 0.3, 0.45, 0.05]


def test_error_rates_at_threshold():
    rates = error_rates(GENUINE, IMPOSTOR, 0.4)

    assert rates.far == pytest.approx(1 / 5)
    assert rates.frr == pytest.approx(1 / 4)


def test_eer_zero_for_separated_scores():
    rates = equal_error_rate([0.8, 0.9], [0.1, 0.2])

    assert rates.far == 0.0 and rates.frr == 0.0
    assert 0.2 < rates.threshold <= 0.8


def test_threshold_for_far_zero_sits_just_above_max_impostor():
    threshold = threshold_for_far(IMPOSTOR, 0.0)

    assert threshold > 0.45
    assert error_rates(GENUINE, IMPOSTOR, threshold).far == 0.0


def test_threshold_for_far_allows_budget():
    threshold = threshold_for_far(IMPOSTOR, 0.2)

    assert error_rates(GENUINE, IMPOSTOR, threshold).far <= 0.2
    assert threshold == pytest.approx(0.3, abs=1e-9)


def test_threshold_for_far_rejects_bad_target():
    with pytest.raises(ValueError):
        threshold_for_far(IMPOSTOR, 1.5)


def test_pairwise_scores_split():
    embeddings = {
        "a": [np.array([1.0, 0.0]), np.array([1.0, 0.1])],
        "b": [np.array([0.0, 1.0])],
    }

    genuine, impostor = pairwise_scores(embeddings)

    assert genuine.shape == (1,) and genuine[0] > 0.99
    assert impostor.shape == (2,)


def test_evaluate_report():
    rng = np.random.default_rng(0)
    centers = rng.normal(size=(4, 64))
    embeddings = {
        f"p{i}": [c + 0.05 * rng.normal(size=64) for _ in range(3)] for i, c in enumerate(centers)
    }

    report = evaluate(embeddings, threshold=0.5, target_far=0.0).to_dict()

    assert report["num_genuine_pairs"] == 4 * 3
    assert report["num_impostor_pairs"] == 12 * 11 // 2 - 12
    assert report["equal_error"]["far"] == 0.0 and report["equal_error"]["frr"] == 0.0
    assert report["tar_at_target_far"] == 1.0


def test_evaluate_needs_genuine_and_impostor_pairs():
    with pytest.raises(ValueError):
        evaluate({"a": [np.ones(3)]}, threshold=0.5, target_far=0.01)
