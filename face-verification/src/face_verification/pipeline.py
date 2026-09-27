"""Enrollment and 1:1 verification orchestration."""

from datetime import datetime, timezone
from typing import Callable, Optional, Sequence, Tuple

import numpy as np

from face_verification.encoder import FaceEncoder
from face_verification.gallery import EnrollmentRecord, EnrollmentSample, EnrollmentStore
from face_verification.similarity import cosine_similarity
from face_verification.verification import (
    IdentificationResult,
    IdentificationStatus,
    ThresholdVerifier,
    VerificationResult,
    VerificationStatus,
)


class NoFaceDetectedError(ValueError):
    """Raised when an enrollment image contains no detectable face."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VerificationPipeline:
    """Enrolls people and verifies probe images against a claimed identity."""

    def __init__(
        self,
        encoder: FaceEncoder,
        store: EnrollmentStore,
        verifier: ThresholdVerifier,
        clock: Callable[[], datetime] = _utc_now,
    ):
        """
        Args:
            encoder: Image-to-embedding encoder.
            store: Enrollment persistence.
            verifier: Threshold decision rule.
            clock: Source of enrollment timestamps.
        """
        self._encoder = encoder
        self._store = store
        self._verifier = verifier
        self._clock = clock

    def enroll(
        self, person_id: str, images: Sequence[Tuple[str, np.ndarray]]
    ) -> EnrollmentRecord:
        """
        Enroll one or more images for a person.

        All images are encoded before anything is stored, so a bad image leaves
        the gallery unchanged.

        Args:
            person_id: Identity to enroll under.
            images: (source name, BGR image) pairs.

        Returns:
            The updated enrollment record.

        Raises:
            NoFaceDetectedError: If any image has no detectable face.
            ValueError: If images is empty or person_id is invalid.
        """
        if not images:
            raise ValueError("At least one image is required for enrollment")
        enrolled_at = self._clock()
        samples = []
        for source, image in images:
            embedding = self._encoder.encode(image, image_id=source)
            if embedding is None:
                raise NoFaceDetectedError(f"No face detected in enrollment image {source!r}")
            samples.append(EnrollmentSample(embedding, enrolled_at, source))
        return self._store.add_samples(person_id, samples)

    def verify(self, person_id: str, image: np.ndarray) -> VerificationResult:
        """
        Check whether the face in an image belongs to the claimed person.

        Args:
            person_id: Claimed identity.
            image: BGR probe image.

        Returns:
            Verification result; NOT_ENROLLED and NO_FACE are reported explicitly
            rather than as a failed match.
        """
        threshold = self._verifier.threshold
        record = self._store.get(person_id)
        if record is None or not record.samples:
            return VerificationResult(person_id, VerificationStatus.NOT_ENROLLED, None, threshold)

        embedding = self._encoder.encode(image, image_id=person_id)
        if embedding is None:
            return VerificationResult(person_id, VerificationStatus.NO_FACE, None, threshold)

        score = cosine_similarity(embedding, record.template())
        return VerificationResult(person_id, self._verifier.decide(score), score, threshold)

    def identify(self, image: np.ndarray) -> IdentificationResult:
        """
        Search a probe image against every enrolled identity (1:N).

        This is a linear scan over the gallery, scoring one template per enrolled
        person; it does not use an approximate nearest-neighbour index, so cost
        grows with the number of enrolled identities.

        Args:
            image: BGR probe image.

        Returns:
            The best-scoring candidate and whether it clears the threshold.
            EMPTY_GALLERY and NO_FACE are reported explicitly rather than as NO_MATCH.
        """
        threshold = self._verifier.threshold
        person_ids = self._store.list_ids()
        if not person_ids:
            return IdentificationResult(IdentificationStatus.EMPTY_GALLERY, None, None, threshold, 0)

        embedding = self._encoder.encode(image, image_id="probe")
        if embedding is None:
            return IdentificationResult(
                IdentificationStatus.NO_FACE, None, None, threshold, len(person_ids)
            )

        best_id: Optional[str] = None
        best_score = -1.0
        for person_id in person_ids:
            record = self._store.get(person_id)
            if record is None or not record.samples:
                continue
            score = cosine_similarity(embedding, record.template())
            if score > best_score:
                best_id, best_score = person_id, score

        status = (
            IdentificationStatus.MATCH
            if self._verifier.accepts(best_score)
            else IdentificationStatus.NO_MATCH
        )
        return IdentificationResult(status, best_id, best_score, threshold, len(person_ids))
