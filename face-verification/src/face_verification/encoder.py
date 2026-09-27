"""Image to identity embedding: detect, pick the primary face, align, embed."""

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from face_verification.alignment import align_face
from face_verification.detection import FaceDetector
from face_verification.embedding import FaceEmbedder


class FaceEncoder:
    """Turns a raw image into the embedding of its primary (largest) face."""

    def __init__(self, detector: FaceDetector, embedder: FaceEmbedder,
                 save_aligned_dir: Optional[str] = None):
        """
        Args:
            detector: Face detector providing five-point landmarks.
            embedder: Embedding model operating on aligned 112x112 crops.
            save_aligned_dir: Directory to save aligned face images (optional).
        """
        self._detector = detector
        self._embedder = embedder
        self._save_aligned_dir = Path(save_aligned_dir) if save_aligned_dir else None
        if self._save_aligned_dir:
            self._save_aligned_dir.mkdir(parents=True, exist_ok=True)

    def encode(self, image: np.ndarray, image_id: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Embed the largest face in an image.

        The largest face is taken as the subject presenting to the camera; other
        faces in frame (bystanders) are ignored.

        Args:
            image: BGR uint8 image.
            image_id: Optional identifier for saving the aligned image.

        Returns:
            Unit-norm embedding, or None if no face was detected.
        """
        faces = self._detector.detect(image)
        if not faces:
            return None
        primary = max(faces, key=lambda face: face.area)
        aligned = align_face(image, primary.landmarks)

        if self._save_aligned_dir and image_id:
            save_path = self._save_aligned_dir / f"aligned_{image_id}"
            cv2.imwrite(str(save_path), aligned)

        return self._embedder.embed(aligned)
