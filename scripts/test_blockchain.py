#!/usr/bin/env python3
"""
Integration test script for Person 3 — Blockchain & Verification module.
Demonstrates:
1. Matched result input payload (Person 1 → Person 3 contract)
2. Canonicalization & SHA-256 fingerprinting
3. Smart contract / blockchain record storage & transaction generation
4. On-chain record retrieval & verification (VERIFIED)
5. Tamper test — modifying post data and re-verifying (NOT VERIFIED)
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.verification.hasher import compute_content_hash
from src.verification.verifier import verify_match_record
from src.blockchain.client import BlockchainClient


def main():
    print("==================================================================")
    print("      HH GOA 2026 TASK 3 — PERSON 3: BLOCKCHAIN & VERIFICATION    ")
    print("==================================================================\n")

    # Step 1: Simulated matched_result payload from Person 1 (Candidate Matcher)
    sample_matched_result = {
        "url": "https://github.com/shikhar0x/face-id-blockchain",
        "platform": "github",
        "image_url": "https://github.com/shikhar0x/face-id-blockchain/raw/main/sample.jpg",
        "content": "HH Goa 2026 Shortlisting Task 3 Candidate Profile",
        "similarity": 0.965432,
        "metadata": {
            "candidate_id": "candidate_001",
            "source_domain": "github.com"
        }
    }

    print("--- STEP 1: MATCHED RESULT INPUT ---")
    print(f"URL:        {sample_matched_result['url']}")
    print(f"Platform:   {sample_matched_result['platform']}")
    print(f"Similarity: {sample_matched_result['similarity']}")
    print(f"Content:    '{sample_matched_result['content']}'\n")

    # Step 2: Canonicalization & SHA-256 fingerprinting
    print("--- STEP 2: CANONICALIZATION & SHA-256 FINGERPRINT ---")
    hash_info = compute_content_hash(sample_matched_result)
    print(f"Canonical Bytes (JSON): {hash_info['canonical_data']}")
    print(f"SHA-256 Hex:            {hash_info['content_hash']}")
    print(f"Bytes32 Format (EVM):   {hash_info['bytes32_hex']}\n")

    # Step 3: Blockchain Recording
    print("--- STEP 3: BLOCKCHAIN RECORDING ---")
    client = BlockchainClient()
    rec_tx = client.record_hash(
        bytes32_hash=hash_info['bytes32_hex'],
        page_url=sample_matched_result['url'],
        platform=sample_matched_result['platform']
    )
    print(f"Status:           {rec_tx['status'].upper()}")
    print(f"Transaction Hash: {rec_tx['transaction_hash']}")
    print(f"Block Number:     {rec_tx['block_number']}")
    print(f"Contract Address: {rec_tx['contract_address']}\n")

    # Step 4: Verification against On-Chain Record
    print("--- STEP 4: VERIFICATION & RETRIEVAL ---")
    verification = verify_match_record(sample_matched_result, blockchain_client=client)
    print(f"Verification Status: {'SUCCESS [VERIFIED]' if verification['verified'] else 'FAILED'}")
    print(f"Local Hash:          {verification['content_hash']}")
    print(f"On-Chain Hash:       {verification['on_chain_hash']}")
    print(f"Detail:              {verification['details']}\n")

    assert verification['verified'] is True, "Verification failed for unaltered data!"

    # Step 5: Tamper Test
    print("--- STEP 5: TAMPER TEST (MUTATING DATA) ---")
    tampered_result = dict(sample_matched_result)
    tampered_result["content"] = "Tampered/Altered Post Content — Fraud Attempt"

    tampered_hash_info = compute_content_hash(tampered_result)
    tampered_verification = verify_match_record(tampered_result, blockchain_client=client)

    print(f"Tampered Content:        '{tampered_result['content']}'")
    print(f"Tampered Local SHA-256:  {tampered_hash_info['content_hash']}")
    print(f"Original On-Chain Hash:  {verification['on_chain_hash']}")
    print(f"Tamper Verification Status: {'FAIL' if not tampered_verification['verified'] else 'PASSED'}")
    print(f"Detail:                  {tampered_verification['details']}\n")

    assert tampered_verification['verified'] is False, "Tamper test failed! Altered data was incorrectly verified."

    print("==================================================================")
    print("  [SUCCESS] All Blockchain & Verification requirements satisfied!  ")
    print("==================================================================")


if __name__ == "__main__":
    main()
