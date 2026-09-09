"""Unit tests for src/matching/matcher.py (no models, no network).

A routing fake detector serves per-image detections so the full
candidate-handling logic (ranking, thresholds, skips, multi-face max)
is exercised against real image files.
"""

import numpy as np
import pytest

from src.face.detector import FaceDetection
from src.matching.matcher import (
    MatchReport,
    match_candidates,
    to_matched_result,
)
from src.models.candidate import Candidate

FIXTURE_SINGLE = "tests/fixtures/single_face.jpg"
FIXTURE_GROUP = "tests/fixtures/group_faces.jpg"
FIXTURE_NO_FACE_FILE = "tests/fixtures/no_face.jpg"


def _detection(index: int, size: int = 100, confidence: float = 0.9) -> FaceDetection:
    return FaceDetection(
        bbox=(5, 5, size, size),
        landmarks=[(0.0, 0.0)] * 5,
        confidence=confidence,
        area=size * size,
        raw=np.zeros(15, dtype=np.float32),
        index=index,
    )


class RoutingFakeDetector:
    """Serve detections based on which file is being processed.

    ``cv2.imread`` output differs per file, so route on image bytes hash via
    a caller-supplied list of (path, detections) pairs matched by reading
    the same file the processor reads. Simpler: tests copy fixtures to
    distinct tmp paths and register detections per path.
    """

    def __init__(self):
        self.by_signature: dict[bytes, list[FaceDetection]] = {}

    def register_path(self, path: str, detections: list[FaceDetection]) -> None:
        import cv2

        image = cv2.imread(path)
        self.by_signature[image.tobytes()[::997]] = detections

    def detect(self, image_bgr):
        return list(self.by_signature.get(image_bgr.tobytes()[::997], []))


class RoutingFakeEmbedder:
    """Serve embeddings per (image, detection index)."""

    def __init__(self, detector: RoutingFakeDetector):
        self._detector = detector
        self.by_signature: dict[tuple[bytes, int], np.ndarray] = {}

    def register(self, path: str, index: int, embedding: np.ndarray) -> None:
        import cv2

        image = cv2.imread(path)
        self.by_signature[(image.tobytes()[::997], index)] = embedding

    def embed_detection(self, image_bgr, detection):
        return self.by_signature[(image_bgr.tobytes()[::997], detection.index)]


def _unit_vector(seed: int, dim: int = 128) -> np.ndarray:
    rng = np.random.RandomState(seed)
    vector = rng.randn(dim).astype(np.float32)
    return vector / np.linalg.norm(vector)


def _candidate(candidate_id: str, local_path, status: str = "success") -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        page_url=f"https://example.com/{candidate_id}",
        image_url=f"https://example.com/{candidate_id}.jpg",
        thumbnail_url=f"https://example.com/{candidate_id}_thumb.jpg",
        title=f"Title {candidate_id}",
        platform="Example",
        snippet=f"Snippet {candidate_id}",
        local_image_path=local_path,
        retrieval_status=status,
        metadata={"position": 1},
    )


@pytest.fixture()
def rig(tmp_path):
    """Three distinct local candidate images routed to fake faces."""
    import shutil

    detector = RoutingFakeDetector()
    embedder = RoutingFakeEmbedder(detector)

    paths = {}
    # NOTE: each routed path must have distinct bytes (routing is by content
    # sample). Fixture *content* is irrelevant here — the detector is faked.
    for name, fixture in (
        ("a", FIXTURE_SINGLE),
        ("b", FIXTURE_GROUP),
        ("c", FIXTURE_NO_FACE_FILE),
    ):
        dest = str(tmp_path / f"{name}.jpg")
        shutil.copyfile(fixture, dest)
        paths[name] = dest
    return detector, embedder, paths


def test_ranking_is_descending_by_similarity(rig):
    detector, embedder, paths = rig
    query = _unit_vector(100)
    near = query  # similarity 1.0
    mid = _unit_vector(101)
    # force mid similarity into a known band by blending
    mid = (query + 0.6 * mid)
    mid = (mid / np.linalg.norm(mid)).astype(np.float32)
    far = _unit_vector(102)

    detector.register_path(paths["a"], [_detection(0)])
    embedder.register(paths["a"], 0, mid)
    detector.register_path(paths["b"], [_detection(0)])
    embedder.register(paths["b"], 0, far)
    detector.register_path(paths["c"], [_detection(0)])
    embedder.register(paths["c"], 0, near)

    report = match_candidates(
        query,
        [_candidate("candidate_001", paths["a"]),
         _candidate("candidate_002", paths["b"]),
         _candidate("candidate_003", paths["c"])],
        threshold=0.0,
        detector=detector,
        embedder=embedder,
    )
    assert isinstance(report, MatchReport)
    assert report.matched is True
    order = [m.candidate_id for m in report.ranked]
    assert order == ["candidate_003", "candidate_001", "candidate_002"]
    sims = [m.similarity for m in report.ranked]
    assert sims == sorted(sims, reverse=True)
    assert report.best_match.candidate_id == "candidate_003"


def test_threshold_filters_weak_matches_without_fabrication(rig):
    detector, embedder, paths = rig
    query = _unit_vector(200)
    weak = _unit_vector(201)  # random pair: low cosine

    detector.register_path(paths["a"], [_detection(0)])
    embedder.register(paths["a"], 0, weak)

    report = match_candidates(
        query,
        [_candidate("candidate_001", paths["a"])],
        threshold=0.95,
        detector=detector,
        embedder=embedder,
    )
    assert report.matched is False
    assert report.best_match is None
    assert "threshold" in report.reason
    # ...but the honest ranking is still preserved.
    assert len(report.ranked) == 1
    assert report.ranked[0].matchable is True
    assert report.ranked[0].above_threshold is False


def test_candidate_with_no_face_is_skipped_not_fatal(rig):
    detector, embedder, paths = rig
    query = _unit_vector(300)

    detector.register_path(paths["a"], [])  # no face
    detector.register_path(paths["c"], [_detection(0)])
    embedder.register(paths["c"], 0, query.copy())

    report = match_candidates(
        query,
        [_candidate("candidate_001", paths["a"]),
         _candidate("candidate_002", paths["c"])],
        threshold=0.5,
        detector=detector,
        embedder=embedder,
    )
    assert report.matched is True
    assert report.best_match.candidate_id == "candidate_002"
    skipped = [m for m in report.ranked if not m.matchable]
    assert len(skipped) == 1
    assert skipped[0].candidate_id == "candidate_001"
    assert "No face detected" in skipped[0].reason


def test_missing_and_failed_candidates_are_skipped(rig):
    detector, embedder, paths = rig
    query = _unit_vector(400)

    detector.register_path(paths["c"], [_detection(0)])
    embedder.register(paths["c"], 0, query.copy())

    report = match_candidates(
        query,
        [
            _candidate("candidate_001", None),  # no local path
            _candidate("candidate_002", str(paths["c"]) + ".missing"),  # not on disk
            _candidate("candidate_003", None, status="failed"),  # failed retrieval
            _candidate("candidate_004", paths["c"]),  # good one
        ],
        threshold=0.5,
        detector=detector,
        embedder=embedder,
    )
    assert report.matched is True
    assert report.best_match.candidate_id == "candidate_004"
    assert report.stats["matchable"] == 1
    assert report.stats["unmatchable"] == 3


def test_corrupt_candidate_image_is_skipped(tmp_path):
    detector = RoutingFakeDetector()
    embedder = RoutingFakeEmbedder(detector)
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image" * 100)
    query = _unit_vector(500)

    report = match_candidates(
        query,
        [_candidate("candidate_001", str(bad))],
        threshold=0.5,
        detector=detector,
        embedder=embedder,
    )
    assert report.matched is False
    assert report.ranked[0].matchable is False
    assert "decodable" in report.ranked[0].reason


def test_multi_face_candidate_uses_highest_similarity(rig):
    detector, embedder, paths = rig
    query = _unit_vector(600)
    stranger = _unit_vector(601)

    detector.register_path(
        paths["b"], [_detection(0, size=120), _detection(1, size=90)]
    )
    embedder.register(paths["b"], 0, stranger)  # low score face
    embedder.register(paths["b"], 1, query.copy())  # the matching person

    report = match_candidates(
        query,
        [_candidate("candidate_001", paths["b"])],
        threshold=0.5,
        detector=detector,
        embedder=embedder,
    )
    assert report.matched is True
    match = report.ranked[0]
    assert match.candidate_face_count == 2
    assert match.similarity == pytest.approx(1.0)
    assert match.metadata["best_face_index"] == 1
    assert len(match.metadata["face_scores"]) == 2


def test_empty_candidate_list_reports_no_match():
    report = match_candidates(_unit_vector(700), [], threshold=0.5)
    assert report.matched is False
    assert report.best_match is None
    assert "No candidates" in report.reason


def test_empty_query_embedding_raises():
    with pytest.raises(ValueError):
        match_candidates(
            np.array([]), [_candidate("candidate_001", FIXTURE_NO_FACE_FILE)]
        )


def test_to_matched_result_has_person3_contract(rig):
    detector, embedder, paths = rig
    query = _unit_vector(800)
    detector.register_path(paths["a"], [_detection(0)])
    embedder.register(paths["a"], 0, query.copy())

    candidate = _candidate("candidate_001", paths["a"])
    report = match_candidates(
        query, [candidate], threshold=0.5, detector=detector, embedder=embedder
    )
    assert report.matched is True
    result = to_matched_result(report.best_match, candidate)
    assert result["url"] == candidate.page_url
    assert result["platform"] == "Example"
    assert result["similarity"] == pytest.approx(1.0)
    assert result["image_url"] == candidate.image_url
    assert result["content"] == candidate.snippet
    assert isinstance(result["metadata"], dict)
    assert result["metadata"]["candidate_id"] == "candidate_001"


def test_report_to_dict_contains_no_embeddings(rig):
    detector, embedder, paths = rig
    query = _unit_vector(900)
    detector.register_path(paths["a"], [_detection(0)])
    embedder.register(paths["a"], 0, query.copy())

    report = match_candidates(
        query,
        [_candidate("candidate_001", paths["a"])],
        threshold=0.5,
        detector=detector,
        embedder=embedder,
    )
    import json

    payload = json.dumps(report.to_dict())  # must be JSON-serializable
    assert "embedding" not in payload.lower()
