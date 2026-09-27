"""Vector normalisation and similarity metrics for face embeddings."""

import numpy as np


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    """
    Scale a vector to unit L2 norm.

    Args:
        vector: 1-D embedding.

    Returns:
        Float32 unit-norm copy of the vector.

    Raises:
        ValueError: If the vector has zero norm.
    """
    vector = np.asarray(vector, dtype=np.float32).ravel()
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("Cannot normalise a zero vector")
    return vector / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two embeddings, in [-1, 1].

    Args:
        a: First embedding.
        b: Second embedding of the same dimension.

    Returns:
        Cosine of the angle between the two vectors.

    Raises:
        ValueError: If dimensions differ or either vector is zero.
    """
    a_arr = np.asarray(a).ravel()
    b_arr = np.asarray(b).ravel()
    if a_arr.shape != b_arr.shape:
        raise ValueError(f"Embedding dimensions differ: {a_arr.shape} vs {b_arr.shape}")
    score = float(np.dot(l2_normalize(a_arr), l2_normalize(b_arr)))
    return float(np.clip(score, -1.0, 1.0))
