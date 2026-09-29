"""Enrollment records and their persistence."""

import os
import re
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np

from face_verification.similarity import l2_normalize

_PERSON_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def validate_person_id(person_id: str) -> str:
    """
    Ensure a person id is safe to use as a file name.

    Args:
        person_id: Identifier to check.

    Returns:
        The same identifier.

    Raises:
        ValueError: If it contains characters other than letters, digits, '_', '.', '-',
            starts with a non-alphanumeric character, or exceeds 128 characters.
    """
    if not _PERSON_ID_PATTERN.match(person_id):
        raise ValueError(
            f"Invalid person id {person_id!r}: use 1-128 of [A-Za-z0-9_.-], "
            "starting with a letter or digit"
        )
    return person_id


@dataclass(frozen=True)
class EnrollmentSample:
    """
    One enrolled embedding.

    Attributes:
        embedding: Unit-norm embedding.
        enrolled_at: Timezone-aware capture/enrollment time (kept for drift analysis).
        source: Name of the image the embedding came from.
    """

    embedding: np.ndarray
    enrolled_at: datetime
    source: str


@dataclass
class EnrollmentRecord:
    """All enrolled samples for one person."""

    person_id: str
    samples: List[EnrollmentSample] = field(default_factory=list)

    def template(self) -> np.ndarray:
        """
        Identity template: re-normalised mean of all sample embeddings.

        Raises:
            ValueError: If the record has no samples.
        """
        if not self.samples:
            raise ValueError(f"Person {self.person_id!r} has no enrolled samples")
        return l2_normalize(np.mean([sample.embedding for sample in self.samples], axis=0))


class EnrollmentStore(ABC):
    """Contract for enrollment persistence."""

    @abstractmethod
    def get(self, person_id: str) -> Optional[EnrollmentRecord]:
        """Return the record for person_id, or None if not enrolled."""

    @abstractmethod
    def add_samples(
        self, person_id: str, samples: Sequence[EnrollmentSample]
    ) -> EnrollmentRecord:
        """Append samples to a person's record (creating it if needed) and return it."""

    @abstractmethod
    def list_ids(self) -> List[str]:
        """All enrolled person ids, sorted."""


class FileEnrollmentStore(EnrollmentStore):
    """Stores each person as `<root>/<person_id>.npz` (no pickle, atomic writes)."""

    def __init__(self, root: Path):
        """
        Args:
            root: Directory holding the gallery; created if missing.
        """
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def get(self, person_id: str) -> Optional[EnrollmentRecord]:
        """See EnrollmentStore.get."""
        path = self._path_for(person_id)
        if not path.exists():
            return None
        with np.load(path, allow_pickle=False) as data:
            samples = [
                EnrollmentSample(
                    embedding=embedding.astype(np.float32),
                    enrolled_at=datetime.fromisoformat(str(timestamp)),
                    source=str(source),
                )
                for embedding, timestamp, source in zip(
                    data["embeddings"], data["enrolled_at"], data["sources"]
                )
            ]
        return EnrollmentRecord(person_id=person_id, samples=samples)

    def add_samples(
        self, person_id: str, samples: Sequence[EnrollmentSample]
    ) -> EnrollmentRecord:
        """See EnrollmentStore.add_samples."""
        if not samples:
            raise ValueError("No samples to enroll")
        record = self.get(person_id) or EnrollmentRecord(person_id=person_id)
        record.samples.extend(samples)
        self._write(record)
        return record

    def list_ids(self) -> List[str]:
        """See EnrollmentStore.list_ids."""
        return sorted(path.stem for path in self._root.glob("*.npz"))

    def _path_for(self, person_id: str) -> Path:
        return self._root / f"{validate_person_id(person_id)}.npz"

    def _write(self, record: EnrollmentRecord) -> None:
        path = self._path_for(record.person_id)
        fd, tmp_name = tempfile.mkstemp(dir=self._root, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                np.savez(
                    handle,
                    embeddings=np.stack([s.embedding for s in record.samples]).astype(np.float32),
                    enrolled_at=np.array([s.enrolled_at.isoformat() for s in record.samples]),
                    sources=np.array([s.source for s in record.samples]),
                )
            os.replace(tmp_name, path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
