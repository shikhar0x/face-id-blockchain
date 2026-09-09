"""Unit tests for src/face/processor.py.

The detector/embedder are faked (dependency injection), so these tests need
no model files and no network. Real fixture image files ARE used for the
image-loading paths.
"""

import numpy as np
import pytest

from src.face.detector import FaceDetection
from src.face.errors import FaceProcessingError
from src.face.processor import (
    load_image_bgr,
    process_candidate_image,
    process_query_image,
    select_primary_face,
)

FIXTURE_SINGLE = "tests/fixtures/single_face.jpg"


def _detection(index: int, w: int, h: int, confidence: float) -> FaceDetection:
    return FaceDetection(
        bbox=(10, 10, w, h),
        landmarks=[(0.0, 0.0)] * 5,
        confidence=confidence,
        area=w * h,
        raw=np.zeros(15, dtype=np.float32),
        index=index,
    )


class FakeDetector:
    """Returns a fixed detection list regardless of input."""

    def __init__(self, detections):
        self._detections = detections

    def detect(self, image_bgr):
        return list(self._detections)


class FakeEmbedder:
    """Returns fixed per-face embeddings keyed by detection index."""

    def __init__(self, by_index: dict[int, np.ndarray]):
        self._by_index = by_index

    def embed_detection(self, image_bgr, detection):
        return self._by_index[detection.index]


class FailingEmbedder:
    def embed_detection(self, image_bgr, detection):
        raise FaceProcessingError("synthetic embedding failure")


def _unit_vector(seed: int, dim: int = 128) -> np.ndarray:
    rng = np.random.RandomState(seed)
    vector = rng.randn(dim).astype(np.float32)
    return vector / np.linalg.norm(vector)


# ---- image loading --------------------------------------------------------


def test_load_valid_image():
    image = load_image_bgr(FIXTURE_SINGLE)
    assert image.ndim == 3 and image.shape[2] == 3


def test_load_missing_image_raises():
    with pytest.raises(FaceProcessingError, match="not found"):
        load_image_bgr("tests/fixtures/does_not_exist.jpg")


def test_load_corrupt_image_raises(tmp_path):
    bad = tmp_path / "corrupt.jpg"
    bad.write_bytes(b"this is definitely not image data" * 100)
    with pytest.raises(FaceProcessingError, match="not a decodable image"):
        load_image_bgr(str(bad))


def test_load_empty_path_raises():
    with pytest.raises(FaceProcessingError):
        load_image_bgr("")


# ---- primary-face selection ------------------------------------------------


def test_select_primary_face_prefers_largest_area():
    detections = [
        _detection(0, 50, 50, 0.99),  # small but confident
        _detection(1, 200, 200, 0.61),  # largest -> winner
        _detection(2, 100, 100, 0.95),
    ]
    assert select_primary_face(detections).index == 1


def test_select_primary_face_breaks_area_ties_by_confidence():
    detections = [_detection(0, 100, 100, 0.70), _detection(1, 100, 100, 0.90)]
    assert select_primary_face(detections).index == 1


def test_select_primary_face_requires_detections():
    with pytest.raises(FaceProcessingError):
        select_primary_face([])


# ---- query processing -------------------------------------------------------


def test_query_single_face_success():
    result = process_query_image(
        FIXTURE_SINGLE,
        detector=FakeDetector([_detection(0, 120, 120, 0.95)]),
        embedder=FakeEmbedder({0: _unit_vector(3)}),
    )
    assert result["success"] is True
    assert result["face_detected"] is True
    assert result["face_count"] == 1
    assert result["multiple_faces"] is False
    assert result["selected_face_index"] == 0
    assert result["embedding_dim"] == 128
    assert isinstance(result["embedding"], np.ndarray)


def test_query_no_face_reports_clean_failure():
    result = process_query_image(
        FIXTURE_SINGLE, detector=FakeDetector([]), embedder=FakeEmbedder({})
    )
    assert result["success"] is False
    assert result["face_detected"] is False
    assert result["face_count"] == 0
    assert "No face detected" in result["reason"]


def test_query_multiple_faces_selects_largest_but_reports_all():
    result = process_query_image(
        FIXTURE_SINGLE,
        detector=FakeDetector(
            [
                _detection(0, 60, 60, 0.99),
                _detection(1, 180, 180, 0.80),
                _detection(2, 90, 90, 0.92),
            ]
        ),
        embedder=FakeEmbedder({i: _unit_vector(10 + i) for i in range(3)}),
    )
    assert result["success"] is True
    assert result["face_count"] == 3
    assert result["multiple_faces"] is True
    assert result["selected_face_index"] == 1  # largest area wins
    assert result["selection_strategy"] == "largest_area"


def test_query_missing_file_reports_failure_not_exception():
    result = process_query_image(
        "tests/fixtures/does_not_exist.jpg",
        detector=FakeDetector([_detection(0, 50, 50, 0.9)]),
        embedder=FakeEmbedder({0: _unit_vector(1)}),
    )
    assert result["success"] is False
    assert result["face_detected"] is False
    assert "not found" in result["reason"]


def test_query_corrupt_file_reports_failure(tmp_path):
    bad = tmp_path / "corrupt.jpg"
    bad.write_bytes(b"\x00\x01\x02" * 500)
    result = process_query_image(
        str(bad),
        detector=FakeDetector([_detection(0, 50, 50, 0.9)]),
        embedder=FakeEmbedder({0: _unit_vector(1)}),
    )
    assert result["success"] is False
    assert "decodable" in result["reason"]


def test_query_embedding_failure_reports_failure():
    result = process_query_image(
        FIXTURE_SINGLE,
        detector=FakeDetector([_detection(0, 120, 120, 0.95)]),
        embedder=FailingEmbedder(),
    )
    assert result["success"] is False
    assert "embedding" in result["reason"].lower()


# ---- candidate processing ----------------------------------------------------


def test_candidate_embeds_every_face():
    result = process_candidate_image(
        FIXTURE_SINGLE,
        detector=FakeDetector(
            [_detection(0, 80, 80, 0.9), _detection(1, 70, 70, 0.85)]
        ),
        embedder=FakeEmbedder({0: _unit_vector(21), 1: _unit_vector(22)}),
    )
    assert result["success"] is True
    assert result["face_detected"] is True
    assert result["face_count"] == 2
    assert len(result["embeddings"]) == 2
    assert len(result["faces"]) == 2


def test_candidate_no_face_reports_failure():
    result = process_candidate_image(
        FIXTURE_SINGLE, detector=FakeDetector([]), embedder=FakeEmbedder({})
    )
    assert result["success"] is False
    assert result["face_detected"] is False
    assert "No face detected" in result["reason"]


def test_candidate_partial_embedding_failure_keeps_good_faces():
    class PartialEmbedder:
        def embed_detection(self, image_bgr, detection):
            if detection.index == 0:
                raise FaceProcessingError("bad face chip")
            return _unit_vector(33)

    result = process_candidate_image(
        FIXTURE_SINGLE,
        detector=FakeDetector(
            [_detection(0, 80, 80, 0.9), _detection(1, 70, 70, 0.85)]
        ),
        embedder=PartialEmbedder(),
    )
    assert result["success"] is True
    assert result["face_count"] == 2  # detection count preserved
    assert len(result["embeddings"]) == 1  # only the good face embedded


def test_candidate_all_embeddings_fail_reports_failure():
    result = process_candidate_image(
        FIXTURE_SINGLE,
        detector=FakeDetector([_detection(0, 80, 80, 0.9)]),
        embedder=FailingEmbedder(),
    )
    assert result["success"] is False
    assert "embedding failed" in result["reason"]
