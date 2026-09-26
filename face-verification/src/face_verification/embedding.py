"""Face embedding extraction with ArcFace-class ONNX models."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import onnxruntime as ort

from face_verification.alignment import ALIGNED_FACE_SIZE
from face_verification.similarity import l2_normalize

DEFAULT_PROVIDERS = ("CPUExecutionProvider",)


class FaceEmbedder(ABC):
    """Contract for models mapping an aligned face crop to an identity embedding."""

    @abstractmethod
    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        """
        Compute an identity embedding.

        Args:
            aligned_face: (112, 112, 3) BGR uint8 crop from align_face.

        Returns:
            Unit-norm float32 embedding.
        """


class OnnxArcFaceEmbedder(FaceEmbedder):
    """ArcFace embedder (e.g. InsightFace `w600k_r50.onnx`, 512-d output)."""

    def __init__(self, session: ort.InferenceSession):
        """
        Args:
            session: ONNX Runtime session taking (1, 3, 112, 112) RGB input.
        """
        self._session = session
        self._input_name = session.get_inputs()[0].name

    @classmethod
    def from_path(
        cls, model_path: Path, providers: Optional[Sequence[str]] = None
    ) -> "OnnxArcFaceEmbedder":
        """Load the embedder from an ONNX file."""
        session = ort.InferenceSession(
            str(model_path), providers=list(providers or DEFAULT_PROVIDERS)
        )
        return cls(session)

    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        """See FaceEmbedder.embed."""
        expected_shape = (ALIGNED_FACE_SIZE, ALIGNED_FACE_SIZE, 3)
        if aligned_face.shape != expected_shape:
            raise ValueError(f"Expected aligned face {expected_shape}, got {aligned_face.shape}")
        rgb = aligned_face[:, :, ::-1].astype(np.float32)
        blob = np.ascontiguousarray(((rgb - 127.5) / 127.5).transpose(2, 0, 1)[None])
        output = self._session.run(None, {self._input_name: blob})[0]
        return l2_normalize(output[0])
