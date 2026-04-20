#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen

from app.data.exercise_seed import get_english_translation

BASE_URL = "https://wger.de/api/v2/exerciseinfo/?language=2&limit=200"


def fetch_payload(url: str) -> dict:
    with urlopen(url) as response:  # noqa: S310
        return json.load(response)


def project_record(record: dict) -> dict:
    translation = get_english_translation(record) or {}
    return {
        "id": record["id"],
        "uuid": record.get("uuid"),
        "category": record.get("category"),
        "equipment": record.get("equipment", []),
        "muscles": record.get("muscles", []),
        "muscles_secondary": record.get("muscles_secondary", []),
        "license": record.get("license"),
        "license_author": record.get("license_author"),
        "translations": [translation] if translation else [],
    }


def fetch_snapshot() -> list[dict]:
    url = BASE_URL
    records: list[dict] = []

    while url:
        payload = fetch_payload(url)
        records.extend(project_record(item) for item in payload.get("results", []))
        url = payload.get("next")

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a raw public exercise snapshot from wger.")
    parser.add_argument(
        "--output",
        default="data/raw/wger_exercises_snapshot.json",
        help="Path to the raw snapshot output file.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = fetch_snapshot()
    output_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Saved {len(records)} raw records to {output_path}")


if __name__ == "__main__":
    main()
