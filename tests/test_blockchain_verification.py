from src.verification.hasher import compute_content_hash
from src.verification.verifier import verify_match_record
from src.blockchain.client import BlockchainClient
from src.blockchain.provider import LocalBlockchainProvider


def test_blockchain_record_and_verify():
    provider = LocalBlockchainProvider()
    client = BlockchainClient(provider=provider)

    matched_result = {
        "url": "https://linkedin.com/in/testuser",
        "platform": "linkedin",
        "similarity": 0.92,
        "content": "Test LinkedIn Post"
    }

    hash_info = compute_content_hash(matched_result)
    bytes32_hex = hash_info["bytes32_hex"]

    # Record on blockchain
    rec_tx = client.record_hash(bytes32_hex, page_url=matched_result["url"], platform=matched_result["platform"])
    assert rec_tx["status"] == "success"
    assert rec_tx["transaction_hash"].startswith("0x")

    # Verify on blockchain
    verification = verify_match_record(matched_result, blockchain_client=client)
    assert verification["verified"] is True
    assert verification["content_hash"] == hash_info["content_hash"]
    assert verification["bytes32_hex"] == bytes32_hex


def test_tamper_detection():
    provider = LocalBlockchainProvider()
    client = BlockchainClient(provider=provider)

    original_result = {
        "url": "https://facebook.com/post/123",
        "platform": "facebook",
        "similarity": 0.99,
        "content": "Authentic Face ID Match"
    }

    hash_info = compute_content_hash(original_result)
    client.record_hash(hash_info["bytes32_hex"], page_url=original_result["url"], platform=original_result["platform"])

    # Modify content (tampering)
    tampered_result = dict(original_result)
    tampered_result["content"] = "Fake/Tampered Content"

    tampered_verification = verify_match_record(tampered_result, blockchain_client=client)
    assert tampered_verification["verified"] is False
    assert "NOT VERIFIED" in tampered_verification["details"]


def test_unregistered_hash_verification():
    provider = LocalBlockchainProvider()
    client = BlockchainClient(provider=provider)

    unknown_result = {
        "url": "https://unknown.com/post",
        "platform": "unknown",
        "similarity": 0.50,
        "content": "Never recorded"
    }

    verification = verify_match_record(unknown_result, blockchain_client=client)
    assert verification["verified"] is False
    assert "No record found" in verification["details"]
