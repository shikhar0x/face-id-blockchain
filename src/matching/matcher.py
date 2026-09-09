"""Candidate face matching, ranking, and best-match selection (Person 1).

Pipeline per candidate::

    Candidate.local_image_path (already downloaded by Person 2 — no re-download)
        -> detect faces -> embed every face
        -> cosine similarity of EACH candidate face vs the query embedding
        -> candidate score = MAX over its faces

Multi-face rule: a candidate image may show several people; the candidate
scores the similarity of its MOST similar face to the query. The number of
faces is always reported alongside the score.

Threshold rule: a candidate is only a VALID match when
``similarity >= threshold``. When nothing passes, the report says
``matched=False`` with an honest reason — a match is never fabricated.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import numpy as np

from src.face.processor import process_candidate_image
from src.matching.similarity import (
    cosine_similarity,
    is_phash_available,
    phash_similarity,
)
from src.models.candidate import Candidate

DEFAULT_MATCH_THRESHOLD = 0.5
DEFAULT_PHASH_WEIGHT = 0.15


def get_match_threshold(override: Optional[float] = None) -> float:
    """Resolve the similarity threshold (CLI override > env > default)."""
    if override is not None:
        return float(override)
    return float(os.getenv("FACE_MATCH_THRESHOLD", str(DEFAULT_MATCH_THRESHOLD)))


@dataclass
class CandidateMatch:
    """Match outcome for a single Person-2 candidate."""

    candidate_id: str
    page_url: str
    platform: str
    title: str
    image_url: str
    thumbnail_url: str
    local_image_path: str
    similarity: Optional[float]  # None when unmatchable
    face_similarity: Optional[float]  # pure face cosine (None when unmatchable)
    phash_similarity: Optional[float]  # None unless the pHash signal was used
    face_detected: bool
    candidate_face_count: int
    matchable: bool
    above_threshold: bool
    reason: str
    retrieval_status: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe dict (embeddings are never included — privacy)."""
        data = asdict(self)
        for key in ("similarity", "face_similarity", "phash_similarity"):
            if data[key] is not None:
                data[key] = round(float(data[key]), 6)
        return data


@dataclass
class MatchReport:
    """Full ranking + selection outcome for one query face."""

    matched: bool
    reason: str
    threshold: float
    ranked: list[CandidateMatch]
    best_match: Optional[CandidateMatch]
    query_face_count: int
    query_selected_face_index: Optional[int]
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """JSON-safe dict (no biometric embeddings included)."""
        return {
            "matched": self.matched,
            "reason": self.reason,
            "threshold": self.threshold,
            "query_face_count": self.query_face_count,
            "query_selected_face_index": self.query_selected_face_index,
            "stats": dict(self.stats),
            "ranked": [match.to_dict() for match in self.ranked],
            "best_match": self.best_match.to_dict() if self.best_match else None,
        }


def _match_single_candidate(
    candidate: Candidate,
    query_embedding: np.ndarray,
    *,
    detector=None,
    embedder=None,
    query_image_path: Optional[str] = None,
    use_phash: bool = False,
    phash_weight: float = DEFAULT_PHASH_WEIGHT,
) -> CandidateMatch:
    """Score one candidate; every failure mode yields an unmatchable result."""

    def unmatchable(reason: str) -> CandidateMatch:
        return CandidateMatch(
            candidate_id=candidate.candidate_id,
            page_url=candidate.page_url or "",
            platform=candidate.platform or "",
            title=candidate.title or "",
            image_url=candidate.image_url or "",
            thumbnail_url=candidate.thumbnail_url or "",
            local_image_path=candidate.local_image_path or "",
            similarity=None,
            face_similarity=None,
            phash_similarity=None,
            face_detected=False,
            candidate_face_count=0,
            matchable=False,
            above_threshold=False,
            reason=reason,
            retrieval_status=candidate.retrieval_status,
            metadata=dict(candidate.metadata or {}),
        )

    if candidate.retrieval_status == "failed" and not candidate.local_image_path:
        return unmatchable("Candidate image retrieval failed (status=failed)")
    if not candidate.local_image_path:
        return unmatchable("Candidate has no local_image_path")
    if not os.path.isfile(candidate.local_image_path):
        return unmatchable(
            f"Candidate image not found: {candidate.local_image_path}"
        )

    processed = process_candidate_image(
        candidate.local_image_path, detector=detector, embedder=embedder
    )
    if not processed.get("success"):
        return unmatchable(str(processed.get("reason") or "Face processing failed"))

    face_count = int(processed.get("face_count", 0))
    embeddings: list[np.ndarray] = list(processed.get("embeddings") or [])
    if not embeddings:
        return unmatchable("No usable face embedding in candidate image")

    # Multi-face rule: keep the HIGHEST similarity across all faces.
    try:
        face_scores = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    except ValueError as exc:
        return unmatchable(f"Similarity computation failed: {exc}")
    best_face_score = max(face_scores)
    best_face_index = int(np.argmax(face_scores))

    combined_score = float(best_face_score)
    phash_score: Optional[float] = None
    if use_phash and query_image_path:
        if not is_phash_available():
            return unmatchable(
                "Perceptual-hash signal requested but ImageHash is not installed"
            )
        try:
            phash_score = phash_similarity(query_image_path, candidate.local_image_path)
        except Exception as exc:
            return unmatchable(f"Perceptual-hash comparison failed: {exc}")
        weight = max(0.0, min(1.0, float(phash_weight)))
        combined_score = (1.0 - weight) * float(best_face_score) + weight * float(
            phash_score
        )

    metadata = dict(candidate.metadata or {})
    metadata["best_face_index"] = best_face_index
    metadata["face_scores"] = [round(float(s), 6) for s in face_scores]

    return CandidateMatch(
        candidate_id=candidate.candidate_id,
        page_url=candidate.page_url or "",
        platform=candidate.platform or "",
        title=candidate.title or "",
        image_url=candidate.image_url or "",
        thumbnail_url=candidate.thumbnail_url or "",
        local_image_path=candidate.local_image_path or "",
        similarity=float(combined_score),
        face_similarity=float(best_face_score),
        phash_similarity=(float(phash_score) if phash_score is not None else None),
        face_detected=True,
        candidate_face_count=face_count,
        matchable=True,
        above_threshold=False,  # decided by the caller against the threshold
        reason="OK",
        retrieval_status=candidate.retrieval_status,
        metadata=metadata,
    )


def match_candidates(
    query_embedding: np.ndarray,
    candidates: list[Candidate],
    *,
    threshold: Optional[float] = None,
    detector=None,
    embedder=None,
    query_image_path: Optional[str] = None,
    query_face_count: int = 1,
    query_selected_face_index: Optional[int] = None,
    use_phash: bool = False,
    phash_weight: float = DEFAULT_PHASH_WEIGHT,
) -> MatchReport:
    """Rank Person-2 candidates against a query embedding.

    Args:
        query_embedding: L2-normalized query face embedding.
        candidates: Person-2 :class:`Candidate` objects (uses only
            ``local_image_path`` — no network requests are issued here).
        threshold: minimum similarity for a valid match (default from
            ``FACE_MATCH_THRESHOLD`` env or 0.5).
        use_phash: when True, blend the optional perceptual-hash signal
            (default False — face similarity stays the primary signal).

    Returns:
        MatchReport with candidates ranked by descending similarity
        (matchable first), plus the best valid match or ``matched=False``.
    """
    resolved_threshold = get_match_threshold(threshold)

    query_vector = np.asarray(query_embedding, dtype=np.float64).reshape(-1)
    if query_vector.size == 0:
        raise ValueError("match_candidates() requires a non-empty query embedding.")

    ranked: list[CandidateMatch] = []
    for candidate in candidates or []:
        try:
            match = _match_single_candidate(
                candidate,
                query_vector,
                detector=detector,
                embedder=embedder,
                query_image_path=query_image_path,
                use_phash=use_phash,
                phash_weight=phash_weight,
            )
        except Exception as exc:  # one bad candidate must never kill the run
            match = CandidateMatch(
                candidate_id=getattr(candidate, "candidate_id", "unknown"),
                page_url=getattr(candidate, "page_url", "") or "",
                platform=getattr(candidate, "platform", "") or "",
                title=getattr(candidate, "title", "") or "",
                image_url=getattr(candidate, "image_url", "") or "",
                thumbnail_url=getattr(candidate, "thumbnail_url", "") or "",
                local_image_path=getattr(candidate, "local_image_path", "") or "",
                similarity=None,
                face_similarity=None,
                phash_similarity=None,
                face_detected=False,
                candidate_face_count=0,
                matchable=False,
                above_threshold=False,
                reason=f"Unexpected matching error: {exc}",
                retrieval_status=getattr(candidate, "retrieval_status", "unknown"),
                metadata=dict(getattr(candidate, "metadata", {}) or {}),
            )
        if match.matchable and match.similarity is not None:
            match.above_threshold = bool(match.similarity >= resolved_threshold)
        ranked.append(match)

    # Ranked: matchable by descending similarity, then unmatchable as-is.
    matchable = sorted(
        [m for m in ranked if m.matchable],
        key=lambda m: float(m.similarity if m.similarity is not None else -2.0),
        reverse=True,
    )
    unmatchable = [m for m in ranked if not m.matchable]
    ranked = matchable + unmatchable

    valid = [m for m in matchable if m.above_threshold]
    best_match = valid[0] if valid else None

    if best_match is not None:
        matched = True
        reason = (
            f"Best match {best_match.candidate_id} "
            f"(similarity={best_match.similarity:.4f} >= {resolved_threshold:.2f})"
        )
    elif matchable:
        matched = False
        top = matchable[0]
        reason = (
            f"No candidate exceeded similarity threshold "
            f"(best={top.similarity:.4f} < {resolved_threshold:.2f})"
        )
    elif ranked:
        matched = False
        reason = "No matchable candidate (no usable face found in any candidate)"
    else:
        matched = False
        reason = "No candidates to match"

    stats = {
        "total_candidates": len(ranked),
        "matchable": len(matchable),
        "unmatchable": len(unmatchable),
        "above_threshold": len(valid),
        "use_phash": bool(use_phash),
    }

    return MatchReport(
        matched=matched,
        reason=reason,
        threshold=resolved_threshold,
        ranked=ranked,
        best_match=best_match,
        query_face_count=int(query_face_count),
        query_selected_face_index=query_selected_face_index,
        stats=stats,
    )


def to_matched_result(match: CandidateMatch, candidate: Candidate) -> dict[str, Any]:
    """Convert the winning match into the Person-3 ``matched_result`` format.

    Expected keys: url, platform, similarity, image_url, content, metadata.
    """
    content = (candidate.snippet or candidate.title or "").strip()
    metadata = dict(candidate.metadata or {})
    metadata.update(
        {
            "candidate_id": match.candidate_id,
            "title": candidate.title or "",
            "thumbnail_url": candidate.thumbnail_url or "",
            "local_image_path": match.local_image_path,
            "candidate_face_count": match.candidate_face_count,
            "retrieval_status": match.retrieval_status,
            "face_similarity": (
                round(float(match.face_similarity), 6)
                if match.face_similarity is not None
                else None
            ),
        }
    )
    if match.phash_similarity is not None:
        metadata["phash_similarity"] = round(float(match.phash_similarity), 6)

    return {
        "url": candidate.page_url or "",
        "platform": (candidate.platform or "").strip(),
        "similarity": round(float(match.similarity or 0.0), 6),
        "image_url": candidate.image_url or "",
        "content": content,
        "metadata": metadata,
    }
