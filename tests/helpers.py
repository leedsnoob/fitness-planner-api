from __future__ import annotations

from app.data.exercise_import import import_exercises


def register_user(client, email: str = "user@example.com") -> str:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "display_name": email.split("@")[0],
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def update_profile(client, token: str, **overrides) -> None:
    payload = {
        "display_name": "Alex",
        "training_level": "INTERMEDIATE",
        "preferred_environment": "HOME",
        "primary_goal": "MUSCLE_GAIN",
        "training_days_per_week": 3,
        "available_equipment": ["dumbbell", "resistance_band"],
        "discomfort_tags": [],
        "blocked_exercise_ids": [],
    }
    payload.update(overrides)
    response = client.put(
        "/me/profile",
        headers=auth_headers(token),
        json=payload,
    )
    assert response.status_code == 200


def seed_planner_exercises() -> None:
    import_exercises(
        [
            {
                "source_id": "h-2001",
                "source_name": "wger",
                "name": "Barbell Bench Press",
                "description": "Gym chest press.",
                "primary_muscles": ["chest"],
                "secondary_muscles": ["triceps", "shoulders"],
                "movement_pattern": "horizontal_push",
                "equipment_tags": ["barbell", "bench"],
                "environment_tags": ["gym"],
                "difficulty": "intermediate",
                "impact_level": "low",
                "contraindication_tags": ["shoulder_discomfort"],
                "is_custom": False,
            },
            {
                "source_id": "h-2002",
                "source_name": "wger",
                "name": "Dumbbell Floor Press",
                "description": "Home-friendly press.",
                "primary_muscles": ["chest"],
                "secondary_muscles": ["triceps"],
                "movement_pattern": "horizontal_push",
                "equipment_tags": ["dumbbell"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "h-2003",
                "source_name": "wger",
                "name": "Dumbbell Shoulder Press",
                "description": "Standing shoulder press.",
                "primary_muscles": ["shoulders"],
                "secondary_muscles": ["triceps"],
                "movement_pattern": "vertical_push",
                "equipment_tags": ["dumbbell"],
                "environment_tags": ["both"],
                "difficulty": "intermediate",
                "impact_level": "low",
                "contraindication_tags": ["shoulder_discomfort"],
                "is_custom": False,
            },
            {
                "source_id": "h-2004",
                "source_name": "wger",
                "name": "Resistance Band Pulldown",
                "description": "Vertical pull variation.",
                "primary_muscles": ["lats"],
                "secondary_muscles": ["biceps"],
                "movement_pattern": "vertical_pull",
                "equipment_tags": ["resistance_band"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "h-2005",
                "source_name": "wger",
                "name": "Dumbbell Row",
                "description": "Horizontal pull variation.",
                "primary_muscles": ["lats"],
                "secondary_muscles": ["biceps"],
                "movement_pattern": "horizontal_pull",
                "equipment_tags": ["dumbbell"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "h-2006",
                "source_name": "wger",
                "name": "Goblet Squat",
                "description": "Lower-body squat pattern.",
                "primary_muscles": ["quads", "glutes"],
                "secondary_muscles": ["hamstrings"],
                "movement_pattern": "squat",
                "equipment_tags": ["dumbbell"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": ["knee_discomfort"],
                "is_custom": False,
            },
            {
                "source_id": "h-2007",
                "source_name": "wger",
                "name": "Reverse Lunge",
                "description": "Lower-body lunge pattern.",
                "primary_muscles": ["quads", "glutes"],
                "secondary_muscles": ["hamstrings"],
                "movement_pattern": "lunge",
                "equipment_tags": ["bodyweight"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": ["knee_discomfort"],
                "is_custom": False,
            },
            {
                "source_id": "h-2008",
                "source_name": "wger",
                "name": "Dumbbell Romanian Deadlift",
                "description": "Hip hinge variation.",
                "primary_muscles": ["hamstrings", "glutes"],
                "secondary_muscles": ["lower_back"],
                "movement_pattern": "hinge",
                "equipment_tags": ["dumbbell"],
                "environment_tags": ["both"],
                "difficulty": "intermediate",
                "impact_level": "medium",
                "contraindication_tags": ["lower_back_discomfort"],
                "is_custom": False,
            },
            {
                "source_id": "h-2009",
                "source_name": "wger",
                "name": "Dead Bug",
                "description": "Core stability exercise.",
                "primary_muscles": ["core"],
                "secondary_muscles": ["abs"],
                "movement_pattern": "core",
                "equipment_tags": ["bodyweight"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "h-2010",
                "source_name": "wger",
                "name": "Plank",
                "description": "Core brace.",
                "primary_muscles": ["core"],
                "secondary_muscles": ["abs"],
                "movement_pattern": "core",
                "equipment_tags": ["bodyweight"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
        ]
    )


def generate_plan(
    client,
    token: str,
    *,
    split: str = "full_body",
    goal: str = "MUSCLE_GAIN",
    days: int = 3,
    environment: str = "HOME",
) -> dict:
    response = client.post(
        "/plans/generate",
        headers=auth_headers(token),
        json={
            "split": split,
            "goal": goal,
            "training_days_per_week": days,
            "environment": environment,
        },
    )
    assert response.status_code == 201
    return response.json()


def find_session_exercise(plan_payload: dict, slot_type: str) -> dict:
    for session in plan_payload["sessions"]:
        for exercise in session["exercises"]:
            if exercise["slot_type"] == slot_type:
                return exercise
    raise AssertionError(f"Missing slot type: {slot_type}")
