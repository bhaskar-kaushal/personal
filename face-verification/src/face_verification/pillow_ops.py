"""
Pillow-based `Resize`/`Warp` implementations (see detection.py, alignment.py).

For deployments where OpenCV's footprint is a problem (e.g. a serverless function
size budget) but Pillow's is not. Requires the `pillow` extra; PIL is imported
lazily so importing this module doesn't require Pillow unless these are called.
"""

from typing import Tuple

import numpy as np


def resize_with_pillow(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """`Resize` for detection.ScrfdDetector: bilinear resize via Pillow."""
    from PIL import Image

    width, height = size
    resized = Image.fromarray(image).resize((width, height), Image.BILINEAR)
    return np.asarray(resized)


def warp_affine_with_pillow(image: np.ndarray, matrix: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """
    `Warp` for alignment.align_face: affine warp via Pillow.

    PIL's AFFINE transform takes the *inverse* map (destination -> source), so
    the forward `matrix` (source -> destination) produced by
    estimate_similarity_transform is inverted here first.
    """
    from PIL import Image

    width, height = size
    rotation_scale = matrix[:, :2]
    translation = matrix[:, 2]
    inverse_rotation_scale = np.linalg.inv(rotation_scale)
    inverse_translation = -inverse_rotation_scale @ translation
    inverse_coeffs = np.hstack([inverse_rotation_scale, inverse_translation[:, None]]).ravel()

    warped = Image.fromarray(image).transform(
        (width, height), Image.AFFINE, inverse_coeffs.tolist(), resample=Image.BILINEAR
    )
    return np.asarray(warped)
