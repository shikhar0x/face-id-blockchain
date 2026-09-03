import os
from io import BytesIO

import requests
from PIL import Image


def try_download_image(image_url: str, output_path: str) -> bool:
    """
    Try to download and validate an image from a URL.
    """

    try:
        response = requests.get(
            image_url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image.verify()

        image = Image.open(BytesIO(response.content)).convert("RGB")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "JPEG")

        return True

    except Exception as exc:
        print(f"Image retrieval failed: {exc}")
        return False


def download_candidate_image(
    image_url: str | None,
    thumbnail_url: str | None,
    output_path: str,
) -> str:
    """
    Download a candidate image.

    Tries the main image URL first and falls back to the thumbnail.

    Returns:
        'image'       if the main image succeeded
        'thumbnail'  if the thumbnail succeeded
        'failed'     if both failed
    """

    if image_url:
        print("Trying main image...")
        if try_download_image(image_url, output_path):
            return "image"

    if thumbnail_url:
        print("Main image failed. Trying thumbnail...")
        if try_download_image(thumbnail_url, output_path):
            return "thumbnail"

    return "failed"