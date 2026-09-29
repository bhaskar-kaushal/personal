"""Lazily-built, process-wide pipeline for the demo API (reused across warm invocations)."""

from pathlib import Path
from typing import Optional

from face_verification.detection import ScrfdDetector
from face_verification.embedding import OnnxArcFaceEmbedder
from face_verification.encoder import FaceEncoder
from face_verification.pillow_ops import resize_with_pillow, warp_affine_with_pillow
from face_verification.pipeline import VerificationPipeline
from face_verification.verification import DEFAULT_THRESHOLD, ThresholdVerifier

from api._lib.blob_store import BlobEnrollmentStore

MODELS_DIR = Path(__file__).resolve().parent.parent / "_models"
DETECTOR_PATH = MODELS_DIR / "det_500m.onnx"
EMBEDDER_PATH = MODELS_DIR / "w600k_mbf.onnx"

_pipeline: Optional[VerificationPipeline] = None
_store: Optional[BlobEnrollmentStore] = None


def _build() -> None:
    global _pipeline, _store
    detector = ScrfdDetector.from_path(DETECTOR_PATH, resize=resize_with_pillow)
    embedder = OnnxArcFaceEmbedder.from_path(EMBEDDER_PATH)
    encoder = FaceEncoder(detector, embedder, warp=warp_affine_with_pillow)
    _store = BlobEnrollmentStore()
    _pipeline = VerificationPipeline(encoder, _store, ThresholdVerifier(DEFAULT_THRESHOLD))


def get_pipeline() -> VerificationPipeline:
    """Build the pipeline on first use and reuse it for the life of the process."""
    if _pipeline is None:
        _build()
    return _pipeline


def get_store() -> BlobEnrollmentStore:
    """The same store instance used by get_pipeline(), for admin/read-only operations."""
    if _store is None:
        _build()
    return _store
