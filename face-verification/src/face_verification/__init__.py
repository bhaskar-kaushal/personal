"""Offline 1:1 facial identity verification: detect, align, embed, score, decide."""

from face_verification.alignment import ARCFACE_TEMPLATE_112, align_face
from face_verification.detection import DetectedFace, FaceDetector, ScrfdDetector
from face_verification.embedding import FaceEmbedder, OnnxArcFaceEmbedder
from face_verification.encoder import FaceEncoder
from face_verification.gallery import (
    EnrollmentRecord,
    EnrollmentSample,
    EnrollmentStore,
    FileEnrollmentStore,
)
from face_verification.pipeline import NoFaceDetectedError, VerificationPipeline
from face_verification.similarity import cosine_similarity, l2_normalize
from face_verification.verification import (
    DEFAULT_THRESHOLD,
    ThresholdVerifier,
    VerificationResult,
    VerificationStatus,
)

__all__ = [
    "ARCFACE_TEMPLATE_112",
    "DEFAULT_THRESHOLD",
    "DetectedFace",
    "EnrollmentRecord",
    "EnrollmentSample",
    "EnrollmentStore",
    "FaceDetector",
    "FaceEmbedder",
    "FaceEncoder",
    "FileEnrollmentStore",
    "NoFaceDetectedError",
    "OnnxArcFaceEmbedder",
    "ScrfdDetector",
    "ThresholdVerifier",
    "VerificationPipeline",
    "VerificationResult",
    "VerificationStatus",
    "align_face",
    "cosine_similarity",
    "l2_normalize",
]
