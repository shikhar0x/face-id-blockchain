"""Offline integration test: Person 1 match -> Person 3 hash/record/verify.

The face backend is faked (no models), but everything else is REAL code:
matcher ranking, matched_result conversion, canonicalization, SHA-256
hashing, local blockchain record/retrieval, and tamper detection.
"""

import shutil

import numpy as np
import pytest

from src.blockchain.client import BlockchainClient
from src.blockchain.provider import LocalBlockchainProvider
from src.face.detector import FaceDetection
from src.matching.matcher import match_candidates, to_matched_result
from src.models.candidate import Candidate
from src.verification.hasher import compute_content_hash
from src.verification.verifier import verify_match_record

FIXTURE_SINGLE = "tests/fixtures/single_face.jpg"
FIXTURE_GROUP = "tests/fixtures/group_faces.jpg"


def _unit_vector(seed: int, dim: int = 128) -> np.ndarray:
    rng = np.random.RandomState(seed)
    vector = rng.randn(dim).astype(np.float32)
    return vector / np.linalg.norm(vector)


class FakeDetector:
    def __init__(self, by_sig):
        self._by_sig = by_sig

    def detect(self, image_bgr):
        return list(self._by_sig.get(image_bgr.tobytes()[::997], []))


class FakeEmbedder:
    def __init__(self, by_sig):
        self._by_sig = by_sig

    def embed_detection(self, image_bgr, detection):
        return self._by_sig[(image_bgr.tobytes()[::997], detection.index)]


def _sig(path: str) -> bytes:
    import cv2

    return cv2.imread(path).tobytes()[::997]


def _face(index: int) -> FaceDetection:
    return FaceDetection(
        bbox=(5, 5, 100, 100),
        landmarks=[(0.0, 0.0)] * 5,
        confidence=0.95,
        area=10000,
        raw=np.zeros(15, dtype=np.float32),
        index=index,
    )


def test_match_to_blockchain_verified_and_tamper_detected(tmp_path):
    query = _unit_vector(11)

    # Two local candidate images: one matching face, one stranger.
    good_path = str(tmp_path / "good.jpg")
    bad_path = str(tmp_path / "bad.jpg")
    shutil.copyfile(FIXTURE_SINGLE, good_path)
    shutil.copyfile(FIXTURE_GROUP, bad_path)

    detector = FakeDetector({_sig(good_path): [_face(0)], _sig(bad_path): [_face(0)]})
    embedder = FakeEmbedder(
        {
            (_sig(good_path), 0): query.copy(),
            (_sig(bad_path), 0): _unit_vector(12),
        }
    )

    candidates = [
        Candidate(
            candidate_id="candidate_001",
            page_url="https://example.com/alice",
            image_url="https://example.com/alice.jpg",
            title="Alice Example",
            platform="Example",
            snippet="Alice's public profile photo",
            local_image_path=good_path,
            retrieval_status="success",
            metadata={"position": 1},
        ),
        Candidate(
            candidate_id="candidate_002",
            page_url="https://example.com/stranger",
            image_url="https://example.com/stranger.jpg",
            title="Someone Else",
            platform="Example",
            snippet="Unrelated photo",
            local_image_path=bad_path,
            retrieval_status="success",
            metadata={"position": 2},
        ),
    ]

    # Person 1: rank + select.
    report = match_candidates(
        query, candidates, threshold=0.5, detector=detector, embedder=embedder
    )
    assert report.matched is True
    assert report.best_match.candidate_id == "candidate_001"

    matched_result = to_matched_result(report.best_match, candidates[0])
    assert set(matched_result) == {
        "url", "platform", "similarity", "image_url", "content", "metadata",
    }

    # Person 3: hash -> record -> retrieve -> verify.
    client = BlockchainClient(provider=LocalBlockchainProvider())
    hash_info = compute_content_hash(matched_result)
    receipt = client.record_hash(
        hash_info["bytes32_hex"],
        page_url=matched_result["url"],
        platform=matched_result["platform"],
    )
    assert receipt["status"] == "success"

    verification = verify_match_record(matched_result, blockchain_client=client)
    assert verification["verified"] is True
    assert verification["content_hash"] == hash_info["content_hash"]

    # Tampered data must NOT verify against the same chain state.
    tampered = dict(matched_result)
    tampered["content"] = "Tampered content"
    tampered_check = verify_match_record(tampered, blockchain_client=client)
    assert tampered_check["verified"] is False
