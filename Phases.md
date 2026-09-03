# Development Phases

## Team Split

The project is divided into three parallel workstreams.

### Person 1 — Face Processing & Matching
Owns face detection, face encoding/embeddings, candidate face extraction, similarity calculation, and match selection.

### Person 2 — Reverse Image Search & Web Retrieval
Owns genuine reverse-image search, search API/provider integration, candidate extraction, candidate URL/image retrieval, and search failure handling.

### Person 3 — Blockchain & Verification
Owns data canonicalization, SHA-256 fingerprinting, smart contract, blockchain deployment, on-chain storage/retrieval, and verification/tamper detection.

### Shared Responsibility
All three people participate in end-to-end integration, testing, README/documentation, final demo, screen recording, and submission.

---

# Phase 0 — Project Setup & Interface Design

**Goal:** Establish the repository, environments, component boundaries, and interfaces before major implementation.

### Person 1 — Face Processing
- Set up Python environment.
- Choose face-processing library.
- Test face detection and face embeddings.
- Define face-processing output format.

### Person 2 — Search
- Research and shortlist reverse-image-search mechanisms.
- Test whether genuine runtime search is possible.
- Determine what candidate data can be extracted.
- Define the search-result output format.

**Person 2 progress:**
- SerpApi Google Lens selected and tested.
- Runtime binary image upload works.
- Structured `visual_matches` results are returned.
- `Candidate` model and parser implemented.
- Candidate image retrieval implemented with main-image/thumbnail fallback.
- Batch retrieval successfully retrieved 10/10 candidates.
- `candidates.json` produced as the current Person 2 → Person 1 handoff.

### Person 3 — Blockchain
- Set up blockchain development environment.
- Choose local chain or public testnet.
- Create minimal Solidity verification registry.
- Test deployment and Web3 connection.
- Define the on-chain record format.

### Shared
- Initialize GitHub repository.
- Create directory structure.
- Create `requirements.txt` and `.env.example`.
- Review `Architecture.md` and `rules.md`.
- Agree on interfaces between all three components.

**Overall Phase 0 exit condition:** All three developers can run their respective environments and the interfaces are agreed upon.

**Important:** Person 2's Phase 0/search setup work is substantially complete, but the overall Phase 0 is not complete until the shared and Person 1/Person 3 requirements are also satisfied.

---

# Phase 1 — Face Detection & Encoding

**Primary owner: Person 1**

Build:

```text
input.jpg
   ↓
face detection
   ↓
face crop
   ↓
face embedding
```

### Person 1
- Implement image loading.
- Implement face detection and cropping.
- Implement face embedding.
- Handle no-face input.
- Handle multiple faces sensibly.
- Return a reusable face representation.
- Add basic tests.

### Person 2
- Provide representative search test images.
- Confirm that Person 1's output works with the search/matching workflow.
- Continue search implementation.

### Person 3
- Continue smart-contract/data-schema work.
- Define what information will eventually be hashed.

**Exit condition:** A valid input image produces a usable face representation.

---

# Phase 2 — Genuine Reverse Image Search

**Primary owner: Person 2**

Build:

```text
input image
     ↓
reverse image search
     ↓
candidate URLs/images
```

### Person 2
- Select the final search mechanism.
- Implement runtime search.
- Ensure the image itself drives the search.
- Parse search results.
- Extract candidate URLs/images where permitted.
- Handle rate limits and failures.
- Ensure no hardcoded final result exists.
- Test with real publicly accessible content.

**Current implementation:**
- SerpApi `engine=google_lens`.
- Local binary upload → `image_id` → Lens search.
- Normalized `Candidate` output.
- Candidate retrieval with main-image/thumbnail fallback.
- `data/candidates/candidates.json` generated from runtime results.
- Direct social crawler image URLs may return HTML redirects; image validation catches this and the thumbnail fallback is used.

### Person 1
- Test whether returned candidate images contain detectable faces.
- Prepare the matching interface.
- Test face extraction on search candidates.

### Person 3
- Continue blockchain implementation.
- Finalize the data structure that will be hashed.

**Exit condition:** Given a test image, the application performs a genuine search and returns usable candidate results.

**Person 2 status:** The core search/retrieval portion currently satisfies this condition in development testing. Further testing with the team's final consenting/public demo subject remains necessary.

---

# Phase 3 — Candidate Matching

**Primary owner: Person 1**

Build:

```text
candidate result
      ↓
candidate image
      ↓
face detection / embedding
      ↓
similarity calculation
      ↓
ranking
      ↓
best match
```

### Person 1
- Process candidate images.
- Detect faces in candidate images.
- Generate candidate embeddings.
- Calculate similarity.
- Define/document a threshold.
- Rank candidates.
- Select the strongest valid match.
- Return URL + platform + similarity + supporting data.

### Person 2
- Improve candidate extraction quality.
- Ensure search results contain enough information for matching.
- Handle inaccessible/broken candidate images.
- Test multiple search-result layouts/providers if necessary.

### Person 3
- Prepare blockchain module to accept the final `matched_result`.
- Implement deterministic canonicalization.
- Begin SHA-256 hashing.

**Exit condition:** The system can take search candidates and identify a best matching result using a defined similarity method.

---

# Phase 4 — Blockchain Recording

**Primary owner: Person 3**

Build:

```text
matched_result
      ↓
canonicalization
      ↓
SHA-256
      ↓
smart contract
      ↓
blockchain transaction
```

### Person 3
- Finalize canonical data format.
- Implement deterministic hashing.
- Implement smart contract.
- Deploy contract.
- Implement Web3 client.
- Store hash/fingerprint and necessary metadata/reference.
- Return transaction hash/record identifier.
- Implement retrieval.

### Person 1
- Verify that the matching output contains all required fields.
- Ensure similarity information is represented consistently.

### Person 2
- Verify that source URL/platform/content metadata are captured correctly.
- Test search-result data against canonicalization.

**Exit condition:** A real `matched_result` can be hashed, recorded on-chain, and retrieved.

---

# Phase 5 — Blockchain Verification & Tamper Test

**Primary owner: Person 3**

Build:

```text
stored post data
      ↓
recompute hash
      ↓
retrieve blockchain hash
      ↓
compare
      ↓
VERIFIED / NOT VERIFIED
```

### Person 3
- Implement local hash recomputation.
- Retrieve on-chain hash.
- Compare hashes.
- Return clear verification status.
- Implement mismatch/tamper test.
- Record transaction/contract details for the demo.

### Person 1
- Test verification using different matching candidates.
- Confirm that the match result remains compatible with hashing.

### Person 2
- Test source metadata changes.
- Confirm that modified data produces a different fingerprint.

**Exit condition:** Both genuine matching data and altered data produce the expected verification result.

---

# Phase 6 — End-to-End Integration

**Owners: All Three**

Connect:

```text
Person 1
Face Detection + Encoding
        ↓
Person 2
Reverse Search + Candidate Retrieval
        ↓
Person 1
Candidate Matching
        ↓
Person 3
Hash + Blockchain Recording
        ↓
Person 3
Blockchain Verification
```

### Person 1
- Connect face module to search input.
- Connect search candidates to matcher.
- Standardize match output.

### Person 2
- Connect search module to the matching module.
- Ensure real candidate URLs/images flow automatically.
- Remove temporary hardcoded test results.

### Person 3
- Connect matcher output to hashing.
- Connect hashing to blockchain.
- Connect blockchain retrieval to verification.
- Return final verification result.

### Shared
- Implement/update `main.py`.
- Standardize logging/output and errors.
- Remove duplicate code.
- Run the full pipeline from one command.

**Exit condition:** One command executes the complete pipeline without manual intervention.

---

# Phase 7 — Testing & Hardening

**Owners: All Three**

### Person 1 — Face & Matching Tests
- No face.
- Low-quality image.
- Multiple faces.
- Different face angles.
- Incorrect candidate.
- Similar-looking but different face.
- Different similarity thresholds.

### Person 2 — Search Tests
- Successful reverse search.
- No search results.
- Search API/provider failure.
- Rate limiting.
- Broken candidate URL.
- Candidate image unavailable.
- Multiple candidate results.
- Real social/web result discovery.
- Main image URL returning HTML/non-image content.
- Thumbnail fallback.
- Duplicate candidate URLs.

### Person 3 — Blockchain Tests
- RPC failure.
- Transaction failure.
- Duplicate hash.
- Hash mismatch.
- Invalid record.
- Blockchain unavailable.
- Tampered data.
- Successful retrieval and verification.

### Shared
- Run from a fresh Git clone.
- Install dependencies from scratch.
- Verify `.env.example`.
- Ensure no secrets are committed.
- Verify README commands.
- Test the complete pipeline.
- Check final output is understandable.

**Exit condition:** Known failure cases are handled cleanly and the complete pipeline is reproducible.

---

# Phase 8 — Documentation

**Owners: All Three**

### Person 1
Document:
- Face-processing library.
- Face encoding method.
- Similarity method.
- Matching threshold.
- Face-processing limitations.

### Person 2
Document:
- Reverse-image-search mechanism.
- Search flow.
- Candidate extraction.
- Candidate retrieval and fallback behavior.
- Search limitations.
- Access/rate-limit considerations.

### Person 3
Document:
- Blockchain/network.
- Smart contract.
- Hashing/canonicalization.
- Transaction flow.
- Verification mechanism.
- Blockchain limitations.

### Shared
Complete `README.md` with:
- Project overview.
- Architecture.
- Tech stack.
- Installation.
- Configuration.
- How to run.
- Example output.
- Blockchain details.
- Known limitations.
- Demo instructions.

**Exit condition:** Someone unfamiliar with the project can clone the repository and understand how to run it.

---

# Phase 9 — Final Demo & Submission

**Owners: All Three**

Recommended command:

```bash
python src/main.py --image sample/input.jpg
```

The recording should show:

```text
1. Input image
       ↓
2. Face detected
       ↓
3. Face encoded
       ↓
4. Genuine reverse search
       ↓
5. Candidate results
       ↓
6. Real matching post
       ↓
7. Similarity score
       ↓
8. SHA-256 hash
       ↓
9. Blockchain transaction
       ↓
10. Transaction/record identifier
       ↓
11. Local hash vs on-chain hash
       ↓
12. VERIFIED
```

### Person 1
- Prepare stable face/matching demo input.
- Verify the final match.
- Help operate the demo.

### Person 2
- Verify the genuine search works immediately before recording.
- Ensure the displayed social/web result is accessible.
- Help operate the demo.

### Person 3
- Verify blockchain/network availability.
- Ensure contract and wallet configuration work.
- Verify transaction and final verification output.

### Shared
- Record the end-to-end screen capture.
- Upload recording.
- Check GitHub repository.
- Verify README.
- Verify no secrets are exposed.
- Perform a final clean run.
- Submit the form only after everything is final.

**Exit condition:** A single unedited recording demonstrates the entire pipeline successfully.

---

# Work Distribution Summary

| Phase | Person 1 — Face & Matching | Person 2 — Search & Web | Person 3 — Blockchain |
|---|---|---|---|
| 0 | Face setup | Search setup | Blockchain setup |
| 1 | **Face pipeline** | Search support | Contract/schema |
| 2 | Matching preparation | **Reverse search** | Hash preparation |
| 3 | **Candidate matching** | Search improvements | Canonicalization |
| 4 | Match-output validation | Metadata validation | **Blockchain recording** |
| 5 | Match testing | Search/data testing | **Verification + tamper test** |
| 6 | **Integration** | **Integration** | **Integration** |
| 7 | Face/matching tests | Search tests | Blockchain tests |
| 8 | Face docs | Search docs | Blockchain docs |
| 9 | Demo | Demo | Demo |

# Critical Interfaces

## Person 1 → Person 2
Person 1 provides the input image and face representation needed by the search/matching workflow.

## Person 2 → Person 1
Person 2 provides candidate results approximately like:

```json
{
  "candidate_id": "candidate_001",
  "page_url": "...",
  "local_image_path": "data/candidates/candidate_001.jpg",
  "retrieval_status": "success",
  "image_url": "...",
  "thumbnail_url": "...",
  "title": "...",
  "platform": "...",
  "snippet": "...",
  "metadata": {}
}
```

**Guarantee:** Person 1 should be able to read the local candidate image without issuing a network request.

## Person 1 → Person 3
Person 1 provides the selected matching result:

```json
{
  "url": "...",
  "platform": "...",
  "similarity": 0.94,
  "image_url": "...",
  "content": "...",
  "metadata": {}
}
```

## Person 3 → Everyone
Person 3 returns:

```json
{
  "content_hash": "...",
  "transaction_hash": "...",
  "on_chain_hash": "...",
  "verified": true
}
```

# Definition of Done

- [ ] Person 1's face pipeline works.
- [ ] Person 2's search genuinely runs at runtime.
- [ ] Person 2's search produces a real matching online/social result.
- [ ] Person 1's matcher supports the result with a defined similarity method.
- [ ] Person 3's hash is deterministic.
- [ ] Person 3's blockchain record is real and retrievable.
- [ ] Blockchain verification recomputes the hash.
- [ ] Tampered data fails verification.
- [ ] All three components run through one pipeline.
- [ ] No final result is hardcoded.
- [ ] README is complete.
- [ ] GitHub repository is clean.
- [ ] Screen recording shows the full flow.
- [ ] Final submission has been checked by all three people.
