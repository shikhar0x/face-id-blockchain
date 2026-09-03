from src.models.candidate import Candidate


def parse_visual_matches(results: dict, limit: int = 10) -> list[Candidate]:
    """
    Convert raw Google Lens / SerpApi results
    into normalized Candidate objects.
    """

    visual_matches = results.get("visual_matches", [])

    candidates = []

    for index, match in enumerate(visual_matches[:limit]):
        page_url = match.get("link")

        # A result without a page URL isn't useful to Person 1.
        if not page_url:
            continue

        source = match.get("source")

        candidate = Candidate(
            candidate_id=f"candidate_{index + 1:03d}",
            page_url=page_url,
            image_url=match.get("image"),
            thumbnail_url=match.get("thumbnail"),
            title=match.get("title"),
            platform=source,
            snippet=match.get("snippet"),
            metadata={
                "position": match.get("position"),
                "source_domain": source,
                "thumbnail_url": match.get("thumbnail"),
                "original_image_url": match.get("image"),
                "image_width": match.get("image_width"),
                "image_height": match.get("image_height"),
                "thumbnail_width": match.get("thumbnail_width"),
                "thumbnail_height": match.get("thumbnail_height"),
            },
        )

        candidates.append(candidate)

    return candidates
