"""Unit tests for src/matching/similarity.py (no models, no network)."""

import numpy as np
import pytest

from src.matching.similarity import (
    cosine_similarity,
    is_phash_available,
    phash_similarity,
)

FIXTURE_SINGLE = "tests/fixtures/single_face.jpg"
FIXTURE_GROUP = "tests/fixtures/group_faces.jpg"


def _normalized(vector) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float64)
    return array / np.linalg.norm(array)


def test_identical_embeddings_score_one():
    embedding = _normalized(np.random.RandomState(0).randn(128))
    assert cosine_similarity(embedding, embedding) == pytest.approx(1.0)


def test_same_direction_scores_one_despite_scale():
    base = np.random.RandomState(1).randn(128)
    assert cosine_similarity(base, base * 3.5) == pytest.approx(1.0)


def test_orthogonal_embeddings_score_zero():
    assert cosine_similarity(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)


def test_opposite_embeddings_score_minus_one():
    assert cosine_similarity(np.array([1.0, 2.0]), np.array([-1.0, -2.0])) == pytest.approx(-1.0)


def test_similar_pair_scores_higher_than_dissimilar_pair():
    rng = np.random.RandomState(42)
    query = _normalized(rng.randn(128))
    near = _normalized(query + 0.02 * rng.randn(128))  # same-face-like
    far = _normalized(rng.randn(128))  # different-face-like
    assert cosine_similarity(query, near) > 0.9
    assert cosine_similarity(query, near) > cosine_similarity(query, far)


def test_output_always_within_minus_one_to_one():
    rng = np.random.RandomState(7)
    for _ in range(50):
        score = cosine_similarity(rng.randn(128), rng.randn(128))
        assert -1.0 <= score <= 1.0


def test_zero_vector_raises():
    with pytest.raises(ValueError):
        cosine_similarity(np.zeros(128), np.ones(128))
    with pytest.raises(ValueError):
        cosine_similarity(np.ones(128), np.zeros(128))


def test_shape_mismatch_raises():
    with pytest.raises(ValueError):
        cosine_similarity(np.ones(128), np.ones(64))


def test_empty_embedding_raises():
    with pytest.raises(ValueError):
        cosine_similarity(np.array([]), np.array([]))


def test_phash_identical_image_scores_one():
    if not is_phash_available():
        pytest.skip("ImageHash not installed")
    assert phash_similarity(FIXTURE_SINGLE, FIXTURE_SINGLE) == pytest.approx(1.0)


def test_phash_different_images_score_below_one():
    if not is_phash_available():
        pytest.skip("ImageHash not installed")
    score = phash_similarity(FIXTURE_SINGLE, FIXTURE_GROUP)
    assert 0.0 <= score < 1.0


def test_phash_missing_file_raises():
    if not is_phash_available():
        pytest.skip("ImageHash not installed")
    with pytest.raises((FileNotFoundError, ValueError)):
        phash_similarity(FIXTURE_SINGLE, "tests/fixtures/does_not_exist.jpg")
