from dataclasses import dataclass, field
from typing import Any


@dataclass
class Candidate:
    """
    A single result returned by the reverse-image search layer.
    """

    candidate_id: str
    page_url: str
    image_url: str | None = None
    thumbnail_url: str | None = None
    title: str | None = None
    platform: str | None = None
    snippet: str | None = None
    local_image_path: str | None = None
    retrieval_status: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
