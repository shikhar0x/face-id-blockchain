"""Real-model integration tests for YuNet + SFace (Person 1).

These run ONLY when the verified model files are present locally
(``python scripts/download_face_models.py``) and OpenCV is installed.
Otherwise they skip — unit tests with faked backends cover the logic.

No network access is performed by these tests (models must pre-exist).
"""

import pytest

try:
    import cv2  # noqa: F401
    import numpy as np

    from src.face.models import models_available
    from src.face.processor import process_candidate_image, process_query_image
    from src.matching.similarity import cosine_similarity

    _IMPORTS_OK = True
except ImportError:
    _IMPORTS_OK = False

MODELS_READY = _IMPORTS_OK and models_available()

pytestmark = pytest.mark.skipif(
    not MODELS_READY, reason="face models not downloaded (offline-safe skip)"
)

FIXTURE_SINGLE = "tests/fixtures/single_face.jpg"
FIXTURE_GROUP = "tests/fixtures/group_faces.jpg"
FIXTURE_NO_FACE = "tests/fixtures/no_face.jpg"


def test_real_single_face_query():
    result = process_query_image(FIXTURE_SINGLE)
    assert result["success"] is True, result.get("reason")
    assert result["face_detected"] is True
    assert result["face_count"] == 1
    assert result["embedding_dim"] == 128
    assert float(np.linalg.norm(result["embedding"])) == pytest.approx(1.0, abs=1e-4)


def test_real_group_photo_reports_multiple_faces():
    result = process_query_image(FIXTURE_GROUP)
    assert result["success"] is True, result.get("reason")
    assert result["face_count"] >= 2
    assert result["multiple_faces"] is True
    assert result["selected_face_index"] is not None


def test_real_no_face_image_fails_cleanly():
    result = process_query_image(FIXTURE_NO_FACE)
    assert result["success"] is False
    assert result["face_detected"] is False
    assert "No face detected" in result["reason"]


def test_real_candidate_processing_and_self_similarity():
    candidate = process_candidate_image(FIXTURE_SINGLE)
    assert candidate["success"] is True
    assert len(candidate["embeddings"]) >= 1

    query = process_query_image(FIXTURE_SINGLE)
    assert query["success"] is True

    # Same image -> same primary face -> similarity ~1.0.
    score = cosine_similarity(query["embedding"], candidate["embeddings"][0])
    assert score == pytest.approx(1.0, abs=1e-3)


def test_real_different_people_score_lower_than_self_match():
    a = process_query_image(FIXTURE_SINGLE)
    b = process_candidate_image(FIXTURE_GROUP)
    assert a["success"] and b["success"]

    self_score = cosine_similarity(a["embedding"], a["embedding"])
    cross_scores = [cosine_similarity(a["embedding"], emb) for emb in b["embeddings"]]
    assert max(cross_scores) < self_score
    assert all(-1.0 <= s <= 1.0 for s in cross_scores)
