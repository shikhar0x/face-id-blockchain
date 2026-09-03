import sys
import json

from src.search.parser import parse_visual_matches
from src.search.serpapi_client import (
    upload_image,
    google_lens_search,
)


def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_search.py <image>")
        sys.exit(1)

    image_path = sys.argv[1]

    print(f"Uploading image: {image_path}")

    image_id = upload_image(image_path)

    print(f"Upload successful.")
    print(f"Image ID: {image_id}")
    print()
    print("Running Google Lens search...")

    results = google_lens_search(image_id)
    candidates = parse_visual_matches(results)

    print(f"Parsed {len(candidates)} candidates.")
    
    for candidate in candidates:
        print(
            f"- {candidate.candidate_id}: "
            f"{candidate.title} | "
            f"{candidate.platform} | "
            f"{candidate.page_url}"
        )

    with open("lens_results.json", "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("Search successful.")
    print("Raw results saved to: lens_results.json")


if __name__ == "__main__":
    main()
