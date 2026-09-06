# Architecture

## 1. High-Level Flow

```text
                   ┌─────────────────────┐
                   │    Input Image      │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Face Detection      │
                   │ + Face Encoding     │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Reverse Image / Web │
                   │ Search              │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Candidate Results   │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Image / Face        │
                   │ Similarity Matching │
                   └──────────┬──────────┘
                              │
                        Match Found
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Canonical Post Data │
                   │ + SHA-256 Hash      │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Smart Contract /    │
                   │ Blockchain          │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │ Retrieve On-Chain   │
                   │ Hash + Verify       │
                   └─────────────────────┘
```

## 2. Recommended Tech Stack

### Language
- **Python 3.11+** for the application pipeline.

### Face Processing
Recommended starting options:
- InsightFace
- DeepFace
- OpenCV as supporting image-processing infrastructure

The final choice should be recorded here and in `README.md` once implementation starts.

### Search
The selected search mechanism is:
- **SerpApi — `engine=google_lens`**

Current flow:
1. Upload the local image to SerpApi's image endpoint.
2. Use the returned `image_id` with the Google Lens engine.
3. Parse `visual_matches` into normalized candidates.
4. Retrieve candidate images locally.

Requirements:
- Runtime search
- Image-driven search
- No hardcoded matching result
- Results must expose usable candidate URLs/images

Current testing:
- Binary upload works.
- Google Lens returns structured candidate results.
- Candidate parsing is implemented.
- Candidate retrieval is implemented with a main-image/thumbnail fallback.
- 10/10 candidates were retrieved successfully in the current batch test.
- Direct social-platform crawler image URLs may return HTML redirects instead of image bytes, so retrieval validates the response as an actual image.

### Matching
Possible components:
- Face embeddings + cosine similarity
- Perceptual image hashing
- OpenCV/image comparison

Preferred approach:
`face embedding → candidate face embedding → cosine similarity`

Use image-level similarity as a supporting signal when useful.

### Blockchain
Recommended architecture:
- Solidity smart contract
- Web3.py for Python integration
- Ethereum-compatible network

For development/demo reliability, a local Hardhat/Anvil-style chain is acceptable. A public testnet can be used if it is reliable enough for the final recording.

### Hashing
- Python `hashlib`
- SHA-256
- Canonical JSON representation for deterministic metadata hashing

### Configuration
Use environment variables for:
- API keys
- RPC URLs
- Private keys
- Contract addresses
- Search credentials

Never commit secrets.

## 3. Current Directory & File Structure

```text
face-id-blockchain/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── Project_Requirements.md
├── Architecture.md
├── rules.md
├── Phases.md
├── memory.md
│
├── data/
│   ├── input/
│   └── candidates/
│
├── contracts/
│   └── VerificationRegistry.sol
│
├── scripts/
│   ├── test_search.py
│   └── test_blockchain.py
│
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── candidate.py
│   │
│   ├── search/
│   │   ├── __init__.py
│   │   ├── serpapi_client.py
│   │   ├── parser.py
│   │   ├── image_utils.py
│   │   └── retriever.py
│   │
│   ├── verification/
│   │   ├── __init__.py
│   │   ├── canonicalizer.py
│   │   ├── hasher.py
│   │   └── verifier.py
│   │
│   └── blockchain/
│       ├── __init__.py
│       ├── provider.py
│       └── client.py
│
└── tests/
    ├── test_image_utils.py
    ├── test_parser.py
    ├── test_canonicalizer.py
    ├── test_hasher.py
    └── test_blockchain_verification.py
```

The structure can be expanded as the face and matching modules are implemented. Do not create files merely to match a diagram.

## 4. Component Responsibilities

### `scripts/test_search.py`
Current development entry point for testing the reverse-image-search flow.

### `scripts/test_blockchain.py`
Integration script for testing the Person 3 blockchain recording, verification, and tamper detection workflow.

### `src/models/candidate.py`
Defines the normalized `Candidate` structure used between search/retrieval and matching.

### `src/search/serpapi_client.py`
Handles local image upload to SerpApi and Google Lens search using the returned `image_id`.

### `src/search/parser.py`
Handles Lens `visual_matches`, candidate normalization, and preservation of primary image and thumbnail URLs.

### `src/search/image_utils.py`
Handles HTTP image retrieval, Pillow validation, JPEG normalization, and main-image/thumbnail fallback.

### `src/search/retriever.py`
Handles candidate image downloads, retrieval metadata, local paths, and `candidates.json`.

### `src/verification/canonicalizer.py`
Handles key-sorted, compact JSON canonicalization for deterministic payload hashing.

### `src/verification/hasher.py`
Handles SHA-256 fingerprint generation (`0x...` EVM `bytes32` format).

### `src/verification/verifier.py`
Handles local hash re-computation, on-chain record retrieval, hash comparison, and tamper detection.

### `src/blockchain/provider.py`
Provides dual-mode architecture: zero-dependency `LocalBlockchainProvider` and Web3 RPC `Web3BlockchainProvider`.

### `src/blockchain/client.py`
High-level client interface for recording and querying verification records on-chain.

### `contracts/VerificationRegistry.sol`
Solidity smart contract storing SHA-256 content hashes, URLs, platforms, timestamps, and recorder addresses.

### Future `face/`
Will handle image loading, face detection, and face embeddings.

### Future `matching/`
Will handle candidate face extraction, similarity calculation, ranking, and selection.


## 5. Data Flow

### Person 2 → Person 1

```json
{
  "candidate_id": "candidate_001",
  "page_url": "...",
  "image_url": "...",
  "thumbnail_url": "...",
  "title": "...",
  "platform": "...",
  "snippet": "...",
  "local_image_path": "data/candidates/candidate_001.jpg",
  "retrieval_status": "success",
  "metadata": {
    "position": 1,
    "source_domain": "...",
    "retrieval_source": "thumbnail"
  }
}
```

Person 1 should be able to use `local_image_path` without issuing additional network requests.

### Overall result object

```json
{
  "input_image": "...",
  "face_detected": true,
  "face_embedding": "...",
  "search_results": [],
  "matched_result": {
    "url": "...",
    "platform": "...",
    "similarity": 0.0
  },
  "content_hash": "...",
  "transaction_hash": "...",
  "blockchain_verified": true
}
```

Embeddings and binary image data do not need to be placed on-chain.

## 6. Search Provider Boundary

```text
Input Image
     │
     ▼
SerpApi Image Upload
     │
     ▼
image_id
     │
     ▼
Google Lens Search
     │
     ▼
Raw visual_matches
     │
     ▼
Candidate Parser
     │
     ▼
Normalized Candidates
     │
     ▼
Candidate Retrieval
```

A future provider can be added without changing the `Candidate` interface if it produces equivalent normalized fields.

## 7. Security Boundaries

- Secrets remain in `.env`.
- Private keys are never committed.
- Only hashes/fingerprints and necessary metadata should be stored on-chain.
- Avoid storing sensitive biometric data on a public blockchain.
- Demo with consenting subjects and publicly available content.
- Generated search caches and candidate images remain local unless explicitly needed for the repository.

## 8. Engineering Principle

The architecture separates search discovery, candidate normalization, image retrieval, face matching, verification, and blockchain recording.

A failure in one layer should be represented explicitly rather than silently converted into a successful result.
