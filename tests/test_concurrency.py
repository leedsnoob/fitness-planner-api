from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.data.exercise_import import import_exercises
from app.main import create_app


def _register_user(client, email: str) -> str:
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


def _update_profile(client, token: str) -> None:
    response = client.put(
        "/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Alex",
            "training_level": "INTERMEDIATE",
            "preferred_environment": "HOME",
            "primary_goal": "MUSCLE_GAIN",
            "training_days_per_week": 3,
            "available_equipment": ["dumbbell", "resistance_band"],
            "discomfort_tags": [],
            "blocked_exercise_ids": [],
        },
    )
    assert response.status_code == 200


def _seed_planner_exercises() -> None:
    import_exercises(
        [
            {
                "source_id": "c-2001",
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
                "source_id": "c-2002",
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
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "c-2003",
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
                "source_id": "c-2004",
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
                "source_id": "c-2005",
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
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "c-2006",
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
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "c-2007",
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
                "contraindication_tags": [],
                "is_custom": False,
            },
            {
                "source_id": "c-2008",
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
        ]
    )


def _generate_plan(app, token: str) -> tuple[int, dict]:
    with TestClient(app) as client:
        response = client.post(
            "/plans/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "split": "full_body",
                "goal": "MUSCLE_GAIN",
                "training_days_per_week": 3,
                "environment": "HOME",
            },
        )
        return response.status_code, response.json()


def _adjust_plan(app, plan_id: int, session_exercise_id: int, token: str, reason: str) -> tuple[int, dict]:
    with TestClient(app) as client:
        response = client.post(
            f"/plans/{plan_id}/adjustments",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "session_exercise_id": session_exercise_id,
                "reason": reason,
            },
        )
        return response.status_code, response.json()


def test_parallel_plan_generation_supports_multiple_users(db_client) -> None:
    _seed_planner_exercises()
    app = create_app()
    token_one = _register_user(db_client, "parallel-one@example.com")
    token_two = _register_user(db_client, "parallel-two@example.com")
    _update_profile(db_client, token_one)
    _update_profile(db_client, token_two)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda token: _generate_plan(app, token), [token_one, token_two]))

    assert [status for status, _ in results] == [201, 201]
    plan_ids = [payload["id"] for _, payload in results]
    assert len(set(plan_ids)) == 2

    plans_one = db_client.get("/plans", headers={"Authorization": f"Bearer {token_one}"})
    plans_two = db_client.get("/plans", headers={"Authorization": f"Bearer {token_two}"})

    assert plans_one.status_code == 200
    assert plans_two.status_code == 200
    assert plans_one.json()["total"] == 1
    assert plans_two.json()["total"] == 1


def test_parallel_adjustments_on_same_plan_are_serialized(db_client) -> None:
    _seed_planner_exercises()
    app = create_app()
    token = _register_user(db_client, "parallel-adjust@example.com")
    _update_profile(db_client, token)
    status_code, plan_payload = _generate_plan(app, token)

    assert status_code == 201
    target_entry = next(
        exercise
        for session in plan_payload["sessions"]
        for exercise in session["exercises"]
        if exercise["slot_type"] == "main_push"
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                lambda reason: _adjust_plan(app, plan_payload["id"], target_entry["id"], token, reason),
                ["DISLIKE", "WANTS_VARIETY"],
            )
        )

    assert sorted(status for status, _ in results) == [200, 200]

    plan_response = db_client.get(
        f"/plans/{plan_payload['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    revisions_response = db_client.get(
        f"/plans/{plan_payload['id']}/revisions",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert plan_response.status_code == 200
    assert revisions_response.status_code == 200
    assert plan_response.json()["current_revision_number"] == 2
    assert revisions_response.json()["total"] == 2
