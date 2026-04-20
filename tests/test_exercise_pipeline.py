from app.data.exercise_seed import build_curated_seed, clean_wger_exercise


def make_wger_record(
    *,
    exercise_id: int,
    name: str,
    description: str,
    category: str,
    equipment: list[str],
    muscles: list[str],
    muscles_secondary: list[str],
) -> dict:
    return {
        "id": exercise_id,
        "category": {"name": category},
        "equipment": [{"name": item} for item in equipment],
        "muscles": [{"name_en": item} for item in muscles],
        "muscles_secondary": [{"name_en": item} for item in muscles_secondary],
        "translations": [
            {
                "language": 2,
                "name": name,
                "description": description,
            }
        ],
    }


def test_clean_wger_exercise_enriches_supported_fields() -> None:
    record = make_wger_record(
        exercise_id=101,
        name="Bench Press",
        description="<p>Press the barbell away from the chest.</p>",
        category="Chest",
        equipment=["Barbell", "Bench"],
        muscles=["Chest"],
        muscles_secondary=["Triceps", "Shoulders"],
    )

    cleaned = clean_wger_exercise(record)

    assert cleaned is not None
    assert cleaned["source_id"] == "101"
    assert cleaned["source_name"] == "wger"
    assert cleaned["name"] == "Bench Press"
    assert cleaned["description"] == "Press the barbell away from the chest."
    assert cleaned["primary_muscles"] == ["chest"]
    assert cleaned["secondary_muscles"] == ["triceps", "shoulders"]
    assert cleaned["equipment_tags"] == ["barbell", "bench"]
    assert cleaned["environment_tags"] == ["gym"]
    assert cleaned["movement_pattern"] == "horizontal_push"
    assert cleaned["difficulty"] == "intermediate"
    assert cleaned["impact_level"] == "low"
    assert cleaned["contraindication_tags"] == ["shoulder_discomfort"]
    assert cleaned["is_custom"] is False


def test_build_curated_seed_is_deduplicated_and_deterministic() -> None:
    raw_records = [
        make_wger_record(
            exercise_id=201,
            name="Bodyweight Squat",
            description="<p>Stand tall and squat down.</p>",
            category="Legs",
            equipment=["none (bodyweight exercise)"],
            muscles=["Quads"],
            muscles_secondary=["Glutes"],
        ),
        make_wger_record(
            exercise_id=202,
            name="Bodyweight Squat",
            description="<p>Stand tall and squat down.</p>",
            category="Legs",
            equipment=["none (bodyweight exercise)"],
            muscles=["Quads"],
            muscles_secondary=["Glutes"],
        ),
        make_wger_record(
            exercise_id=203,
            name="Bent Over Row",
            description="<p>Row the dumbbells to the torso.</p>",
            category="Back",
            equipment=["Dumbbell"],
            muscles=["Lats"],
            muscles_secondary=["Biceps"],
        ),
    ]

    first = build_curated_seed(raw_records, target_size=2)
    second = build_curated_seed(raw_records, target_size=2)

    assert first == second
    assert [item["name"] for item in first] == ["Bent Over Row", "Bodyweight Squat"]
    assert len(first) == 2
