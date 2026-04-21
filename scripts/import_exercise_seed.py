#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import inspect

from app.data.exercise_import import import_exercises
from app.db.session import get_engine


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
    engine = get_engine()
    inspector = inspect(engine)
    if not inspector.has_table("exercises"):
        raise SystemExit(
            "Database schema is not initialized. Run `alembic upgrade head` before importing the seed."
        )
    result = import_exercises(records)
    print(
        f"Imported exercises from {input_path}: "
        f"{result['inserted']} inserted, {result['updated']} updated"
    )


if __name__ == "__main__":
    main()
