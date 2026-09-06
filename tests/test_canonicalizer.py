import json
import pytest
from src.verification.canonicalizer import canonicalize_matched_result, normalize_url


def test_normalize_url():
    assert normalize_url("  HTTPS://EXAMPLE.COM/Path  ") == "https://example.com/Path"
    assert normalize_url("http://domain.com") == "http://domain.com"
    assert normalize_url("") == ""


def test_canonicalize_matched_result_determinism():
    payload1 = {
        "url": "https://example.com/post1",
        "platform": "Twitter",
        "similarity": 0.95,
        "content": "Hello World",
        "image_url": "https://example.com/img.jpg",
        "metadata": {"key": "val", "a": 1}
    }

    # Different key ordering in dictionary
    payload2 = {
        "metadata": {"a": 1, "key": "val"},
        "similarity": 0.95,
        "content": "Hello World",
        "platform": "TWITTER ",
        "image_url": "https://EXAMPLE.COM/img.jpg",
        "url": "HTTPS://EXAMPLE.COM/post1"
    }

    bytes1 = canonicalize_matched_result(payload1)
    bytes2 = canonicalize_matched_result(payload2)

    assert bytes1 == bytes2
    
    # Parse back to json to check compact structure
    data = json.loads(bytes1.decode("utf-8"))
    assert data["platform"] == "twitter"
    assert data["url"] == "https://example.com/post1"
    assert data["similarity"] == 0.95


def test_canonicalize_matched_result_invalid_type():
    with pytest.raises(ValueError):
        canonicalize_matched_result("not a dict")
