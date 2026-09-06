"""
Verification module for canonicalization, SHA-256 fingerprinting, and tamper detection.
"""

from src.verification.canonicalizer import canonicalize_matched_result
from src.verification.hasher import compute_content_hash
from src.verification.verifier import verify_match_record

__all__ = [
    "canonicalize_matched_result",
    "compute_content_hash",
    "verify_match_record",
]
