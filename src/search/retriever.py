import json
import os

from src.models.candidate import Candidate
from src.search.image_utils import download_candidate_image


def retrieve_candidates(
    candidates: list[Candidate],
    output_dir: str = "data/candidates",
) -> list[Candidate]:
    """
    Download images for all candidates and update their retrieval metadata.
    """

    os.makedirs(output_dir, exist_ok=True)

    for candidate in candidates:
        output_path = os.path.join(
            output_dir,
            f"{candidate.candidate_id}.jpg",
        )

        print(f"\n{candidate.candidate_id}")
        print(f"Page: {candidate.page_url}")

        result = download_candidate_image(
            candidate.image_url,
            candidate.thumbnail_url,
            output_path,
        )

        if result != "failed":
            candidate.local_image_path = output_path
            candidate.retrieval_status = "success"
            candidate.metadata["retrieval_source"] = result
        else:
            candidate.retrieval_status = "failed"

    return candidates


def save_candidates(
    candidates: list[Candidate],
    output_path: str = "data/candidates/candidates.json",
) -> None:
    """
    Save normalized candidates as JSON.
    """

    data = [
        {
            "candidate_id": candidate.candidate_id,
            "page_url": candidate.page_url,
            "image_url": candidate.image_url,
            "thumbnail_url": candidate.thumbnail_url,
            "title": candidate.title,
            "platform": candidate.platform,
            "snippet": candidate.snippet,
            "local_image_path": candidate.local_image_path,
            "retrieval_status": candidate.retrieval_status,
            "metadata": candidate.metadata,
        }
        for candidate in candidates
    ]

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )