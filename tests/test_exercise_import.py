from sqlalchemy import select

from app.data.exercise_import import import_exercises
from app.models.exercise import Exercise


def test_import_exercises_is_idempotent(db_client) -> None:
    seed = [
        {
            "source_id": "901",
            "source_name": "wger",
            "name": "Bodyweight Squat",
            "description": "Stand tall and squat down.",
            "primary_muscles": ["quads"],
            "secondary_muscles": ["glutes"],
            "movement_pattern": "squat",
            "equipment_tags": ["bodyweight"],
            "environment_tags": ["both"],
            "difficulty": "beginner",
            "impact_level": "low",
            "contraindication_tags": ["knee_discomfort"],
            "is_custom": False,
        }
    ]

    first = import_exercises(seed)
    second = import_exercises(seed)

    assert first == {"inserted": 1, "updated": 0}
    assert second == {"inserted": 0, "updated": 1}

    with db_client.app.state.session_factory() as session:
        count = session.execute(select(Exercise)).scalars().all()

    assert len(count) == 1
