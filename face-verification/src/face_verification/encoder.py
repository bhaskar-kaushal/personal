"""Image to identity embedding: detect, pick the primary face, align, embed."""

from typing import Optional

import numpy as np

from face_verification.alignment import align_face
from face_verification.detection import FaceDetector
from face_verification.embedding import FaceEmbedder


class FaceEncoder:
    """Turns a raw image into the embedding of its primary (largest) face."""

    def __init__(self, detector: FaceDetector, embedder: FaceEmbedder):
        """
        Args:
            detector: Face detector providing five-point landmarks.
            embedder: Embedding model operating on aligned 112x112 crops.
        """
        self._detector = detector
        self._embedder = embedder

    def encode(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Embed the largest face in an image.

        The largest face is taken as the subject presenting to the camera; other
        faces in frame (bystanders) are ignored.

        Args:
            image: BGR uint8 image.

        Returns:
            Unit-norm embedding, or None if no face was detected.
        """
        faces = self._detector.detect(image)
        if not faces:
            return None
        primary = max(faces, key=lambda face: face.area)
        return self._embedder.embed(align_face(image, primary.landmarks))
