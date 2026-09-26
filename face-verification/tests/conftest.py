"""Shared test doubles."""

from types import SimpleNamespace
from typing import Dict, List, Optional, Sequence

import numpy as np

from face_verification.detection import DetectedFace, FaceDetector
from face_verification.embedding import FaceEmbedder


class FakeSession:
    """Minimal stand-in for onnxruntime.InferenceSession."""

    def __init__(self, outputs: Sequence[np.ndarray], num_outputs: Optional[int] = None):
        self.outputs = list(outputs)
        self.inputs_seen: List[Dict[str, np.ndarray]] = []
        self._num_outputs = num_outputs or len(self.outputs)

    def get_inputs(self):
        return [SimpleNamespace(name="input.1")]

    def get_outputs(self):
        return [SimpleNamespace(name=str(i)) for i in range(self._num_outputs)]

    def run(self, _output_names, feed):
        self.inputs_seen.append(feed)
        return self.outputs


class StubDetector(FaceDetector):
    """Returns a preset list of faces for every image."""

    def __init__(self, faces: List[DetectedFace]):
        self.faces = faces

    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        return list(self.faces)


class PixelEmbedder(FaceEmbedder):
    """Deterministic embedding derived from the aligned crop's mean colour."""

    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        vector = aligned_face.reshape(-1, 3).mean(axis=0).astype(np.float32) + 1.0
        return vector / np.linalg.norm(vector)


def face_at(x: float, y: float, size: float = 100.0, score: float = 0.9) -> DetectedFace:
    """A face whose landmarks are the ArcFace template scaled into a box at (x, y)."""
    from face_verification.alignment import ARCFACE_TEMPLATE_112

    landmarks = ARCFACE_TEMPLATE_112 * (size / 112.0) + np.array([x, y], dtype=np.float32)
    return DetectedFace(np.array([x, y, x + size, y + size], np.float32), score, landmarks)
