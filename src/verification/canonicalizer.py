import json
from typing import Any, Dict
from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Normalizes a URL string by stripping whitespace and lowercasing the scheme and netloc.
    """
    if not url:
        return ""
    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
        # Lowercase scheme and netloc while preserving path/query case
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        return normalized
    except Exception:
        return url_clean


def canonicalize_matched_result(matched_result: Dict[str, Any]) -> bytes:
    """
    Creates a deterministic, canonical JSON representation of a matched result payload.
    
    Canonical format guarantees:
    - Key sorting enabled (sort_keys=True)
    - Compact formatting without trailing whitespace (separators=(',', ':'))
    - Lowercased/trimmed URLs and platform strings
    - Float similarity rounded to 6 decimal places for floating-point stability
    - UTF-8 encoded bytes output
    """
    if not isinstance(matched_result, dict):
        raise ValueError(f"matched_result must be a dictionary, got {type(matched_result)}")

    # Extract fields with safe fallbacks according to project contracts
    url = normalize_url(str(matched_result.get("url") or matched_result.get("page_url") or ""))
    platform = str(matched_result.get("platform") or "").strip().lower()
    image_url = normalize_url(str(matched_result.get("image_url") or ""))
    content = str(matched_result.get("content") or matched_result.get("snippet") or matched_result.get("title") or "").strip()
    
    raw_similarity = matched_result.get("similarity", 0.0)
    try:
        similarity = round(float(raw_similarity), 6)
    except (ValueError, TypeError):
        similarity = 0.0

    metadata = matched_result.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    canonical_dict = {
        "content": content,
        "image_url": image_url,
        "metadata": metadata,
        "platform": platform,
        "similarity": similarity,
        "url": url,
    }

    # Dump deterministic UTF-8 bytes
    canonical_json_str = json.dumps(
        canonical_dict,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False
    )
    
    return canonical_json_str.encode("utf-8")
