"""Image loading helpers."""

from pathlib import Path
from typing import List

import cv2
import numpy as np

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".bmp", ".webp"})


def load_image(path: Path) -> np.ndarray:
    """
    Read an image from disk as BGR uint8.

    Args:
        path: Image file.

    Returns:
        (H, W, 3) BGR image.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be decoded as an image.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found: {path}")
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {path}")
    return image


def list_images(directory: Path) -> List[Path]:
    """Image files directly inside a directory, sorted by name."""
    return sorted(
        p for p in Path(directory).iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
