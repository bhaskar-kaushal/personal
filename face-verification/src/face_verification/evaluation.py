"""
Verification accuracy metrics and threshold calibration.

Conventions: a score >= threshold is an accept. FAR is the fraction of impostor
pairs accepted; FRR is the fraction of genuine pairs rejected.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import numpy as np

from face_verification.similarity import l2_normalize


@dataclass(frozen=True)
class ErrorRates:
    """FAR and FRR at a threshold."""

    threshold: float
    far: float
    frr: float


def _as_scores(scores: Sequence[float], name: str) -> np.ndarray:
    array = np.sort(np.asarray(scores, dtype=np.float64).ravel())
    if array.size == 0:
        raise ValueError(f"{name} scores are empty")
    return array


def _far(impostor_sorted: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    accepted = impostor_sorted.size - np.searchsorted(impostor_sorted, thresholds, side="left")
    return accepted / impostor_sorted.size


def _frr(genuine_sorted: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    return np.searchsorted(genuine_sorted, thresholds, side="left") / genuine_sorted.size


def error_rates(
    genuine: Sequence[float], impostor: Sequence[float], threshold: float
) -> ErrorRates:
    """
    FAR and FRR at a fixed threshold.

    Args:
        genuine: Same-person similarity scores.
        impostor: Different-person similarity scores.
        threshold: Accept when score >= threshold.

    Returns:
        Error rates at the threshold.
    """
    t = np.array([threshold])
    far = _far(_as_scores(impostor, "impostor"), t)[0]
    frr = _frr(_as_scores(genuine, "genuine"), t)[0]
    return ErrorRates(threshold=float(threshold), far=float(far), frr=float(frr))


def equal_error_rate(genuine: Sequence[float], impostor: Sequence[float]) -> ErrorRates:
    """
    Operating point where FAR and FRR are closest.

    Args:
        genuine: Same-person similarity scores.
        impostor: Different-person similarity scores.

    Returns:
        Error rates at the EER threshold (EER ~= (far + frr) / 2).
    """
    genuine_sorted = _as_scores(genuine, "genuine")
    impostor_sorted = _as_scores(impostor, "impostor")
    candidates = np.unique(np.concatenate([genuine_sorted, impostor_sorted]))
    candidates = np.concatenate([candidates, [np.nextafter(candidates[-1], np.inf)]])
    far = _far(impostor_sorted, candidates)
    frr = _frr(genuine_sorted, candidates)
    best = int(np.argmin(np.abs(far - frr)))
    return ErrorRates(float(candidates[best]), float(far[best]), float(frr[best]))


def threshold_for_far(impostor: Sequence[float], target_far: float) -> float:
    """
    Lowest threshold whose FAR does not exceed target_far.

    Args:
        impostor: Different-person similarity scores.
        target_far: Maximum acceptable false-accept rate in [0, 1].

    Returns:
        Threshold meeting the FAR target on this data.

    Raises:
        ValueError: If target_far is outside [0, 1].
    """
    if not 0.0 <= target_far <= 1.0:
        raise ValueError(f"target_far must be in [0, 1], got {target_far}")
    impostor_sorted = _as_scores(impostor, "impostor")
    # FAR only changes just above each impostor score, so those are the only candidates.
    candidates = np.concatenate(
        [[impostor_sorted[0]], np.nextafter(np.unique(impostor_sorted), np.inf)]
    )
    feasible = candidates[_far(impostor_sorted, candidates) <= target_far]
    return float(feasible.min())


def pairwise_scores(
    embeddings_by_person: Mapping[str, Sequence[np.ndarray]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    All-pairs cosine scores split into genuine and impostor sets.

    Args:
        embeddings_by_person: person id -> embeddings.

    Returns:
        (genuine scores, impostor scores), each over unordered distinct pairs.
    """
    labels: List[str] = []
    vectors: List[np.ndarray] = []
    for person_id, embeddings in embeddings_by_person.items():
        for embedding in embeddings:
            labels.append(person_id)
            vectors.append(l2_normalize(embedding))
    if len(vectors) < 2:
        return np.empty(0), np.empty(0)

    matrix = np.stack(vectors)
    similarities = matrix @ matrix.T
    rows, cols = np.triu_indices(len(vectors), k=1)
    label_array = np.array(labels)
    same_person = label_array[rows] == label_array[cols]
    pair_scores = np.clip(similarities[rows, cols], -1.0, 1.0).astype(np.float64)
    return pair_scores[same_person], pair_scores[~same_person]


@dataclass(frozen=True)
class EvaluationReport:
    """Summary of a verification evaluation run."""

    num_identities: int
    num_embeddings: int
    num_genuine_pairs: int
    num_impostor_pairs: int
    at_threshold: ErrorRates
    equal_error: ErrorRates
    target_far: float
    threshold_at_target_far: float
    tar_at_target_far: float

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable representation."""
        return asdict(self)


def evaluate(
    embeddings_by_person: Mapping[str, Sequence[np.ndarray]],
    threshold: float,
    target_far: float,
) -> EvaluationReport:
    """
    Evaluate verification accuracy over all pairs in a labelled embedding set.

    Args:
        embeddings_by_person: person id -> embeddings (>= 2 people, some with >= 2 samples).
        threshold: Operating threshold to report FAR/FRR at.
        target_far: FAR target for threshold calibration.

    Returns:
        Evaluation report.

    Raises:
        ValueError: If there are no genuine or no impostor pairs.
    """
    genuine, impostor = pairwise_scores(embeddings_by_person)
    if genuine.size == 0 or impostor.size == 0:
        raise ValueError(
            "Need at least two identities and at least one identity with two or more images"
        )
    calibrated = threshold_for_far(impostor, target_far)
    return EvaluationReport(
        num_identities=len(embeddings_by_person),
        num_embeddings=sum(len(v) for v in embeddings_by_person.values()),
        num_genuine_pairs=int(genuine.size),
        num_impostor_pairs=int(impostor.size),
        at_threshold=error_rates(genuine, impostor, threshold),
        equal_error=equal_error_rate(genuine, impostor),
        target_far=target_far,
        threshold_at_target_far=calibrated,
        tar_at_target_far=1.0 - error_rates(genuine, impostor, calibrated).frr,
    )
