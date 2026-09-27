"""Image to identity embedding: detect, pick the primary face, align, embed."""

from pathlib import Path
from typing import Optional

import numpy as np

from face_verification.alignment import Warp, align_face, warp_affine_with_cv2
from face_verification.detection import FaceDetector
from face_verification.embedding import FaceEmbedder


class FaceEncoder:
    """Turns a raw image into the embedding of its primary (largest) face."""

    def __init__(
        self,
        detector: FaceDetector,
        embedder: FaceEmbedder,
        warp: Warp = warp_affine_with_cv2,
        save_aligned_dir: Optional[str] = None,
    ):
        """
        Args:
            detector: Face detector providing five-point landmarks.
            embedder: Embedding model operating on aligned 112x112 crops.
            warp: Alignment warp; defaults to OpenCV (see `align_face`).
            save_aligned_dir: Directory to save aligned face crops to, for
                debugging/inspection. Saving always uses OpenCV regardless of
                `warp`, so this requires the `cv2` extra when set.
        """
        self._detector = detector
        self._embedder = embedder
        self._warp = warp
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
            image_id: Optional identifier for naming the saved aligned image
                (only used when save_aligned_dir was set).

        Returns:
            Unit-norm embedding, or None if no face was detected.
        """
        faces = self._detector.detect(image)
        if not faces:
            return None
        primary = max(faces, key=lambda face: face.area)
        aligned = align_face(image, primary.landmarks, self._warp)

        if self._save_aligned_dir and image_id:
            import cv2

            cv2.imwrite(str(self._save_aligned_dir / f"aligned_{image_id}"), aligned)

        return self._embedder.embed(aligned)
