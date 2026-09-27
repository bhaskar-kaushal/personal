"""
Landmark-based face alignment.

Faces are warped with a similarity transform (rotation, uniform scale,
translation) so that five detected landmarks land on the canonical ArcFace
112x112 template. ArcFace-class models are trained on exactly this crop, so
matching it is what makes embeddings comparable across images.
"""

from typing import Callable, Tuple

import numpy as np

ALIGNED_FACE_SIZE = 112

Warp = Callable[[np.ndarray, np.ndarray, Tuple[int, int]], np.ndarray]

# Left eye, right eye, nose tip, left mouth corner, right mouth corner (image coordinates).
ARCFACE_TEMPLATE_112 = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ],
    dtype=np.float32,
)


def estimate_similarity_transform(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    Least-squares similarity transform mapping source points onto target points.

    Implements Umeyama (1991) without reflection.

    Args:
        source: (N, 2) points to transform.
        target: (N, 2) destination points.

    Returns:
        (2, 3) affine matrix suitable for cv2.warpAffine.

    Raises:
        ValueError: If shapes mismatch, fewer than 2 points, or source points coincide.
    """
    src = np.asarray(source, dtype=np.float64)
    dst = np.asarray(target, dtype=np.float64)
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 2 or src.shape[0] < 2:
        raise ValueError(f"Expected matching (N>=2, 2) arrays, got {src.shape} and {dst.shape}")

    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)
    src_centered = src - src_mean
    dst_centered = dst - dst_mean

    src_variance = (src_centered**2).sum() / len(src)
    if src_variance == 0.0:
        raise ValueError("Source points are degenerate (all identical)")

    covariance = dst_centered.T @ src_centered / len(src)
    u, singular_values, vt = np.linalg.svd(covariance)
    signs = np.ones(2)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        signs[-1] = -1.0

    rotation = u @ np.diag(signs) @ vt
    scale = (singular_values * signs).sum() / src_variance
    translation = dst_mean - scale * rotation @ src_mean
    return np.hstack([scale * rotation, translation[:, None]]).astype(np.float32)


def warp_affine_with_cv2(image: np.ndarray, matrix: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Default `Warp`: OpenCV, imported lazily so it's only required when used."""
    import cv2

    return cv2.warpAffine(image, matrix, size, borderValue=0.0)


def align_face(image: np.ndarray, landmarks: np.ndarray, warp: Warp = warp_affine_with_cv2) -> np.ndarray:
    """
    Warp a face into the canonical 112x112 ArcFace crop.

    Args:
        image: BGR image (H, W, 3).
        landmarks: (5, 2) landmarks in the order of ARCFACE_TEMPLATE_112.
        warp: (image, 2x3 affine matrix, (width, height)) -> warped image. Defaults
            to OpenCV; pass an alternative to avoid needing OpenCV installed at all.

    Returns:
        Aligned (112, 112, 3) BGR uint8 crop.
    """
    matrix = estimate_similarity_transform(landmarks, ARCFACE_TEMPLATE_112)
    return warp(image, matrix, (ALIGNED_FACE_SIZE, ALIGNED_FACE_SIZE))
