from typing import Any, Dict, Optional
from src.verification.hasher import compute_content_hash
from src.blockchain.client import BlockchainClient


def verify_match_record(
    matched_result: Dict[str, Any],
    blockchain_client: Optional[BlockchainClient] = None
) -> Dict[str, Any]:
    """
    Verifies a matched result payload against the blockchain.
    
    Flow:
    1. Recomputes local canonical SHA-256 hash.
    2. Queries the recorded hash on the blockchain.
    3. Compares the recomputed local hash against the retrieved on-chain hash.
    4. Returns verification status and evidence.
    """
    if blockchain_client is None:
        blockchain_client = BlockchainClient()

    # Step 1: Local hash computation
    hash_result = compute_content_hash(matched_result)
    local_sha256 = hash_result["content_hash"]
    local_bytes32 = hash_result["bytes32_hex"]

    # Step 2: Query blockchain
    on_chain_record = blockchain_client.get_record(local_bytes32)

    exists = on_chain_record.get("exists", False)
    on_chain_bytes32 = on_chain_record.get("content_hash", "")
    on_chain_sha256 = on_chain_bytes32.replace("0x", "").lower()
    tx_hash = on_chain_record.get("transaction_hash", "")
    timestamp = on_chain_record.get("timestamp", 0)

    # Step 3: Comparison
    is_verified = exists and (local_sha256 == on_chain_sha256)

    if is_verified:
        details = "VERIFIED: Local SHA-256 fingerprint exactly matches recorded on-chain record."
    elif not exists:
        details = "NOT VERIFIED: No record found on-chain for this content fingerprint."
    else:
        details = f"NOT VERIFIED: Mismatch detected! Local hash ({local_sha256}) != On-chain hash ({on_chain_sha256})."

    return {
        "verified": is_verified,
        "content_hash": local_sha256,
        "bytes32_hex": local_bytes32,
        "on_chain_hash": on_chain_bytes32,
        "transaction_hash": tx_hash,
        "timestamp": timestamp,
        "details": details,
        "canonical_data": hash_result["canonical_data"],
        "on_chain_record": on_chain_record,
    }
