import json
from pathlib import Path


def test_seed_artifacts_are_present_and_well_formed() -> None:
    raw_path = Path("data/raw/wger_exercises_snapshot.json")
    cleaned_path = Path("data/seeds/exercises_cleaned.json")

    assert raw_path.exists()
    assert cleaned_path.exists()

    raw_records = json.loads(raw_path.read_text(encoding="utf-8"))
    cleaned_records = json.loads(cleaned_path.read_text(encoding="utf-8"))

    assert len(raw_records) >= 500
    assert 100 <= len(cleaned_records) <= 180

    required_keys = {
        "source_id",
        "source_name",
        "name",
        "description",
        "primary_muscles",
        "secondary_muscles",
        "movement_pattern",
        "equipment_tags",
        "environment_tags",
        "difficulty",
        "impact_level",
        "contraindication_tags",
        "is_custom",
    }

    assert required_keys <= cleaned_records[0].keys()
    assert len({item["name"] for item in cleaned_records}) == len(cleaned_records)
