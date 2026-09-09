"""High-level face-processing workflow (Person 1).

``image -> detect faces -> select/process face -> generate embedding``

Selection strategy (documented, deterministic):
- Query image: the LARGEST-area detection is the primary face (ties broken by
  higher detector confidence, then lower detection index). The total
  ``face_count`` and ``multiple_faces`` flag are always preserved so callers
  know when the input was ambiguous.
- Candidate images: embeddings are generated for EVERY detected face; the
  matcher compares each one and keeps the highest similarity.

``detector`` / ``embedder`` arguments allow dependency injection (fakes in
unit tests). When omitted, the shared lazy singletons are used.
"""

from __future__ import annotations

import os
from typing import Any, Optional

import numpy as np

try:
    import cv2
except ImportError as exc:  # pragma: no cover - import-time guard
    raise ImportError(
        "opencv-python-headless is required for face processing. "
        "Install it with: pip install -r requirements.txt"
    ) from exc

from src.face.detector import FaceDetection, get_detector
from src.face.embedder import get_embedder
from src.face.errors import FaceProcessingError

SELECTION_STRATEGY = "largest_area"


def load_image_bgr(image_path: str) -> np.ndarray:
    """Load an image file as a BGR array.

    Raises:
        FaceProcessingError: when the file is missing, unreadable, or not a
            decodable image.
    """
    if not image_path:
        raise FaceProcessingError("No image path provided.")
    if not os.path.isfile(image_path):
        raise FaceProcessingError(f"Image file not found: {image_path}")
    try:
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    except Exception as exc:
        raise FaceProcessingError(
            f"Could not read image '{image_path}': {exc}"
        ) from exc
    if image is None:
        raise FaceProcessingError(
            f"File is not a decodable image: {image_path}"
        )
    return image


def select_primary_face(detections: list[FaceDetection]) -> FaceDetection:
    """Select the primary face: largest area, then confidence, then index."""
    if not detections:
        raise FaceProcessingError("No detections to select from.")
    return max(
        detections,
        key=lambda d: (int(d.area), float(d.confidence), -int(d.index)),
    )


def process_query_image(
    image_path: str,
    detector=None,
    embedder=None,
) -> dict[str, Any]:
    """Detect and embed the primary face of a query/input image.

    Returns a JSON-friendly dict (``embedding`` is a numpy array kept only
    in memory). Never raises for expected failure cases (missing file,
    unreadable image, no face, embedding failure); those produce
    ``{"success": False, ...}`` with a human-readable ``reason``.
    """
    result: dict[str, Any] = {
        "success": False,
        "face_detected": False,
        "reason": None,
        "image_path": image_path,
        "image_shape": None,
        "face_count": 0,
        "selected_face_index": None,
        "selection_strategy": SELECTION_STRATEGY,
        "bbox": None,
        "confidence": None,
        "multiple_faces": False,
        "embedding": None,
        "embedding_dim": None,
    }

    try:
        image = load_image_bgr(image_path)
    except FaceProcessingError as exc:
        result["reason"] = str(exc)
        return result

    result["image_shape"] = tuple(int(v) for v in image.shape)

    face_detector = detector if detector is not None else get_detector()
    face_embedder = embedder if embedder is not None else get_embedder()

    try:
        detections = face_detector.detect(image)
    except FaceProcessingError as exc:
        result["reason"] = f"Face detection failed: {exc}"
        return result
    except Exception as exc:  # never crash the pipeline on detection errors
        result["reason"] = f"Face detection failed unexpectedly: {exc}"
        return result

    result["face_count"] = len(detections)
    result["multiple_faces"] = len(detections) > 1

    if not detections:
        result["reason"] = "No face detected"
        return result

    primary = select_primary_face(detections)
    result["selected_face_index"] = primary.index
    result["bbox"] = tuple(int(v) for v in primary.bbox)
    result["confidence"] = round(float(primary.confidence), 4)

    try:
        embedding = face_embedder.embed_detection(image, primary)
    except FaceProcessingError as exc:
        result["reason"] = f"Face embedding failed: {exc}"
        return result
    except Exception as exc:
        result["reason"] = f"Face embedding failed unexpectedly: {exc}"
        return result

    result["embedding"] = np.asarray(embedding, dtype=np.float32).reshape(-1)
    result["embedding_dim"] = int(result["embedding"].size)
    result["face_detected"] = True
    result["success"] = True
    return result


def process_candidate_image(
    image_path: str,
    detector=None,
    embedder=None,
) -> dict[str, Any]:
    """Detect and embed EVERY face in a candidate image.

    The matcher scores each embedding against the query and keeps the best
    one, so group photos containing the query person stay matchable.
    """
    result: dict[str, Any] = {
        "success": False,
        "face_detected": False,
        "reason": None,
        "image_path": image_path,
        "image_shape": None,
        "face_count": 0,
        "faces": [],
        "embeddings": [],
    }

    try:
        image = load_image_bgr(image_path)
    except FaceProcessingError as exc:
        result["reason"] = str(exc)
        return result

    result["image_shape"] = tuple(int(v) for v in image.shape)

    face_detector = detector if detector is not None else get_detector()
    face_embedder = embedder if embedder is not None else get_embedder()

    try:
        detections = face_detector.detect(image)
    except FaceProcessingError as exc:
        result["reason"] = f"Face detection failed: {exc}"
        return result
    except Exception as exc:
        result["reason"] = f"Face detection failed unexpectedly: {exc}"
        return result

    result["face_count"] = len(detections)

    if not detections:
        result["reason"] = "No face detected"
        return result

    faces: list[dict[str, Any]] = []
    embeddings: list[np.ndarray] = []
    for detection in detections:
        try:
            embedding = np.asarray(
                face_embedder.embed_detection(image, detection), dtype=np.float32
            ).reshape(-1)
        except (FaceProcessingError, Exception):
            # One bad face must not discard the other faces in this image.
            continue
        faces.append(
            {
                "index": detection.index,
                "bbox": tuple(int(v) for v in detection.bbox),
                "confidence": round(float(detection.confidence), 4),
                "embedding": embedding,
            }
        )
        embeddings.append(embedding)

    if not faces:
        result["reason"] = "Face embedding failed for all detected faces"
        return result

    result["faces"] = faces
    result["embeddings"] = embeddings
    result["face_detected"] = True
    result["success"] = True
    return result


def describe_query_result(result: dict[str, Any]) -> str:
    """One-line human-readable summary of a query-processing result."""
    if not result.get("success"):
        return f"face processing failed: {result.get('reason')}"
    extra = ""
    if result.get("multiple_faces"):
        extra = (
            f" (multiple faces: {result.get('face_count')}, "
            f"selected #{result.get('selected_face_index')} by {SELECTION_STRATEGY})"
        )
    return f"face detected: YES, faces found: {result.get('face_count')}{extra}"
