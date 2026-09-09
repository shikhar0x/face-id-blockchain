"""Face embeddings with the pretrained OpenCV SFace model (Person 1).

SFace (``face_recognition_sface_2021dec.onnx`` from the OpenCV Zoo) is a real
pretrained face-recognition network. For an aligned face chip it produces a
128-dimensional floating-point feature vector. This module L2-normalizes the
feature so that cosine similarity between two embeddings is simply their dot
product in ``[-1, 1]``.

Embeddings are used in-memory only for similarity comparison. They are never
written to the blockchain and never persisted to the JSON reports.
"""

from __future__ import annotations

import os
from typing import Optional

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - import-time guard
    raise ImportError(
        "opencv-python-headless is required for face embeddings. "
        "Install it with: pip install -r requirements.txt"
    ) from exc

from src.face.detector import FaceDetection
from src.face.errors import FaceModelError, FaceProcessingError
from src.face.models import ensure_model, get_sface_model_path

SFACE_URLS = (
    "https://raw.githubusercontent.com/opencv/opencv_zoo/main/"
    "models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
    "https://github.com/opencv/opencv_zoo/raw/main/"
    "models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
)
SFACE_SHA256 = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
SFACE_SIZE = 38696353

EMBEDDING_DIM = 128


def _create_sface(model_path: str):
    """Create the OpenCV SFace recognizer (compatible across cv2 4.8+ / 5.x)."""
    backend = int(getattr(cv2.dnn, "DNN_BACKEND_DEFAULT", 0))
    target = int(getattr(cv2.dnn, "DNN_TARGET_CPU", 0))
    kwargs = {
        "model": model_path,
        "config": "",
        "backend_id": backend,
        "target_id": target,
    }
    if hasattr(cv2, "FaceRecognizerSF") and hasattr(cv2.FaceRecognizerSF, "create"):
        return cv2.FaceRecognizerSF.create(**kwargs)
    if hasattr(cv2, "FaceRecognizerSF_create"):  # older 4.x binding name
        return cv2.FaceRecognizerSF_create(**kwargs)
    raise FaceModelError(
        "This OpenCV build has no SFace (FaceRecognizerSF) support. "
        "Install opencv-python-headless>=4.10."
    )


def l2_normalize(vector: np.ndarray) -> np.ndarray:
    """Return the L2-normalized copy of a vector.

    Raises FaceProcessingError for empty or zero-norm vectors.
    """
    array = np.asarray(vector, dtype=np.float64).reshape(-1)
    if array.size == 0:
        raise FaceProcessingError("Cannot normalize an empty embedding.")
    norm = float(np.linalg.norm(array))
    if norm <= 0.0 or not np.isfinite(norm):
        raise FaceProcessingError("Cannot normalize a zero/invalid embedding.")
    return (array / norm).astype(np.float32)


class SFaceEmbedder:
    """Thin reusable wrapper around the SFace ONNX recognizer."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        auto_download: bool = True,
    ) -> None:
        explicit_path = model_path
        self.model_path = model_path or get_sface_model_path()
        if not os.path.isfile(self.model_path):
            if explicit_path:
                raise FaceModelError(
                    f"SFace model not found at explicit path '{self.model_path}'. "
                    f"Check FACE_SFACE_MODEL or run "
                    f"'python scripts/download_face_models.py'."
                )
            self.model_path = ensure_model(
                os.path.basename(self.model_path) or "sface.onnx",
                SFACE_URLS,
                SFACE_SHA256,
                SFACE_SIZE,
                self.model_path,
                auto_download=auto_download,
            )
        try:
            self._recognizer = _create_sface(self.model_path)
        except Exception as exc:
            raise FaceModelError(
                f"Could not initialize the SFace embedder "
                f"from '{self.model_path}': {exc}"
            ) from exc

    def align_crop(
        self, image_bgr: np.ndarray, detection: FaceDetection
    ) -> np.ndarray:
        """Align and crop a detected face into the SFace input chip."""
        if image_bgr is None:
            raise FaceProcessingError("align_crop() requires a valid BGR image.")
        try:
            face_row = np.asarray(detection.raw, dtype=np.float32).reshape(1, -1)
            return self._recognizer.alignCrop(image_bgr, face_row)
        except Exception as exc:
            raise FaceProcessingError(f"SFace face alignment failed: {exc}") from exc

    def embed(self, face_chip: np.ndarray) -> np.ndarray:
        """Generate an L2-normalized 128-d embedding for an aligned face chip."""
        if face_chip is None:
            raise FaceProcessingError("embed() requires a valid aligned face chip.")
        try:
            feature = self._recognizer.feature(face_chip)
        except Exception as exc:
            raise FaceProcessingError(f"SFace embedding failed: {exc}") from exc
        embedding = np.asarray(feature, dtype=np.float32).reshape(-1)
        if embedding.size != EMBEDDING_DIM:
            raise FaceProcessingError(
                f"Unexpected SFace embedding size {embedding.size}; "
                f"expected {EMBEDDING_DIM}."
            )
        return l2_normalize(embedding)

    def embed_detection(
        self, image_bgr: np.ndarray, detection: FaceDetection
    ) -> np.ndarray:
        """Align + embed a single :class:`FaceDetection` in one call."""
        return self.embed(self.align_crop(image_bgr, detection))


_default_embedder: Optional[SFaceEmbedder] = None


def get_embedder(
    model_path: Optional[str] = None,
    auto_download: bool = True,
) -> SFaceEmbedder:
    """Return the shared lazy-initialized SFace embedder singleton."""
    global _default_embedder
    if _default_embedder is not None and model_path is None:
        return _default_embedder
    embedder = SFaceEmbedder(model_path=model_path, auto_download=auto_download)
    if model_path is None:
        _default_embedder = embedder
    return embedder


def reset_embedder_singleton() -> None:
    """Forget the cached embedder (used by tests)."""
    global _default_embedder
    _default_embedder = None
