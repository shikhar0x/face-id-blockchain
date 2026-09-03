import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

IMAGE_UPLOAD_URL = "https://serpapi.com/image"
SEARCH_URL = "https://serpapi.com/search"


def upload_image(image_path: str) -> str:
    """
    Upload an image to SerpApi and return the image_id.
    """

    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY is not configured")

    with open(image_path, "rb") as image_file:
        response = requests.post(
            IMAGE_UPLOAD_URL,
            params={"api_key": SERPAPI_KEY},
            files={
                "image": (
                    os.path.basename(image_path),
                    image_file,
                    "image/jpeg",
                )
            },
            timeout=30,
        )

    response.raise_for_status()

    data = response.json()

    if "image_id" not in data:
        raise RuntimeError(
            f"SerpApi did not return an image_id: {data}"
        )

    return data["image_id"]


def google_lens_search(image_id: str) -> dict:
    """
    Search Google Lens through SerpApi using an uploaded image.
    """

    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY is not configured")

    response = requests.get(
        SEARCH_URL,
        params={
            "engine": "google_lens",
            "image_id": image_id,
            "api_key": SERPAPI_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()
