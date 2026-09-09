"""Person 1 — face detection + face embedding.

Uses the pretrained OpenCV YuNet detector and SFace recognizer (OpenCV Zoo).

Imports are lazy so that ``src.face.models`` (stdlib-only) stays usable even
when OpenCV is not installed yet (e.g. the model-download script).
"""

from __future__ import annotations

__all__ = [
    "FaceDetection",
    "YuNetFaceDetector",
    "get_detector",
    "reset_detector_singleton",
    "SFaceEmbedder",
    "get_embedder",
    "reset_embedder_singleton",
    "l2_normalize",
    "process_query_image",
    "process_candidate_image",
    "select_primary_face",
    "load_image_bgr",
    "describe_query_result",
    "FaceProcessingError",
    "FaceModelError",
    "ensure_models_available",
    "models_available",
]


def __getattr__(name: str):
    if name in {
        "FaceDetection",
        "YuNetFaceDetector",
        "get_detector",
        "reset_detector_singleton",
    }:
        from src.face import detector as _detector

        return getattr(_detector, name)
    if name in {
        "SFaceEmbedder",
        "get_embedder",
        "reset_embedder_singleton",
        "l2_normalize",
    }:
        from src.face import embedder as _embedder

        return getattr(_embedder, name)
    if name in {
        "process_query_image",
        "process_candidate_image",
        "select_primary_face",
        "load_image_bgr",
        "describe_query_result",
    }:
        from src.face import processor as _processor

        return getattr(_processor, name)
    if name in {"FaceProcessingError", "FaceModelError"}:
        from src.face import errors as _errors

        return getattr(_errors, name)
    if name in {"ensure_models_available", "models_available"}:
        from src.face import models as _models

        return getattr(_models, name)
    raise AttributeError(f"module 'src.face' has no attribute {name!r}")
