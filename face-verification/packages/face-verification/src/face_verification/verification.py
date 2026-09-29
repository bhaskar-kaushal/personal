"""Threshold-based verification decisions and their result type."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# Cosine operating point commonly used for InsightFace w600k_r50. Recalibrate on
# in-house data with `face-verify evaluate --target-far` before deployment.
DEFAULT_THRESHOLD = 0.40


class VerificationStatus(str, Enum):
    """Outcome of a verification attempt."""

    MATCH = "match"
    NO_MATCH = "no_match"
    NO_FACE = "no_face"
    NOT_ENROLLED = "not_enrolled"


@dataclass(frozen=True)
class VerificationResult:
    """
    Result of verifying a probe image against a claimed identity.

    Attributes:
        person_id: Claimed identity.
        status: Decision outcome.
        score: Cosine similarity to the enrolled template; None if not computed.
        threshold: Threshold applied to the score.
    """

    person_id: str
    status: VerificationStatus
    score: Optional[float]
    threshold: float

    @property
    def is_verified(self) -> bool:
        """True only for a positive match."""
        return self.status is VerificationStatus.MATCH

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "person_id": self.person_id,
            "status": self.status.value,
            "verified": self.is_verified,
            "score": None if self.score is None else round(self.score, 6),
            "threshold": self.threshold,
        }


class ThresholdVerifier:
    """Accepts a claim when similarity is at or above a fixed threshold."""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        """
        Args:
            threshold: Cosine similarity cut-off in [-1, 1].

        Raises:
            ValueError: If threshold is outside [-1, 1].
        """
        if not -1.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be in [-1, 1], got {threshold}")
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        """Configured cut-off."""
        return self._threshold

    def accepts(self, score: float) -> bool:
        """True if score meets the threshold."""
        return score >= self._threshold

    def decide(self, score: float) -> VerificationStatus:
        """
        Map a similarity score to MATCH or NO_MATCH.

        Args:
            score: Cosine similarity between probe and template.

        Returns:
            MATCH if score >= threshold, else NO_MATCH.
        """
        return VerificationStatus.MATCH if self.accepts(score) else VerificationStatus.NO_MATCH


class IdentificationStatus(str, Enum):
    """Outcome of a 1:N identification attempt."""

    MATCH = "match"
    NO_MATCH = "no_match"
    NO_FACE = "no_face"
    EMPTY_GALLERY = "empty_gallery"


@dataclass(frozen=True)
class IdentificationResult:
    """
    Result of searching a probe image against every enrolled identity.

    Attributes:
        status: Decision outcome.
        person_id: Best-scoring candidate's id; None if no candidate was scored.
        score: That candidate's cosine similarity to its template; None if no candidate was scored.
        threshold: Threshold applied to the score.
        num_candidates: Number of enrolled identities searched.
    """

    status: IdentificationStatus
    person_id: Optional[str]
    score: Optional[float]
    threshold: float
    num_candidates: int

    @property
    def is_identified(self) -> bool:
        """True only for a positive match."""
        return self.status is IdentificationStatus.MATCH

    def to_dict(self) -> Dict[str, Any]:
        """JSON-serialisable representation."""
        return {
            "status": self.status.value,
            "identified": self.is_identified,
            "person_id": self.person_id,
            "score": None if self.score is None else round(self.score, 6),
            "threshold": self.threshold,
            "num_candidates": self.num_candidates,
        }
