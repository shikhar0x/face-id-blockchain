#!/usr/bin/env python3
"""Download + SHA-256-verify the pretrained YuNet/SFace models (Person 1).

The pipeline auto-downloads these on first use; this script lets you fetch
them explicitly (e.g. during setup or before a demo).

Honours FACE_MODEL_DIR. Run from the repository root:

    python scripts/download_face_models.py
"""

import sys
from pathlib import Path

# Add project root to sys.path (src.face.models is stdlib-only).
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.face.models import ensure_models_available, models_available


def main() -> int:
    print("Face-model setup (YuNet detector + SFace recognizer)")
    print("Source: https://github.com/opencv/opencv_zoo")
    print()

    if models_available():
        print("Both models are already present and verified. Nothing to do.")
        return 0

    try:
        paths = ensure_models_available(auto_download=True)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    print()
    print("Model setup complete:")
    print(f"  YuNet: {paths['yunet']}")
    print(f"  SFace: {paths['sface']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
