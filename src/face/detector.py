"""Face detection with the pretrained OpenCV YuNet model (Person 1).

YuNet (``face_detection_yunet_2023mar.onnx`` from the OpenCV Zoo) is a real
pretrained convolutional face detector. Each detection provides a bounding
box, 5 facial landmarks, and a confidence score.

Zero-face and multi-face cases are NOT hidden: :meth:`YuNetFaceDetector.detect`
always returns the full list of detections so callers can react honestly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - import-time guard
    raise ImportError(
        "opencv-python-headless is required for face detection. "
        "Install it with: pip install -r requirements.txt"
    ) from exc

from src.face.errors import FaceModelError, FaceProcessingError
from src.face.models import ensure_model, get_yunet_model_path

YUNET_URLS = (
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
)
YUNET_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
YUNET_SIZE = 232589

DEFAULT_SCORE_THRESHOLD = 0.6
DEFAULT_NMS_THRESHOLD = 0.3
DEFAULT_TOP_K = 5000


@dataclass
class FaceDetection:
    """One detected face.

    Attributes:
        bbox: ``(x, y, w, h)`` bounding box in pixels.
        landmarks: 5 ``(x, y)`` facial landmarks (eyes, nose, mouth corners).
        confidence: detector confidence score in ``[0, 1]``.
        area: bounding-box area in pixels (used for primary-face selection).
        raw: original 15-value YuNet detection row (needed for SFace alignment).
        index: position of this detection in the detector output.
    """

    bbox: tuple[int, int, int, int]
    landmarks: list[tuple[float, float]]
    confidence: float
    area: int
    raw: np.ndarray
    index: int


def _create_yunet(
    model_path: str,
    input_size: tuple[int, int],
    score_threshold: float,
    nms_threshold: float,
    top_k: int,
):
    """Create the OpenCV YuNet detector (compatible across cv2 4.8+ / 5.x)."""
    backend = int(getattr(cv2.dnn, "DNN_BACKEND_DEFAULT", 0))
    target = int(getattr(cv2.dnn, "DNN_TARGET_CPU", 0))
    kwargs = {
        "model": model_path,
        "config": "",
        "input_size": input_size,
        "score_threshold": score_threshold,
        "nms_threshold": nms_threshold,
        "top_k": top_k,
        "backend_id": backend,
        "target_id": target,
    }
    if hasattr(cv2, "FaceDetectorYN") and hasattr(cv2.FaceDetectorYN, "create"):
        return cv2.FaceDetectorYN.create(**kwargs)
    if hasattr(cv2, "FaceDetectorYN_create"):  # older 4.x binding name
        return cv2.FaceDetectorYN_create(**kwargs)
    raise FaceModelError(
        "This OpenCV build has no YuNet (FaceDetectorYN) support. "
        "Install opencv-python-headless>=4.10."
    )


class YuNetFaceDetector:
    """Thin reusable wrapper around the YuNet ONNX detector."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
        top_k: int = DEFAULT_TOP_K,
        auto_download: bool = True,
    ) -> None:
        explicit_path = model_path
        self.model_path = model_path or get_yunet_model_path()
        self.score_threshold = float(score_threshold)
        self.nms_threshold = float(nms_threshold)
        self.top_k = int(top_k)
        if not os.path.isfile(self.model_path):
            if explicit_path:
                raise FaceModelError(
                    f"YuNet model not found at explicit path '{self.model_path}'. "
                    f"Check FACE_YUNET_MODEL or run "
                    f"'python scripts/download_face_models.py'."
                )
            self.model_path = ensure_model(
                os.path.basename(self.model_path) or "yunet.onnx",
                YUNET_URLS,
                YUNET_SHA256,
                YUNET_SIZE,
                self.model_path,
                auto_download=auto_download,
            )
        try:
            self._detector = _create_yunet(
                self.model_path,
                (320, 320),
                self.score_threshold,
                self.nms_threshold,
                self.top_k,
            )
        except Exception as exc:
            raise FaceModelError(
                f"Could not initialize the YuNet face detector "
                f"from '{self.model_path}': {exc}"
            ) from exc

    def detect(self, image_bgr: np.ndarray) -> list[FaceDetection]:
        """Detect faces in a BGR image.

        Returns a (possibly empty) list of :class:`FaceDetection`. An empty
        list means "no face detected" — never an exception.
        """
        if image_bgr is None or not isinstance(image_bgr, np.ndarray):
            raise FaceProcessingError("detect() requires a valid BGR image array.")
        if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
            raise FaceProcessingError(
                f"detect() requires a BGR color image, got shape {image_bgr.shape}."
            )
        height, width = image_bgr.shape[:2]
        if height < 1 or width < 1:
            raise FaceProcessingError("detect() received an empty image.")

        try:
            self._detector.setInputSize((int(width), int(height)))
            result = self._detector.detect(image_bgr)
        except Exception as exc:
            raise FaceProcessingError(f"YuNet face detection failed: {exc}") from exc

        # cv2 4.x returns (retval, faces); newer bindings may return faces only.
        faces = result[1] if isinstance(result, tuple) and len(result) == 2 else result
        if faces is None:
            return []

        detections: list[FaceDetection] = []
        for index, row in enumerate(np.asarray(faces, dtype=np.float32).reshape(-1, 15)):
            x, y, w, h = (int(v) for v in row[0:4])
            confidence = float(row[14])
            landmarks = [
                (float(row[4 + 2 * k]), float(row[5 + 2 * k])) for k in range(5)
            ]
            detections.append(
                FaceDetection(
                    bbox=(x, y, w, h),
                    landmarks=landmarks,
                    confidence=confidence,
                    area=max(w, 0) * max(h, 0),
                    raw=np.asarray(row, dtype=np.float32),
                    index=index,
                )
            )
        return detections


_default_detector: Optional[YuNetFaceDetector] = None


def get_detector(
    model_path: Optional[str] = None,
    score_threshold: Optional[float] = None,
    auto_download: bool = True,
) -> YuNetFaceDetector:
    """Return the shared lazy-initialized YuNet detector singleton."""
    global _default_detector
    if _default_detector is not None and model_path is None and score_threshold is None:
        return _default_detector
    if score_threshold is None:
        score_threshold = float(os.getenv("FACE_DETECT_THRESHOLD", str(DEFAULT_SCORE_THRESHOLD)))
    detector = YuNetFaceDetector(
        model_path=model_path,
        score_threshold=score_threshold,
        auto_download=auto_download,
    )
    if model_path is None:
        _default_detector = detector
    return detector


def reset_detector_singleton() -> None:
    """Forget the cached detector (used by tests)."""
    global _default_detector
    _default_detector = None
