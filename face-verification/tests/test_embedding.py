"""Tests for the ONNX ArcFace embedder."""

import numpy as np
import pytest

from face_verification.embedding import OnnxArcFaceEmbedder
from tests.conftest import FakeSession


def test_embed_preprocesses_and_normalises():
    session = FakeSession([np.array([[3.0, 4.0]], np.float32)])
    embedder = OnnxArcFaceEmbedder(session)
    face = np.zeros((112, 112, 3), np.uint8)
    face[..., 2] = 255  # red channel in BGR

    embedding = embedder.embed(face)

    np.testing.assert_allclose(embedding, [0.6, 0.8], atol=1e-6)
    blob = session.inputs_seen[0]["input.1"]
    assert blob.shape == (1, 3, 112, 112) and blob.dtype == np.float32
    assert blob[0, 0, 0, 0] == pytest.approx(1.0)  # R first after BGR->RGB
    assert blob[0, 2, 0, 0] == pytest.approx(-1.0)


def test_embed_rejects_unaligned_input():
    embedder = OnnxArcFaceEmbedder(FakeSession([np.ones((1, 2), np.float32)]))

    with pytest.raises(ValueError):
        embedder.embed(np.zeros((100, 100, 3), np.uint8))
