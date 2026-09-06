# Project Memory

> This file is the persistent project state.
>
> **Mandatory rule:** Update this file automatically whenever a meaningful project-state change occurs. A meaningful change includes implementation completion, architecture/interface changes, technical decisions, blockers, testing results, provider behavior, file changes, phase progress, or next-action changes. The update should happen in the same development workflow/commit as the change. Do not leave `memory.md` stale and plan to update it later.

## Current Status

**Project:** HH Goa 2026 — Task 3: Face Identification & Blockchain Verification

**Overall status:** Person 2 (Search) and Person 3 (Blockchain & Verification) modules are fully completed and tested. Waiting on Person 1 (Face Processing & Matching) to finalize end-to-end pipeline integration.

**Last updated:** 2026-09-06

## Current File Being Worked On

**Current focus:** Person 3 — Blockchain & Verification module completed.

**Active implementation area:** `src/verification/` and `src/blockchain/`


## Repository State

Local repository:

```text
face-id-blockchain/
```

Current branch:

```text
main
```

Current commits include:
- `4d2ade7 Initial project structure`
- `a9949e0 Implement reverse image search and candidate retrieval`

The working tree was clean when the latest commit was checked.

## Files Created / Tracked

Project planning/state:
- `Project_Requirements.md`
- `Architecture.md`
- `rules.md`
- `Phases.md`
- `memory.md`

Application:
- `README.md`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `scripts/test_search.py`
- `src/__init__.py`
- `src/models/__init__.py`
- `src/models/candidate.py`
- `src/search/__init__.py`
- `src/search/serpapi_client.py`
- `src/search/parser.py`
- `src/search/image_utils.py`
- `src/search/retriever.py`
- `tests/test_image_utils.py`
- `tests/test_parser.py`

## Files Intentionally Not Tracked

The repository's `.gitignore` excludes:
- `.venv/`
- `.env`
- `__pycache__/`
- `*.pyc`
- `.pytest_cache/`
- `data/input/*`
- `data/candidates/*`
- `lens_results.json`

No API key should ever be committed.

## Completed

### Project Setup
- [x] Converted the hackathon task into concrete project requirements.
- [x] Defined the end-to-end pipeline.
- [x] Defined major architectural components.
- [x] Defined the three-person work split.
- [x] Defined development phases.
- [x] Defined implementation, privacy, search, blockchain, and demo rules.
- [x] Initialized the Git repository.
- [x] Created Python environment and installed current dependencies.
- [x] Created `.env.example` and `.gitignore`.

### Person 2 — Search
- [x] Researched reverse-image-search options.
- [x] Selected SerpApi Google Lens as the primary provider.
- [x] Verified runtime binary image upload to SerpApi.
- [x] Verified Google Lens runtime search.
- [x] Saved and inspected a real Lens response during development.
- [x] Implemented `Candidate` dataclass.
- [x] Implemented Lens `visual_matches` parser.
- [x] Preserved both primary `image` URL and `thumbnail` URL.
- [x] Implemented image validation and local JPEG saving.
- [x] Implemented main-image → thumbnail fallback.
- [x] Implemented batch candidate retrieval.
- [x] Implemented `candidates.json` output.
- [x] Successfully retrieved 10/10 candidates in the current batch test.

## Current Search Pipeline

```text
Input Image
    ↓
SerpApi image upload
    ↓
image_id
    ↓
Google Lens search
    ↓
raw visual_matches
    ↓
parse_visual_matches()
    ↓
Candidate objects
    ↓
download_candidate_image()
    ↓
main image URL
    ├── valid image → save
    └── HTML/non-image → thumbnail fallback
                              ↓
                         local JPEG
                              ↓
                     candidates.json
```

## Current Candidate Contract

Person 2 → Person 1:

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

Person 1 should not need to make network requests to process candidates.

## Important Technical Finding

During real testing, the Lens `image` URLs for social-platform results can return:
- HTTP 200
- `Content-Type: text/html`

with an HTML redirect instead of image bytes.

Pillow correctly rejects these responses.

The returned Lens `thumbnail` URLs were directly retrievable as valid JPEGs. The current batch test therefore:
- attempted the main image,
- detected the invalid response,
- fell back to the thumbnail,
- successfully retrieved 10/10 candidates.

This behavior is treated as a normal retrieval failure/fallback case, not hidden.

## Search/Demo Decision

Reverse-image search can return social-platform candidates, but platform indexing/access is not guaranteed.

For the final demonstration, prefer:
- a consenting team member,
- a public GitHub profile,
- a public portfolio,
- or another legitimately accessible public web page.

Do not rely on a manually preselected social-media URL.

## Not Yet Completed

### Person 1 — Face Pipeline
- [ ] Choose final face library.
- [ ] Implement face detection.
- [ ] Implement face encoding.
- [ ] Add face-processing tests.

### Person 2 — Remaining Search Work
- [ ] Test with the final consenting/public demo subject.
- [ ] Confirm the final search result is a genuinely matching page.
- [ ] Add/verify URL deduplication.
- [ ] Test no-result and provider-failure cases.
- [ ] Test rate-limit behavior.
- [ ] Test broken/unavailable candidate images.
- [ ] Connect the search output directly to Person 1's matcher.

### Person 3 — Blockchain
- [x] Choose final blockchain/network (Dual-mode: zero-dependency Local EVM simulator + Web3 RPC client).
- [x] Implement smart contract (`contracts/VerificationRegistry.sol`).
- [x] Deploy contract / contract provider interface.
- [x] Implement Web3 client (`src/blockchain/client.py`).
- [x] Implement deterministic canonicalization (`src/verification/canonicalizer.py`).
- [x] Implement SHA-256 hashing (`src/verification/hasher.py`).
- [x] Implement on-chain verification (`src/verification/verifier.py`).
- [x] Add tamper test (`scripts/test_blockchain.py` & `tests/test_blockchain_verification.py`).


### Integration
- [ ] Finalize module interfaces with all three people.
- [ ] Implement/update `main.py`.
- [ ] Run complete pipeline.
- [ ] Test from a clean environment.

### Documentation & Submission
- [ ] Complete README.
- [ ] Add known limitations.
- [ ] Push clean repository to GitHub.
- [ ] Record end-to-end screen recording.
- [ ] Upload recording.
- [ ] Submit final form.

## Important Decisions

1. **No website:** The project is pipeline-first; a CLI is sufficient.
2. **Search must be genuine:** No hardcoded social-media result.
3. **SerpApi Google Lens is the current primary provider:** It supports local binary upload followed by an `image_id` search.
4. **Search provider is isolated:** Provider-specific behavior should not leak into Person 1's matching interface.
5. **Candidate retrieval is validated:** HTTP 200 is not treated as proof that a response is an image.
6. **Thumbnail fallback is required:** Some social-platform crawler URLs return HTML redirects.
7. **Blockchain should store a fingerprint/hash:** Avoid putting raw biometric data or unnecessary content on-chain.
8. **Verification must recompute the hash:** A transaction existing is not sufficient.
9. **Use consenting/public demo data:** Do not design the system around identifying strangers or covert tracking.
10. **No secrets in Git:** API keys, private keys, seed phrases, passwords, `.env`, and virtual environments remain untracked.
11. **`memory.md` is part of the development workflow:** Meaningful project-state changes require an immediate memory update.

## Current Risks

### High Risk — Final Search Demonstration
The search mechanism works, but the final demo still needs a consenting subject whose public web presence can reliably be discovered by the image-driven search.

### Medium Risk — Social Platform Access
Some platforms may block automated retrieval or may expose only thumbnails/crawler redirects. The system must tolerate this and use legitimately accessible results.

### Medium Risk — Search Quota
SerpApi usage is limited by the account plan. Avoid unnecessary repeated searches during development. Use cached `lens_results.json` for parser/retrieval development whenever possible.

### Medium Risk — Match Quality
The current search/retrieval work does not prove face identity. Person 1 must perform face detection, embedding, similarity calculation, and threshold evaluation.

### Medium Risk — Blockchain Reliability
A public testnet may introduce RPC, faucet, or network issues. A local/simulated chain is allowed and may be preferable if public-network reliability becomes a problem.

## Update Protocol

Whenever meaningful work progresses, update this file immediately with:

```text
## Update — YYYY-MM-DD HH:MM

### Completed
- ...

### Currently Working On
- ...

### Files Changed
- ...

### Decisions
- ...

### Test / Evidence
- ...

### Blockers
- ...

### Next Action
- ...
```

Keep completed items checked off.

Do not delete historical updates unless the file becomes excessively large.

## Update — 2026-09-04

### Completed
- Person 2's SerpApi Google Lens runtime search is working.
- Lens results are parsed into normalized `Candidate` objects.
- Candidate image retrieval is implemented with main-image/thumbnail fallback.
- Batch retrieval succeeded for 10/10 candidates.
- `candidates.json` is generated as the current structured handoff.
- Git repository contains the implementation commit `a9949e0`.

### Currently Working On
- Preparing the project documentation/state files for the GitHub repository.
- Preparing the search module for handoff to Person 1.

### Files Changed
- `src/models/candidate.py`
- `src/search/parser.py`
- `src/search/image_utils.py`
- `src/search/retriever.py`
- `scripts/test_search.py`
- `Project_Requirements.md`
- `Architecture.md`
- `rules.md`
- `Phases.md`
- `memory.md`

### Decisions
- Keep SerpApi Google Lens as the primary search provider.
- Preserve both `image_url` and `thumbnail_url`.
- Validate downloaded bytes as an image.
- Fall back to thumbnails when the primary image URL returns HTML/non-image content.
- Keep generated candidate data local and out of Git.

### Test / Evidence
- Existing cached Lens response produced 10 parsed candidates.
- Main social-platform image URLs returned HTML redirects during retrieval testing.
- Thumbnail fallback successfully produced valid JPEG files.
- Batch retrieval succeeded for 10/10 candidates.

### Blockers
- Final consenting demo subject/result has not yet been validated.
- Person 1's face matching implementation is still pending.
- Person 3's blockchain implementation is still pending.

### Next Action
- Add the updated project documentation to the local repository.
- Push the clean repository to GitHub.
- Coordinate the Person 2 → Person 1 handoff.

## Update — 2026-09-06 18:38

### Completed
- Completed Person 3 — Blockchain & Verification module end-to-end.
- Created `contracts/VerificationRegistry.sol` Solidity contract for on-chain fingerprint recording and verification.
- Implemented `src/verification/canonicalizer.py` for deterministic JSON canonicalization.
- Implemented `src/verification/hasher.py` for SHA-256 fingerprinting (`0x...` 64 hex chars format).
- Implemented `src/blockchain/provider.py` with dual-mode architecture: zero-dependency `LocalBlockchainProvider` for offline testing/demos and `Web3BlockchainProvider` for live EVM RPC endpoints.
- Implemented `src/blockchain/client.py` for high-level Web3 and local blockchain interaction.
- Implemented `src/verification/verifier.py` for on-chain lookup, hash re-computation, and tamper detection.
- Added runnable integration script `scripts/test_blockchain.py`.
- Added unit tests in `tests/test_canonicalizer.py`, `tests/test_hasher.py`, and `tests/test_blockchain_verification.py`.

### Currently Working On
- Ready for Person 1 integration and final pipeline orchestration (`main.py`).

### Files Changed
- `contracts/VerificationRegistry.sol`
- `src/verification/__init__.py`
- `src/verification/canonicalizer.py`
- `src/verification/hasher.py`
- `src/verification/verifier.py`
- `src/blockchain/__init__.py`
- `src/blockchain/provider.py`
- `src/blockchain/client.py`
- `scripts/test_blockchain.py`
- `tests/test_canonicalizer.py`
- `tests/test_hasher.py`
- `tests/test_blockchain_verification.py`
- `requirements.txt`
- `.env.example`
- `memory.md`

### Decisions
- Dual-mode blockchain architecture: default to `LocalBlockchainProvider` (zero-dependency, instant, deterministic block & transaction generation) while supporting full `web3.py` RPC integration via `RPC_URL` in `.env`.
- Canonicalization normalizes URLs, lowercases platform names, sorts dictionary keys, and rounds similarity floats to 6 decimal places.

### Test / Evidence
- `scripts/test_blockchain.py` executed cleanly with exit code 0.
- All 8 unit tests in `tests/` passed (`python -m pytest tests/`).
- Tamper detection correctly flagged altered content with `verified: False`.

### Blockers
- Person 1's face detection and matching module is still pending integration.

### Next Action
- Integrate Person 3's verification module into `main.py` when Person 1 completes candidate matching.

