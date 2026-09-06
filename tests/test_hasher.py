from src.verification.hasher import compute_content_hash


def test_compute_content_hash_format():
    payload = {
        "url": "https://test.com",
        "platform": "instagram",
        "similarity": 0.88,
        "content": "Sample post"
    }

    result = compute_content_hash(payload)

    assert "content_hash" in result
    assert "bytes32_hex" in result
    assert "canonical_data" in result

    # SHA-256 hex string should be 64 characters
    assert len(result["content_hash"]) == 64
    # EVM bytes32 string should start with 0x and be 66 characters long
    assert result["bytes32_hex"].startswith("0x")
    assert len(result["bytes32_hex"]) == 66


def test_compute_content_hash_sensitivity():
    payload_a = {"url": "https://test.com", "content": "Original"}
    payload_b = {"url": "https://test.com", "content": "Modified"}

    hash_a = compute_content_hash(payload_a)
    hash_b = compute_content_hash(payload_b)

    assert hash_a["content_hash"] != hash_b["content_hash"]
    assert hash_a["bytes32_hex"] != hash_b["bytes32_hex"]
