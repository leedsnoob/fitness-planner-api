#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.data.exercise_seed import build_curated_seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a cleaned exercise seed file from a raw snapshot.")
    parser.add_argument(
        "--input",
        default="data/raw/wger_exercises_snapshot.json",
        help="Path to the raw snapshot JSON file.",
    )
    parser.add_argument(
        "--output",
        default="data/seeds/exercises_cleaned.json",
        help="Path to the curated seed JSON file.",
    )
    parser.add_argument(
        "--target-size",
        type=int,
        default=140,
        help="Target number of curated exercises.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    raw_records = json.loads(input_path.read_text(encoding="utf-8"))
    curated = build_curated_seed(raw_records, target_size=args.target_size)
    output_path.write_text(json.dumps(curated, indent=2), encoding="utf-8")
    print(f"Saved {len(curated)} curated records to {output_path}")


if __name__ == "__main__":
    main()
