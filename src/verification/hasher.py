import hashlib
from typing import Any, Dict
from src.verification.canonicalizer import canonicalize_matched_result


def compute_content_hash(matched_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a deterministic SHA-256 fingerprint for a matched result payload.
    
    Returns:
        dict containing:
            - content_hash: 64-character SHA-256 hex string
            - bytes32_hex: 0x-prefixed 66-character string suitable for Web3 / EVM smart contracts
            - canonical_data: string representation of the canonical payload
    """
    canonical_bytes = canonicalize_matched_result(matched_result)
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    bytes32_hex = f"0x{sha256_hex}"

    return {
        "content_hash": sha256_hex,
        "bytes32_hex": bytes32_hex,
        "canonical_data": canonical_bytes.decode("utf-8"),
    }
