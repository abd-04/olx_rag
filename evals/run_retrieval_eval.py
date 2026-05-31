import json
import os
from pathlib import Path

import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
DATASET = Path(__file__).with_name("queries.json")


def recall_at_k(expected_urls, returned_urls):
    if not expected_urls:
        return None
    return len(set(expected_urls) & set(returned_urls)) / len(set(expected_urls))


def main():
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    measured = []
    for case in cases:
        response = requests.post(
            f"{BACKEND_URL}/search",
            json={
                "question": case["question"],
                "filters": case["filters"],
                "top_k": 5,
            },
            timeout=30,
        )
        response.raise_for_status()
        listings = response.json()["listings"]
        returned_urls = [listing["url"] for listing in listings]
        recall = recall_at_k(case["relevant_urls"], returned_urls)
        if recall is not None:
            measured.append(recall)
        print(f"\nQuery: {case['question']}")
        print(f"Returned: {len(returned_urls)}")
        print(f"Recall@5: {'label URLs first' if recall is None else f'{recall:.2f}'}")
        for listing in listings:
            print(f"- {listing['title']} | {listing['url']}")

    if measured:
        print(f"\nMean Recall@5: {sum(measured) / len(measured):.2f}")
    else:
        print("\nAdd relevant_urls labels after reviewing results to establish a Recall@5 baseline.")


if __name__ == "__main__":
    main()
