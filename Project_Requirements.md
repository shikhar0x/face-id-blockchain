# Project Requirements

## Project
**HH Goa 2026 — Task 3: Face Identification & Blockchain Verification**

## Objective
Build an end-to-end pipeline that:
1. Accepts a face image as input.
2. Detects and encodes the face.
3. Performs a genuine reverse-image/web search driven by the input image.
4. Finds at least one real, matching social-media/web post.
5. Verifies the discovered result using image/face similarity.
6. Creates a cryptographic fingerprint of the discovered data.
7. Stores that fingerprint on a blockchain.
8. Recomputes and verifies the fingerprint against the on-chain record.

## Mandatory Features

### 1. Face Detection & Encoding
- Input: an image containing a face.
- Detect at least one face.
- Generate a face embedding/encoding.
- Use an existing library/API; no custom model training is required.
- The pipeline must report whether face detection/encoding succeeded.

### 2. Genuine Web / Social-Media Search
- The search must be performed at runtime.
- Do not hardcode a known URL or preselected answer.
- Use reverse-image search, a suitable API, or a scripted search approach.
- The search must produce candidate web/social-media results.
- At least one real matching post must be found.
- The result should expose its URL/source so it can be demonstrated in the recording.

### 3. Match Verification
- Compare the input against candidate result(s).
- Prefer face-embedding similarity when the candidate contains a detectable face.
- Image similarity/perceptual hashing can be used as an additional signal.
- Produce an interpretable match score or decision.
- Do not claim certainty beyond what the matching method supports.

### 4. Blockchain Record
For the selected matching post, collect relevant data such as:
- Source URL
- Source/platform
- Image or content fingerprint
- Relevant text/metadata when available
- Timestamp of verification

Generate a deterministic cryptographic hash, preferably SHA-256, over a clearly defined canonical representation.

Store the hash/fingerprint and enough metadata to identify the verification record on the blockchain.

### 5. Blockchain Verification
The application must:
- Retrieve the stored on-chain record.
- Recompute the local hash from the same data.
- Compare local and blockchain values.
- Clearly report:
  - `VERIFIED` when they match.
  - `NOT VERIFIED / TAMPERED` when they do not.

A tamper test should be included if practical.

### 6. End-to-End CLI / App
A simple CLI is sufficient. A lightweight UI is optional.

The complete run should visibly follow:

`Input Image → Face Detection/Encoding → Reverse Search → Candidate Results → Match → Hash → Blockchain Upload → Blockchain Verification`

### 7. GitHub Repository
The repository must contain:
- Full source code
- Smart contract, if applicable
- Dependency/setup files
- README
- Run instructions
- Blockchain details
- Known limitations
- Example configuration/environment file without secrets

### 8. Screen Recording
The final recording must show the complete pipeline running end-to-end:
- Input image
- Face detection/encoding
- Genuine search
- Real matching post
- Hash generation
- Blockchain transaction
- Verification result

The recording may be a plain, unedited screen recording.

## Non-Requirements
- No website is required.
- No hosting is required.
- No custom AI model is required.
- No production database is required.
- No complex smart contract is required.
- No mainnet deployment is required.
- No elaborate frontend is required.

## Acceptance Criteria
The project is considered complete when a fresh run can demonstrate:
- [ ] A face is detected and encoded from an input image.
- [ ] A genuine runtime search is performed.
- [ ] At least one real matching online/social post is found.
- [ ] The matching result is supported by a similarity/matching step.
- [ ] A deterministic hash/fingerprint is generated.
- [ ] The hash is recorded on the chosen blockchain.
- [ ] The on-chain record can be retrieved.
- [ ] The local and on-chain hashes can be compared successfully.
- [ ] The complete flow is documented in GitHub.
- [ ] A screen recording demonstrates the complete flow.

## Current Implementation Notes
- Reverse-image search is currently implemented with SerpApi's Google Lens engine.
- The local input image is uploaded through SerpApi's image-upload endpoint and the returned `image_id` is used for the Lens search.
- Lens results are normalized into `Candidate` objects.
- Candidate records preserve the page URL, platform, title, image URL, thumbnail URL, snippet, metadata, local image path, and retrieval status.
- Candidate image retrieval tries the returned `image` URL first and falls back to the returned `thumbnail` URL.
- In the current real test, the direct social-platform image URLs returned HTML redirects rather than image bytes, while the Lens thumbnails were successfully retrieved as valid JPEGs.
- A batch retrieval test successfully retrieved 10/10 candidate images and produced `data/candidates/candidates.json`.
- No API key, virtual environment, raw Lens response, or generated candidate images are intended to be committed to GitHub.
