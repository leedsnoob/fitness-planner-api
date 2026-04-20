#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.data.exercise_import import import_exercises
from app.db.session import Base, get_engine


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the cleaned exercise seed into PostgreSQL.")
    parser.add_argument(
        "--input",
        default="data/seeds/exercises_cleaned.json",
        help="Path to the curated seed JSON file.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    records = json.loads(input_path.read_text(encoding="utf-8"))
    Base.metadata.create_all(bind=get_engine())
    result = import_exercises(records)
    print(
        f"Imported exercises from {input_path}: "
        f"{result['inserted']} inserted, {result['updated']} updated"
    )


if __name__ == "__main__":
    main()
