"""
Face detection with SCRFD (InsightFace `det_10g.onnx` / `det_500m.onnx`) on ONNX Runtime.

The anchor decoding is implemented here directly so the only hard runtime
dependencies are numpy and onnxruntime. Image resizing is the one op that
needs an imaging library; it is injected (see `Resize`) rather than imported
at module level, so callers that supply their own (e.g. a Pillow-based one
for a deployment that can't afford OpenCV's footprint) never need OpenCV
installed at all. `resize_with_cv2` is the default for callers that don't care.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import onnxruntime as ort

Resize = Callable[[np.ndarray, Tuple[int, int]], np.ndarray]

DEFAULT_INPUT_SIZE = (640, 640)
DEFAULT_SCORE_THRESHOLD = 0.5
DEFAULT_NMS_THRESHOLD = 0.4
DEFAULT_PROVIDERS = ("CPUExecutionProvider",)


def resize_with_cv2(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    """Default `Resize`: OpenCV, imported lazily so it's only required when used."""
    import cv2

    return cv2.resize(image, size)

_STRIDES = (8, 16, 32)
_ANCHORS_PER_LOCATION = 2


@dataclass(frozen=True)
class DetectedFace:
    """
    A single detected face.

    Attributes:
        bbox: (4,) x1, y1, x2, y2 in source-image pixels.
        score: Detector confidence in [0, 1].
        landmarks: (5, 2) eyes, nose, mouth corners in source-image pixels.
    """

    bbox: np.ndarray
    score: float
    landmarks: np.ndarray

    @property
    def area(self) -> float:
        """Bounding-box area in pixels."""
        x1, y1, x2, y2 = self.bbox
        return float(max(0.0, x2 - x1) * max(0.0, y2 - y1))


class FaceDetector(ABC):
    """Contract for face detectors returning boxes and five-point landmarks."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        """
        Detect faces in a BGR image.

        Args:
            image: BGR uint8 image (H, W, 3).

        Returns:
            Detected faces, highest score first.
        """


class ScrfdDetector(FaceDetector):
    """SCRFD detector (strides 8/16/32, two anchors per location, with keypoints)."""

    def __init__(
        self,
        session: ort.InferenceSession,
        input_size: Tuple[int, int] = DEFAULT_INPUT_SIZE,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
        resize: Resize = resize_with_cv2,
    ):
        """
        Args:
            session: ONNX Runtime session for an SCRFD model with keypoint outputs.
            input_size: Network input (width, height); both must be multiples of 32.
            score_threshold: Minimum confidence to keep a detection.
            nms_threshold: IoU above which overlapping detections are suppressed.
            resize: (image, (width, height)) -> resized image. Defaults to OpenCV;
                pass an alternative to avoid needing OpenCV installed at all.
        """
        if len(session.get_outputs()) != 3 * len(_STRIDES):
            raise ValueError("SCRFD model must expose score, bbox and keypoint outputs per stride")
        self._session = session
        self._input_name = session.get_inputs()[0].name
        self._input_size = input_size
        self._score_threshold = score_threshold
        self._nms_threshold = nms_threshold
        self._resize = resize
        self._anchor_cache: Dict[Tuple[int, int, int], np.ndarray] = {}

    @classmethod
    def from_path(
        cls, model_path: Path, providers: Optional[Sequence[str]] = None, **kwargs
    ) -> "ScrfdDetector":
        """Load the detector from an ONNX file. Extra kwargs (e.g. `resize`) pass through."""
        session = ort.InferenceSession(
            str(model_path), providers=list(providers or DEFAULT_PROVIDERS)
        )
        return cls(session, **kwargs)

    def detect(self, image: np.ndarray) -> List[DetectedFace]:
        """See FaceDetector.detect."""
        blob, scale = self._preprocess(image)
        outputs = self._session.run(None, {self._input_name: blob})
        boxes, scores, landmarks = self._decode(outputs)
        if len(scores) == 0:
            return []
        boxes /= scale
        landmarks /= scale
        keep = non_max_suppression(boxes, scores, self._nms_threshold)
        return [DetectedFace(boxes[i], float(scores[i]), landmarks[i]) for i in keep]

    def _preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected a BGR image (H, W, 3), got shape {image.shape}")
        width, height = self._input_size
        image_height, image_width = image.shape[:2]
        # Letterbox into the top-left corner so decoded coordinates only need rescaling.
        scale = min(width / image_width, height / image_height)
        new_width = max(1, int(round(image_width * scale)))
        new_height = max(1, int(round(image_height * scale)))
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas[:new_height, :new_width] = self._resize(image, (new_width, new_height))
        rgb = canvas[:, :, ::-1].astype(np.float32)
        blob = ((rgb - 127.5) / 128.0).transpose(2, 0, 1)[None]
        return np.ascontiguousarray(blob), new_height / image_height

    def _decode(
        self, outputs: Sequence[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        width, height = self._input_size
        num_levels = len(_STRIDES)
        all_boxes, all_scores, all_landmarks = [], [], []
        for level, stride in enumerate(_STRIDES):
            scores = np.asarray(outputs[level]).reshape(-1)
            box_distances = np.asarray(outputs[level + num_levels]).reshape(-1, 4) * stride
            landmark_offsets = (
                np.asarray(outputs[level + 2 * num_levels]).reshape(-1, 5, 2) * stride
            )
            centers = self._anchor_centers(height // stride, width // stride, stride)

            keep = scores >= self._score_threshold
            if not keep.any():
                continue
            kept_centers = centers[keep]
            kept_distances = box_distances[keep]
            all_boxes.append(
                np.hstack(
                    [kept_centers - kept_distances[:, :2], kept_centers + kept_distances[:, 2:]]
                )
            )
            all_scores.append(scores[keep])
            all_landmarks.append(kept_centers[:, None, :] + landmark_offsets[keep])

        if not all_scores:
            return np.empty((0, 4), np.float32), np.empty(0, np.float32), np.empty((0, 5, 2))
        return (
            np.concatenate(all_boxes).astype(np.float32),
            np.concatenate(all_scores).astype(np.float32),
            np.concatenate(all_landmarks).astype(np.float32),
        )

    def _anchor_centers(self, rows: int, cols: int, stride: int) -> np.ndarray:
        key = (rows, cols, stride)
        if key not in self._anchor_cache:
            grid_y, grid_x = np.mgrid[:rows, :cols]
            centers = np.stack([grid_x, grid_y], axis=-1).reshape(-1, 2).astype(np.float32)
            self._anchor_cache[key] = np.repeat(centers * stride, _ANCHORS_PER_LOCATION, axis=0)
        return self._anchor_cache[key]


def non_max_suppression(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> List[int]:
    """
    Greedy non-maximum suppression.

    Args:
        boxes: (N, 4) x1, y1, x2, y2.
        scores: (N,) confidences.
        iou_threshold: Boxes overlapping a kept box above this IoU are dropped.

    Returns:
        Indices of kept boxes, highest score first.
    """
    x1, y1, x2, y2 = boxes.T
    areas = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    order = np.argsort(-scores)
    keep: List[int] = []
    while order.size > 0:
        best = int(order[0])
        keep.append(best)
        rest = order[1:]
        inter_w = np.clip(np.minimum(x2[best], x2[rest]) - np.maximum(x1[best], x1[rest]), 0, None)
        inter_h = np.clip(np.minimum(y2[best], y2[rest]) - np.maximum(y1[best], y1[rest]), 0, None)
        intersection = inter_w * inter_h
        iou = intersection / np.maximum(areas[best] + areas[rest] - intersection, 1e-12)
        order = rest[iou <= iou_threshold]
    return keep
