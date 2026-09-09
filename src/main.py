#!/usr/bin/env python3
"""End-to-end CLI: face identification + blockchain verification (all 3 modules).

Pipeline::

    INPUT IMAGE
         |
    [Person 1] FACE DETECTION + FACE EMBEDDING (YuNet + SFace)
         |
    [Person 2] REVERSE IMAGE SEARCH (SerpApi Google Lens) + CANDIDATE RETRIEVAL
         |
    [Person 1] FACE MATCHING + RANKING + BEST-MATCH SELECTION
         |
    [Person 3] CANONICALIZATION + SHA-256
         |
    [Person 3] BLOCKCHAIN RECORD + RETRIEVAL + HASH VERIFICATION

Usage:
    python src/main.py --image sample/input.jpg
    python src/main.py --image sample/input.jpg --limit 10 --threshold 0.5
    python src/main.py --image sample/input.jpg --candidates-json data/candidates/candidates.json

Exit codes:
    0 - VERIFIED (full pipeline succeeded)
    2 - input / face-processing failure (missing file, no face, model error)
    3 - search / matching failure (API error, no candidates, no match)
    4 - blockchain / verification failure (record or hash-mismatch failure)
    1 - unexpected error
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Allow running as `python src/main.py` from the repository root.
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.face.errors import FaceModelError  # noqa: E402
from src.face.processor import describe_query_result, process_query_image  # noqa: E402
from src.matching.matcher import get_match_threshold, match_candidates, to_matched_result  # noqa: E402
from src.models.candidate import Candidate  # noqa: E402

EXIT_OK = 0
EXIT_INPUT_FACE = 2
EXIT_SEARCH_MATCH = 3
EXIT_BLOCKCHAIN = 4
EXIT_UNEXPECTED = 1

CANDIDATE_JSON_FIELDS = (
    "candidate_id",
    "page_url",
    "image_url",
    "thumbnail_url",
    "title",
    "platform",
    "snippet",
    "local_image_path",
    "retrieval_status",
    "metadata",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Face identification + blockchain verification pipeline."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input image containing a face.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of search candidates to process (default: 10).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Face-match similarity threshold (default: FACE_MATCH_THRESHOLD or 0.5).",
    )
    parser.add_argument(
        "--candidates-json",
        default=None,
        help=(
            "Reuse a previously retrieved candidates.json instead of running "
            "a live SerpApi search (saves API quota; the reuse is reported)."
        ),
    )
    parser.add_argument(
        "--use-phash",
        action="store_true",
        help=(
            "Blend the optional perceptual-hash image signal with face "
            "similarity (face stays the primary signal)."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="data/candidates",
        help="Directory for candidates.json + match_report.json (default: data/candidates).",
    )
    return parser


def load_candidates_from_json(path: str) -> list[Candidate]:
    """Load Person-2 candidates from a cached candidates.json file."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Candidates file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, list):
        raise ValueError(f"Candidates file must contain a JSON list: {path}")
    candidates: list[Candidate] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        kwargs = {key: item.get(key) for key in CANDIDATE_JSON_FIELDS if key in item}
        kwargs.setdefault("candidate_id", f"candidate_{len(candidates) + 1:03d}")
        kwargs.setdefault("page_url", "")
        kwargs.setdefault("retrieval_status", "unknown")
        kwargs.setdefault("metadata", {})
        candidates.append(Candidate(**kwargs))
    return candidates


def run_search(image_path: str, limit: int) -> tuple[list[Candidate], bool]:
    """Run the live Person-2 reverse-image-search pipeline.

    Returns (candidates, searched_live). Raises RuntimeError with a clear
    message when the search cannot run.
    """
    try:
        from src.search.parser import parse_visual_matches
        from src.search.retriever import retrieve_candidates, save_candidates
        from src.search.serpapi_client import google_lens_search, upload_image
    except ImportError as exc:
        raise RuntimeError(f"Search module import failed: {exc}") from exc

    if not os.getenv("SERPAPI_KEY"):
        # serpapi_client reads the key at import; re-check env for a clear error.
        from src.search import serpapi_client

        if not getattr(serpapi_client, "SERPAPI_KEY", None):
            raise RuntimeError(
                "SERPAPI_KEY is not configured. Set it in a .env file "
                "(see .env.example) or pass --candidates-json to reuse "
                "previously retrieved candidates."
            )

    try:
        print("      Uploading image to SerpApi...")
        image_id = upload_image(image_path)
        print(f"      Upload OK (image_id={image_id}). Running Google Lens search...")
        results = google_lens_search(image_id)
    except Exception as exc:
        raise RuntimeError(f"Reverse image search failed: {exc}") from exc

    try:
        candidates = parse_visual_matches(results, limit=limit)
    except Exception as exc:
        raise RuntimeError(f"Search-result parsing failed: {exc}") from exc

    if not candidates:
        raise RuntimeError("Search returned zero usable candidates.")

    try:
        candidates = retrieve_candidates(candidates)
        save_candidates(candidates)
    except Exception as exc:
        raise RuntimeError(f"Candidate retrieval failed: {exc}") from exc

    return candidates, True


def print_ranking(report) -> None:
    print("      Ranked candidates (face similarity, descending):")
    for position, match in enumerate(report.ranked, start=1):
        if match.matchable and match.similarity is not None:
            flag = "MATCH" if match.above_threshold else "below threshold"
            print(
                f"      {position:>2}. {match.candidate_id} "
                f"similarity={match.similarity:.4f} "
                f"(faces={match.candidate_face_count}) [{flag}]"
            )
            print(f"          {match.page_url}")
        else:
            print(f"      {position:>2}. {match.candidate_id} SKIPPED: {match.reason}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    threshold = get_match_threshold(args.threshold)

    print("=" * 50)
    print("FACE ID + BLOCKCHAIN VERIFICATION")
    print("=" * 50)
    print()

    # ---- [1/8] Input image ------------------------------------------------
    print("[1/8] Loading input image...")
    if not os.path.isfile(args.image):
        print(f"      ERROR: input file not found: {args.image}")
        return EXIT_INPUT_FACE
    print(f"      Input: {args.image}")

    # ---- [2/8] + [3/8] Face detection + embedding (Person 1) --------------
    print()
    print("[2/8] Detecting face...")
    try:
        query = process_query_image(args.image)
    except FaceModelError as exc:
        print(f"      ERROR: {exc}")
        return EXIT_INPUT_FACE
    except Exception as exc:  # pragma: no cover - defensive
        print(f"      ERROR: unexpected face-processing failure: {exc}")
        return EXIT_INPUT_FACE

    if not query.get("success"):
        print(f"      Face detected: NO ({query.get('reason')})")
        return EXIT_INPUT_FACE

    print(f"      {describe_query_result(query)}")
    print()
    print("[3/8] Generating face embedding...")
    print(
        f"      Embedding OK "
        f"(dim={query.get('embedding_dim')}, "
        f"strategy={query.get('selection_strategy')})"
    )

    # ---- [4/8] Reverse image search (Person 2) ----------------------------
    print()
    print("[4/8] Running reverse image search...")
    candidates: list[Candidate] = []
    searched_live = False
    try:
        if args.candidates_json:
            print(f"      Reusing cached candidates: {args.candidates_json}")
            print("      (No live search performed; SerpApi quota untouched.)")
            candidates = load_candidates_from_json(args.candidates_json)[: args.limit]
            searched_live = False
        else:
            candidates, searched_live = run_search(
                args.image, args.limit, args.output_dir
            )
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"      ERROR: {exc}")
        return EXIT_SEARCH_MATCH
    except Exception as exc:  # pragma: no cover - defensive
        print(f"      ERROR: unexpected search failure: {exc}")
        return EXIT_SEARCH_MATCH

    if not candidates:
        print("      ERROR: no candidates available for matching.")
        return EXIT_SEARCH_MATCH
    print(f"      Candidates found: {len(candidates)} (live search: {searched_live})")

    # ---- [5/8] Face matching (Person 1) -----------------------------------
    print()
    print("[5/8] Matching candidate faces...")
    print(f"      Threshold: {threshold} (cosine similarity, higher = more similar)")
    try:
        report = match_candidates(
            query["embedding"],
            candidates,
            threshold=threshold,
            query_image_path=args.image,
            query_face_count=int(query.get("face_count", 1)),
            query_selected_face_index=query.get("selected_face_index"),
            use_phash=args.use_phash,
        )
    except Exception as exc:  # pragma: no cover - defensive
        print(f"      ERROR: matching failed unexpectedly: {exc}")
        return EXIT_SEARCH_MATCH

    print_ranking(report)
    print(
        f"      Stats: {report.stats.get('matchable', 0)} matchable / "
        f"{report.stats.get('unmatchable', 0)} skipped / "
        f"{report.stats.get('above_threshold', 0)} above threshold"
    )

    # Persist the ranking (no embeddings — privacy).
    try:
        os.makedirs(args.output_dir, exist_ok=True)
        report_path = os.path.join(args.output_dir, "match_report.json")
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(report.to_dict(), handle, indent=2, ensure_ascii=False)
        print(f"      Ranking saved to: {report_path}")
    except OSError as exc:
        print(f"      WARNING: could not save match report: {exc}")

    if not report.matched or report.best_match is None:
        print()
        print("[6/8] Best match")
        print(f"      NO VALID MATCH: {report.reason}")
        print("      (Refusing to fabricate a match — see ranked list above.)")
        return EXIT_SEARCH_MATCH

    best = report.best_match
    winner = next(
        (c for c in candidates if c.candidate_id == best.candidate_id), None
    )
    if winner is None:  # pragma: no cover - defensive, cannot happen
        print("      ERROR: best match has no corresponding candidate.")
        return EXIT_SEARCH_MATCH

    matched_result = to_matched_result(best, winner)

    print()
    print("[6/8] Best match")
    print(f"      Candidate: {best.candidate_id}")
    print(f"      URL: {matched_result['url']}")
    print(f"      Platform: {matched_result['platform']}")
    print(f"      Similarity: {matched_result['similarity']:.4f}")
    print(
        "      NOTE: similarity is a technical matching signal, "
        "not proof of identity."
    )

    # ---- [7/8] Hash + blockchain record (Person 3) ------------------------
    print()
    print("[7/8] Recording verification on blockchain...")
    try:
        from src.blockchain.client import BlockchainClient
        from src.verification.hasher import compute_content_hash
        from src.verification.verifier import verify_match_record
    except ImportError as exc:
        print(f"      ERROR: blockchain module import failed: {exc}")
        return EXIT_BLOCKCHAIN

    try:
        hash_info = compute_content_hash(matched_result)
        print(f"      Content hash: {hash_info['content_hash']}")
        client = BlockchainClient()
        receipt = client.record_hash(
            hash_info["bytes32_hex"],
            page_url=matched_result["url"],
            platform=matched_result["platform"],
        )
        print(f"      Transaction: {receipt.get('transaction_hash')}")
        print(f"      Block: {receipt.get('block_number')}")
        print(f"      Contract: {receipt.get('contract_address')}")
    except Exception as exc:
        print(f"      ERROR: blockchain recording failed: {exc}")
        return EXIT_BLOCKCHAIN

    # ---- [8/8] Verification (Person 3) ------------------------------------
    print()
    print("[8/8] Verifying blockchain record...")
    try:
        verification = verify_match_record(matched_result, blockchain_client=client)
    except Exception as exc:
        print(f"      ERROR: blockchain verification failed: {exc}")
        return EXIT_BLOCKCHAIN

    print(f"      Local hash:    {verification.get('content_hash')}")
    print(f"      On-chain hash: {verification.get('on_chain_hash')}")
    print(f"      Details: {verification.get('details')}")
    print()
    print("=" * 50)
    if verification.get("verified"):
        print("VERIFIED")
        print("=" * 50)
        return EXIT_OK
    print("NOT VERIFIED / TAMPERED")
    print("=" * 50)
    return EXIT_BLOCKCHAIN


if __name__ == "__main__":
    sys.exit(main())
