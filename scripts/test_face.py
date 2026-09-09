#!/usr/bin/env python3
"""Isolated self-test for Person 1 face detection + embedding.

Usage:
    python scripts/test_face.py <image>

Prints the detected faces (count, bounding boxes, confidences) and the
query-embedding details without running search or blockchain steps.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.face.errors import FaceModelError
from src.face.processor import describe_query_result, process_query_image


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_face.py <image>")
        return 2

    image_path = sys.argv[1]
    print(f"Input image: {image_path}")

    try:
        result = process_query_image(image_path)
    except FaceModelError as exc:
        print(f"MODEL ERROR: {exc}")
        return 2

    if not result.get("success"):
        print(f"FAILED: {result.get('reason')}")
        return 2

    print(describe_query_result(result))
    print(f"Selected face index: {result.get('selected_face_index')}")
    print(f"Bounding box (x,y,w,h): {result.get('bbox')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Embedding dim: {result.get('embedding_dim')}")
    print("Face self-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
