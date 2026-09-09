"""Person 1 — candidate face matching and ranking."""

from __future__ import annotations

__all__ = [
    "cosine_similarity",
    "is_phash_available",
    "phash_similarity",
    "CandidateMatch",
    "MatchReport",
    "match_candidates",
    "to_matched_result",
    "get_match_threshold",
    "DEFAULT_MATCH_THRESHOLD",
]


def __getattr__(name: str):
    if name in {"cosine_similarity", "is_phash_available", "phash_similarity"}:
        from src.matching import similarity as _similarity

        return getattr(_similarity, name)
    if name in {
        "CandidateMatch",
        "MatchReport",
        "match_candidates",
        "to_matched_result",
        "get_match_threshold",
        "DEFAULT_MATCH_THRESHOLD",
    }:
        from src.matching import matcher as _matcher

        return getattr(_matcher, name)
    raise AttributeError(f"module 'src.matching' has no attribute {name!r}")
