"""Pretrained face-model file management (Person 1).

This module is intentionally stdlib-only so that
``scripts/download_face_models.py`` works even before the ML
dependencies are installed.

Models (OpenCV Zoo, Apache-2.0 / MIT licensed):
- YuNet ``face_detection_yunet_2023mar.onnx`` — face detection.
- SFace ``face_recognition_sface_2021dec.onnx`` — face recognition embeddings.

Environment overrides:
- ``FACE_MODEL_DIR``: directory holding the ``.onnx`` files (default: ``models``).
- ``FACE_YUNET_MODEL``: explicit full path to the YuNet model file.
- ``FACE_SFACE_MODEL``: explicit full path to the SFace model file.
- ``FACE_AUTO_DOWNLOAD``: ``0``/``false`` disables automatic downloading
  (default: downloading is enabled).
"""

from __future__ import annotations

import hashlib
import os
import urllib.request

YUNET_FILENAME = "face_detection_yunet_2023mar.onnx"
SFACE_FILENAME = "face_recognition_sface_2021dec.onnx"

# SHA-256 digests taken from the upstream Git LFS pointers, used to verify
# that a downloaded model file is intact and untampered.
YUNET_SHA256 = "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4"
YUNET_SIZE = 232589
SFACE_SHA256 = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
SFACE_SIZE = 38696353

_YUNET_PATH = "models/face_detection_yunet/face_detection_yunet_2023mar.onnx"
_SFACE_PATH = "models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

# Primary + fallback download locations (same upstream repository).
YUNET_URLS = (
    f"https://raw.githubusercontent.com/opencv/opencv_zoo/main/{_YUNET_PATH}",
    f"https://github.com/opencv/opencv_zoo/raw/main/{_YUNET_PATH}",
)
SFACE_URLS = (
    f"https://raw.githubusercontent.com/opencv/opencv_zoo/main/{_SFACE_PATH}",
    f"https://github.com/opencv/opencv_zoo/raw/main/{_SFACE_PATH}",
)


def get_model_dir() -> str:
    """Return the directory used to store downloaded face models."""
    return os.getenv("FACE_MODEL_DIR", "models")


def get_yunet_model_path() -> str:
    """Return the YuNet detector model path (env override supported)."""
    explicit = os.getenv("FACE_YUNET_MODEL", "").strip()
    if explicit:
        return explicit
    return os.path.join(get_model_dir(), YUNET_FILENAME)


def get_sface_model_path() -> str:
    """Return the SFace recognizer model path (env override supported)."""
    explicit = os.getenv("FACE_SFACE_MODEL", "").strip()
    if explicit:
        return explicit
    return os.path.join(get_model_dir(), SFACE_FILENAME)


def is_auto_download_enabled() -> bool:
    """Return False only when the user explicitly disables auto-download."""
    return os.getenv("FACE_AUTO_DOWNLOAD", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def sha256_of_file(path: str) -> str:
    """Compute the SHA-256 hex digest of a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_file(path: str, expected_sha256: str, expected_size: int) -> bool:
    """Return True when a model file exists and matches size + SHA-256."""
    try:
        if not os.path.isfile(path):
            return False
        if os.path.getsize(path) != expected_size:
            return False
        return sha256_of_file(path) == expected_sha256.lower()
    except OSError:
        return False


def download_model(urls: tuple[str, ...], dest_path: str) -> str:
    """Download a model file, trying each URL in order.

    Returns the destination path. Raises RuntimeError when every URL fails.
    A partial/corrupt download is removed before the next attempt.
    """
    os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
    errors: list[str] = []
    for url in urls:
        try:
            print(f"Downloading {os.path.basename(dest_path)} from {url} ...")
            urllib.request.urlretrieve(url, dest_path)  # noqa: S310 (fixed hosts)
            return dest_path
        except Exception as exc:  # try next mirror
            errors.append(f"{url}: {exc}")
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except OSError:
                pass
    raise RuntimeError(
        f"Could not download {os.path.basename(dest_path)}. Tried: "
        + "; ".join(errors)
    )


def ensure_model(
    filename: str,
    urls: tuple[str, ...],
    expected_sha256: str,
    expected_size: int,
    dest_path: str,
    auto_download: bool = True,
) -> str:
    """Ensure a model file exists locally and is verified.

    When the file is missing/invalid and ``auto_download`` is enabled, it is
    downloaded and re-verified. Raises FaceModelError (imported lazily to keep
    this module stdlib-only) when the model cannot be provided.
    """
    from src.face.errors import FaceModelError

    if verify_model_file(dest_path, expected_sha256, expected_size):
        return dest_path

    if os.path.isfile(dest_path):
        print(
            f"Existing {filename} failed verification "
            f"(size/SHA-256 mismatch); re-downloading."
        )
        try:
            os.remove(dest_path)
        except OSError:
            pass

    if not (auto_download and is_auto_download_enabled()):
        raise FaceModelError(
            f"Face model '{filename}' is missing at '{dest_path}'. "
            f"Run 'python scripts/download_face_models.py' to fetch it, "
            f"or set FACE_MODEL_DIR / explicit model-path env vars."
        )

    download_model(urls, dest_path)

    if not verify_model_file(dest_path, expected_sha256, expected_size):
        try:
            os.remove(dest_path)
        except OSError:
            pass
        raise FaceModelError(
            f"Downloaded {filename} failed SHA-256 verification; "
            f"the file was removed. Check your network connection."
        )
    print(f"Verified {filename} ({expected_size} bytes, SHA-256 OK).")
    return dest_path


def ensure_models_available(auto_download: bool = True) -> dict[str, str]:
    """Ensure both YuNet and SFace models exist; return their paths."""
    yunet_path = ensure_model(
        YUNET_FILENAME, YUNET_URLS, YUNET_SHA256, YUNET_SIZE,
        get_yunet_model_path(), auto_download=auto_download,
    )
    sface_path = ensure_model(
        SFACE_FILENAME, SFACE_URLS, SFACE_SHA256, SFACE_SIZE,
        get_sface_model_path(), auto_download=auto_download,
    )
    return {"yunet": yunet_path, "sface": sface_path}


def models_available() -> bool:
    """Return True when both verified model files are already on disk."""
    return verify_model_file(
        get_yunet_model_path(), YUNET_SHA256, YUNET_SIZE
    ) and verify_model_file(
        get_sface_model_path(), SFACE_SHA256, SFACE_SIZE
    )
