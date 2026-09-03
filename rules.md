# Rules

This file is the project's operating rules. Follow these rules during implementation and review.

## 1. Core Rules

### MUST
- Build a genuinely end-to-end pipeline.
- Perform the web/reverse-image search at runtime.
- Find a real matching online/social-media result.
- Generate a deterministic fingerprint/hash of the discovered data.
- Store the fingerprint on a blockchain.
- Recompute and compare the fingerprint during verification.
- Keep the complete source code in GitHub.
- Document setup, execution, blockchain choice, and limitations.
- Keep the final demo reproducible.
- Keep `memory.md` synchronized with meaningful project-state changes.

### MUST NOT
- Hardcode the final social-media URL as the search result.
- Pretend a predetermined result came from the search engine.
- Fake blockchain transactions or verification output.
- Use a screenshot as proof of a blockchain transaction.
- Claim a match without a defined matching method.
- Commit API keys, private keys, seed phrases, or passwords.
- Store unnecessary biometric data on-chain.
- Let project state in `memory.md` become stale after a meaningful implementation change.

## 2. Search Rules

The search mechanism must be genuinely driven by the input image.

Acceptable:
- Reverse-image-search service/API
- Image-search API
- Scripted reverse-search workflow

Not acceptable:
- Searching a person's name and calling that face identification.
- Returning a manually selected URL.
- A static JSON file containing the expected answer.
- A hardcoded mapping such as `image A → URL B`.

Search failures should be reported honestly rather than replaced with a fake result.

Current search implementation:
- SerpApi Google Lens
- Local binary image upload followed by `image_id` search
- Structured candidate parsing
- Main image retrieval with thumbnail fallback

## 3. Face Recognition Rules

- Use established libraries/models.
- Clearly distinguish face detection from face matching.
- Use embeddings/similarity rather than subjective visual claims.
- Record the similarity method and threshold.
- Do not present a similarity score as proof of identity.
- Test with variations in image quality where possible.

## 4. Blockchain Rules

- Store a hash/fingerprint rather than unnecessary raw personal data.
- Define exactly what is hashed.
- Use deterministic canonicalization before hashing.
- The same input data must always produce the same hash.
- Save transaction/record identifiers in the application output.
- Verification must independently recompute the local hash.
- A mismatch must produce a failure state.

## 5. Smart Contract Rules

Keep the contract minimal.

It should support at least:
1. Record/store a verification hash.
2. Retrieve/check a stored verification hash.

Do not add unnecessary functionality unless it directly improves the task.

## 6. Data Integrity Rules

Before hashing, create a canonical representation.

For example:

```text
canonical_data =
    normalized URL
    + platform
    + content/image fingerprint
    + selected metadata
```

Then:

```text
SHA-256(canonical_data)
```

The exact canonicalization procedure must be documented so verification can be reproduced.

## 7. Privacy & Responsible Use

- Use test images of consenting people for development/demo.
- Prefer public content that can legitimately be accessed.
- Do not build features for covert tracking or surveillance.
- Do not expose private personal information.
- Do not store raw face embeddings on a public blockchain.
- Treat the output as a technical match signal, not definitive identity proof.

## 8. Engineering Rules

- Keep modules small and testable.
- Handle network/API failures explicitly.
- Add useful error messages.
- Keep credentials in environment variables.
- Pin important dependencies where practical.
- Write tests for hashing and blockchain verification.
- Avoid unnecessary frontend work.
- Prioritize reliability over visual polish.
- Keep search-provider-specific behavior isolated behind clear interfaces.
- Validate downloaded content instead of trusting a URL's file extension or HTTP 200 status.

## 9. Demo Rules

The recording should show the actual application performing:
1. Input image
2. Face detection/encoding
3. Search
4. Real candidate/result
5. Matching
6. Hash creation
7. Blockchain transaction
8. Blockchain verification

Do not edit the recording to hide failed steps or fabricate results.

## 10. Definition of Done

A feature is complete only when:
- It works from the actual application.
- It is connected to the rest of the pipeline.
- It is documented.
- It can be demonstrated in the final recording.
- It does not depend on hardcoded output.
- Its meaningful state/change is recorded in `memory.md`.

## 11. Project Memory Rule

`memory.md` is the persistent project state.

**It must be automatically updated whenever a meaningful project change occurs**, including:
- implementation completion,
- new or changed architecture,
- interface/schema changes,
- important technical decisions,
- blockers,
- testing results,
- provider/search behavior,
- file additions/removals,
- phase progress,
- changes to next actions.

The update should happen as part of the same development workflow/commit that introduces the meaningful change. Do not rely on remembering to update it later.

Each update should record:
- what changed,
- why it changed,
- files affected,
- test/evidence,
- current status,
- next action.

If no meaningful project state changed, a memory update is not required.
