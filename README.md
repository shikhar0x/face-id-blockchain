# Face ID + Blockchain Verification

**HH Goa 2026 — Task 3: Face Identification & Blockchain Verification**

An end-to-end pipeline that takes a face image, finds a real matching
web/social-media post through genuine runtime reverse-image search, supports
the match with face-embedding similarity, fingerprints the result with SHA-256,
records the fingerprint on a blockchain, and verifies it back.

```text
INPUT IMAGE
     |
[Person 1] FACE DETECTION + FACE EMBEDDING (YuNet + SFace)
     |
[Person 2] REVERSE IMAGE SEARCH (SerpApi Google Lens) + CANDIDATE RETRIEVAL
     |
[Person 1] FACE MATCHING + RANKING + BEST-MATCH SELECTION
     |
[Person 3] CANONICALIZATION + SHA-256
     |
[Person 3] BLOCKCHAIN RECORD + RETRIEVAL + HASH VERIFICATION
```

> A similarity score is a **technical matching signal, not proof of identity**.
> The pipeline reports failures honestly and never fabricates a match.

---

## Architecture

| Module | Owner | Responsibility |
|---|---|---|
| `src/face/` | Person 1 | Face detection (YuNet), face embeddings (SFace) |
| `src/search/` | Person 2 | SerpApi Google Lens search, candidate parsing + retrieval |
| `src/matching/` | Person 1 | Cosine similarity, ranking, thresholding, best-match selection |
| `src/verification/` | Person 3 | Canonicalization, SHA-256 fingerprinting, verification |
| `src/blockchain/` | Person 3 | On-chain record / retrieval (local simulator or Web3 RPC) |
| `contracts/` | Person 3 | `VerificationRegistry.sol` minimal registry contract |
| `src/main.py` | Shared | End-to-end CLI connecting all three modules |

Data handoffs:

- **Person 2 → Person 1:** normalized `Candidate` objects with
  `local_image_path` (already downloaded — matching issues no extra requests).
- **Person 1 → Person 3:** `matched_result`
  (`url`, `platform`, `similarity`, `image_url`, `content`, `metadata`).
- **Person 3 → output:** `content_hash`, `transaction_hash`, `verified`.

See `Architecture.md`, `Phases.md`, `Project_Requirements.md`, and `rules.md`
for the full design, work split, and operating rules.

---

## Person 1 — Face Processing & Matching (this implementation)

### Chosen face library: OpenCV YuNet + SFace (OpenCV Zoo)

- **Detection:** YuNet (`face_detection_yunet_2023mar.onnx`) — a real
  pretrained CNN face detector producing bounding box + 5 landmarks +
  confidence per face.
- **Recognition:** SFace (`face_recognition_sface_2021dec.onnx`) — a real
  pretrained face-recognition network producing a **128-dimensional**
  embedding per aligned face, L2-normalized in `src/face/embedder.py`.
- **Runtime:** `cv2.dnn` (CPU) via `opencv-python-headless` + `numpy`.
  No custom model, no training from scratch.

**Why not InsightFace** (the architecture's first suggestion)? InsightFace
pulls `opencv-python` (non-headless), which requires the system `libGL`
library unavailable in minimal/headless containers — working around that
inside `requirements.txt` is fragile. It also needs ~500 MB of dependencies
plus 100–300 MB of model downloads. YuNet + SFace are established
pretrained models (~39 MB total), install cleanly headless, and are fully
adequate for a demo with honestly documented limitations.

### Embedding & similarity

- Query face → one 128-d L2-normalized embedding.
- Candidate face → one embedding **per detected face**.
- Metric: `cosine_similarity(a, b) = dot(a, b) / (||a||·||b||)`,
  implemented in `src/matching/similarity.py`, range `[-1, 1]`,
  **higher = more similar**.
- Candidate score = **maximum** cosine similarity over all faces in the
  candidate image (group photos stay matchable; the face count is reported).

### Threshold

- Default **`FACE_MATCH_THRESHOLD=0.5`** (env) / `--threshold` (CLI).
- A candidate is a valid match only when `similarity >= threshold`.
- This is a **demo threshold** that may need calibration (typical cosine
  face-matching band is ~0.4–0.6; lower = more false positives).
  The full ranked list is always printed and saved, so threshold decisions
  stay auditable.

### Multiple-face behavior

- **Query image:** the **largest-area** detection is the primary face
  (ties → higher confidence → lower index). `face_count` and
  `multiple_faces` are always reported; ambiguity is never hidden.
- **Candidate image:** every face is embedded and scored; the best face wins
  for that candidate (`best_face_index` + all `face_scores` recorded).

### No-face / error handling

Missing file, unreadable/corrupt image, no detectable face, embedding
failure, missing candidate file, failed retrieval — each produces a clear
`success: false` / `matchable: false` result with a `reason`. One bad
candidate never aborts the run. When nothing passes the threshold the CLI
exits non-zero with `NO VALID MATCH` instead of inventing one.

### Optional secondary signal

`--use-phash` blends perceptual-hash image similarity
(`src/matching/similarity.py::phash_similarity`, 15% weight) with the face
score. It is **off by default**, reported separately (`face_similarity`,
`phash_similarity`), and never replaces face matching.

---

## Person 2 — Reverse Image Search (existing)

SerpApi Google Lens: local binary upload → `image_id` → Lens search →
`visual_matches` parsed into `Candidate` objects → images downloaded locally
with main-image → thumbnail fallback → `data/candidates/candidates.json`.
See `scripts/test_search.py` and `src/search/`.

## Person 3 — Blockchain & Verification (existing)

Deterministic canonical JSON → SHA-256 (`0x…` bytes32) → recorded via
`VerificationRegistry.sol` interface → retrieved and re-compared
(`VERIFIED` / `NOT VERIFIED`). Dual-mode provider: zero-dependency local
chain simulator by default, real Web3 RPC when configured.
See `scripts/test_blockchain.py`, `src/verification/`, `src/blockchain/`.

---

## Installation

Requirements: Python 3.11+, pip, internet access (models + SerpApi + PyPI).

```bash
git clone https://github.com/shikhar0x/face-id-blockchain.git
cd face-id-blockchain

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Download + verify the pretrained face models (~39 MB, SHA-256 checked):

```bash
python scripts/download_face_models.py
```

(The pipeline also auto-downloads them on first use unless
`FACE_AUTO_DOWNLOAD=0`.)

## Environment setup

```bash
cp .env.example .env
# then edit .env:
#   SERPAPI_KEY=...            # required for live search
#   FACE_MATCH_THRESHOLD=0.5   # optional
#   FACE_MODEL_DIR=models      # optional
#   USE_LOCAL_BLOCKCHAIN=true  # false + RPC_URL/CONTRACT_ADDRESS/PRIVATE_KEY for live chain
```

Never commit `.env` or any key. `.env.example` documents every variable.

## How to run

Full pipeline (face → live search → match → hash → blockchain → verify):

```bash
python src/main.py --image sample/input.jpg
```

Useful variants:

```bash
# Fewer candidates / custom threshold
python src/main.py --image sample/input.jpg --limit 5 --threshold 0.55

# Reuse previously retrieved candidates (no SerpApi call, quota-safe)
python src/main.py --image sample/input.jpg --candidates-json data/candidates/candidates.json

# Isolated module self-tests
python scripts/test_face.py sample/input.jpg        # Person 1: detect + embed
python scripts/test_search.py sample/input.jpg      # Person 2: live Lens search
python scripts/test_blockchain.py                   # Person 3: hash/record/verify + tamper test
```

Exit codes: `0` VERIFIED · `2` input/face failure · `3` search/match
failure (incl. honest no-match) · `4` blockchain/verify failure · `1`
unexpected error.

### Example output (illustrative — values vary per input)

```text
==================================================
FACE ID + BLOCKCHAIN VERIFICATION
==================================================

[1/8] Loading input image...
      Input: sample/input.jpg

[2/8] Detecting face...
      face detected: YES, faces found: 1

[3/8] Generating face embedding...
      Embedding OK (dim=128, strategy=largest_area)

[4/8] Running reverse image search...
      Candidates found: 10 (live search: True)

[5/8] Matching candidate faces...
      Threshold: 0.5 (cosine similarity, higher = more similar)
      Ranked candidates (face similarity, descending):
       1. candidate_004 similarity=0.91 (faces=1) [MATCH]
          https://example.com/matching-post
       2. candidate_001 similarity=0.42 (faces=1) [below threshold]
          ...
      Ranking saved to: data/candidates/match_report.json

[6/8] Best match
      Candidate: candidate_004
      URL: https://example.com/matching-post
      Platform: Example
      Similarity: 0.91
      NOTE: similarity is a technical matching signal, not proof of identity.

[7/8] Recording verification on blockchain...
      Content hash: 97040fce...
      Transaction: 0xdec5dd...
      Block: 1001

[8/8] Verifying blockchain record...
      Local hash:    97040fce...
      On-chain hash: 0x97040fce...
      Details: VERIFIED: Local SHA-256 fingerprint exactly matches ...

==================================================
VERIFIED
==================================================
```

---

## Tests

```bash
pytest tests/ -v
```

- `test_similarity.py` — cosine math (identical/orthogonal/opposite pairs,
  range, error cases) + perceptual-hash checks.
- `test_face_processor.py` — single/no/multi-face query handling, largest-area
  selection, corrupt-file handling (faked backends, real image files).
- `test_matcher.py` — ranking order, threshold filtering, skipped candidates,
  multi-face max rule, no false match, Person-3 contract shape.
- `test_pipeline_integration.py` — offline match → hash → record → verify →
  tamper-detection using the real Person-3 code.
- `test_face_models_integration.py` — **real** YuNet/SFace inference on
  `tests/fixtures/`; runs only when models are downloaded, otherwise skips.
- Existing Person-2/Person-3 tests keep passing unchanged.

Current status: **48 passed, 5 skipped** (skips = real-model tests awaiting
downloaded weights in offline environments), plus `scripts/test_blockchain.py`
exit 0.

## Project structure

```text
face-id-blockchain/
├── src/
│   ├── main.py                  # end-to-end CLI (all 3 modules)
│   ├── face/                    # Person 1: detector / embedder / processor / models
│   ├── matching/                # Person 1: similarity / matcher
│   ├── search/                  # Person 2: SerpApi client / parser / retriever
│   ├── verification/            # Person 3: canonicalizer / hasher / verifier
│   ├── blockchain/              # Person 3: client / providers
│   └── models/candidate.py      # shared Candidate dataclass
├── contracts/VerificationRegistry.sol
├── scripts/                     # test_search / test_face / test_blockchain / download_face_models
├── tests/ (+ fixtures/)         # unit + integration tests, committed fixtures
├── requirements.txt  .env.example  .gitignore
├── Project_Requirements.md  Architecture.md  Phases.md  rules.md  memory.md
└── models/  data/               # gitignored: downloaded weights, runtime artifacts
```

## Configuration reference

| Variable | Default | Meaning |
|---|---|---|
| `SERPAPI_KEY` | — | SerpApi key for live Lens search (required unless `--candidates-json`) |
| `FACE_MATCH_THRESHOLD` | `0.5` | Cosine threshold for a valid match |
| `FACE_MODEL_DIR` | `models` | Directory for YuNet/SFace `.onnx` files |
| `FACE_YUNET_MODEL` / `FACE_SFACE_MODEL` | — | Explicit model paths (override dir) |
| `FACE_DETECT_THRESHOLD` | `0.6` | YuNet detection confidence cutoff |
| `FACE_AUTO_DOWNLOAD` | `1` | `0` disables model auto-download (fail fast) |
| `USE_LOCAL_BLOCKCHAIN` | `true` | `false` + `RPC_URL`/`CONTRACT_ADDRESS`/`PRIVATE_KEY` for live chain |

## Limitations

- Face similarity degrades with pose, age gaps, occlusions, heavy filters,
  and low resolution; the 0.5 threshold is a starting point, not universal.
- YuNet/SFace are compact demo-grade models — less accurate than
  state-of-the-art systems (e.g. InsightFace/ArcFace pipelines).
- Reverse-image search depends on SerpApi quota and search-engine indexing;
  social platforms may block automated retrieval (thumbnail fallback helps).
- The default blockchain is an in-memory local simulator (deterministic,
  zero-dependency) — use a real RPC endpoint + deployed contract for
  on-chain demo weight.
- Test fixtures (`tests/fixtures/`) are AI-generated portraits used only to
  exercise image-loading paths offline; final demo should use a consenting
  subject with public web presence.

## Privacy & responsible use

- Use only consenting subjects / public content for development and demos.
- Raw face embeddings are **never** written on-chain, never saved to JSON
  reports, and live only in process memory.
- Only the SHA-256 fingerprint + public post metadata touch the blockchain.
- Treat every result as a technical match signal, never as definitive proof
  of identity. See `rules.md` §7.
