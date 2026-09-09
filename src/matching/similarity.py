"""Similarity metrics for face matching (Person 1).

Primary signal: cosine similarity between L2-normalized SFace embeddings.

    cosine_similarity(a, b) = dot(a, b) / (||a|| * ||b||)

For L2-normalized embeddings this equals the dot product and lies in
``[-1, 1]`` (in practice SFace same-identity pairs score well above 0).
A HIGHER value means MORE similar. This score is a technical matching
signal — it is NOT proof of identity.

Secondary (optional) signal: perceptual-hash similarity between the raw
input image and the raw candidate image. It can support the face score but
never replaces it, and it is disabled unless explicitly requested.
"""

from __future__ import annotations

import numpy as np

try:
    from PIL import Image as _PILImage

    import imagehash as _imagehash

    _PHASH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency guard
    _PILImage = None
    _imagehash = None
    _PHASH_AVAILABLE = False


def cosine_similarity(embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
    """Cosine similarity between two 1-D face embeddings.

    Returns a float in ``[-1, 1]`` (1.0 = identical direction).

    Raises:
        ValueError: on empty, non-1-D, mismatched-shape, or zero-norm input.
    """
    vec_a = np.asarray(embedding_a, dtype=np.float64).reshape(-1)
    vec_b = np.asarray(embedding_b, dtype=np.float64).reshape(-1)

    if vec_a.size == 0 or vec_b.size == 0:
        raise ValueError("cosine_similarity() requires non-empty embeddings.")
    if vec_a.shape != vec_b.shape:
        raise ValueError(
            f"Embedding shape mismatch: {vec_a.shape} vs {vec_b.shape}."
        )

    norm_a = float(np.linalg.norm(vec_a))
    norm_b = float(np.linalg.norm(vec_b))
    if norm_a <= 0.0 or norm_b <= 0.0:
        raise ValueError("cosine_similarity() requires non-zero embeddings.")

    score = float(np.dot(vec_a, vec_b) / (norm_a * norm_b))
    # Clamp float noise so the contract [-1, 1] always holds.
    return max(-1.0, min(1.0, score))


def is_phash_available() -> bool:
    """Return True when the optional perceptual-hash dependency is installed."""
    return _PHASH_AVAILABLE


def phash_similarity(
    image_path_a: str, image_path_b: str, hash_size: int = 8
) -> float:
    """Perceptual-hash similarity between two image files, in ``[0, 1]``.

    1.0 means (perceptually) identical images. This is an IMAGE-level signal,
    not a face signal — it must only ever support face similarity.

    Raises:
        ImportError: when the ``ImageHash``/``Pillow`` packages are missing.
        FileNotFoundError / ValueError: when an image cannot be opened.
    """
    if not _PHASH_AVAILABLE:
        raise ImportError(
            "Perceptual hashing needs the 'ImageHash' and 'Pillow' packages. "
            "Install them with: pip install -r requirements.txt"
        )
    if hash_size < 2:
        raise ValueError("hash_size must be >= 2.")

    try:
        with _PILImage.open(image_path_a) as handle_a:
            hash_a = _imagehash.phash(handle_a, hash_size=hash_size)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Cannot hash image '{image_path_a}': {exc}") from exc

    try:
        with _PILImage.open(image_path_b) as handle_b:
            hash_b = _imagehash.phash(handle_b, hash_size=hash_size)
    except FileNotFoundError:
        raise
    except Exception as exc:
        raise ValueError(f"Cannot hash image '{image_path_b}': {exc}") from exc

    max_distance = hash_size * hash_size
    return 1.0 - (float(hash_a - hash_b) / float(max_distance))
