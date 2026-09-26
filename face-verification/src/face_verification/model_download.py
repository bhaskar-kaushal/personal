"""
One-time model installation.

This is the only module that touches the network. Everything else loads
models from a local directory, so after installation the system runs fully
offline. For air-gapped hosts, copy `buffalo_l.zip` over and install it
with `face-verify download-models --zip <path>`.
"""

import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

BUFFALO_L_URL = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
BUFFALO_L_SHA256 = "80ffe37d8a5940d59a7384c201a2a38d4741f2f3c51eef46ebb28218a7b0ca2f"
DETECTOR_FILENAME = "det_10g.onnx"
EMBEDDER_FILENAME = "w600k_r50.onnx"
_CHUNK_SIZE = 1 << 20


def sha256_of(path: Path) -> str:
    """Hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install_models(models_dir: Path, archive: Optional[Path] = None) -> None:
    """
    Install the detector and embedder ONNX files into models_dir.

    Args:
        models_dir: Destination directory.
        archive: Local buffalo_l.zip; downloaded from BUFFALO_L_URL if None.

    Raises:
        ValueError: If the archive checksum does not match BUFFALO_L_SHA256.
    """
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        if archive is None:
            archive = Path(tmp) / "buffalo_l.zip"
            with urllib.request.urlopen(BUFFALO_L_URL) as response, open(archive, "wb") as out:
                shutil.copyfileobj(response, out, _CHUNK_SIZE)

        actual = sha256_of(archive)
        if actual != BUFFALO_L_SHA256:
            raise ValueError(
                f"Checksum mismatch for {archive}: expected {BUFFALO_L_SHA256}, got {actual}"
            )
        with zipfile.ZipFile(archive) as bundle:
            for name in (DETECTOR_FILENAME, EMBEDDER_FILENAME):
                with bundle.open(name) as src, open(models_dir / name, "wb") as dst:
                    shutil.copyfileobj(src, dst, _CHUNK_SIZE)
