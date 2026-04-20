from app.data.exercise_import import import_exercises


def _register_user(client, email: str = "user@example.com") -> str:
    response = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "StrongPass123!",
            "display_name": "Alex",
        },
    )
    return response.json()["access_token"]


def _update_profile(client, token: str, **overrides) -> None:
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
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 200


def _seed_planner_exercises() -> None:
    import_exercises(
        [
            {
                "source_id": "2001",
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
                "source_id": "2002",
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
                "source_id": "2003",
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
                "source_id": "2004",
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
                "source_id": "2005",
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
                "source_id": "2006",
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
                "source_id": "2007",
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
                "source_id": "2008",
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
                "source_id": "2009",
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
                "source_id": "2010",
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


def _generate_plan(client, token: str, *, split: str = "full_body", goal: str = "MUSCLE_GAIN", days: int = 3, environment: str = "HOME"):
    response = client.post(
        "/plans/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "split": split,
            "goal": goal,
            "training_days_per_week": days,
            "environment": environment,
        },
    )
    assert response.status_code == 201
    return response.json()


def _find_session_exercise(plan_payload: dict, slot_type: str) -> dict:
    for session in plan_payload["sessions"]:
        for exercise in session["exercises"]:
            if exercise["slot_type"] == slot_type:
                return exercise
    raise AssertionError(f"Missing slot type: {slot_type}")


def test_adjustment_creates_revision_and_returns_latest_plan(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(db_client, token)
    _seed_planner_exercises()
    plan = _generate_plan(db_client, token)
    target = _find_session_exercise(plan, "main_push")

    response = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
            "detail_note": "I do not want this pressing variation.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["revision_number"] == 1
    assert payload["old_exercise"]["id"] == target["exercise"]["id"]
    assert payload["new_exercise"]["id"] != target["exercise"]["id"]
    assert payload["updated_plan"]["current_revision_number"] == 1
    assert payload["updated_plan"]["id"] == plan["id"]

    revisions_response = db_client.get(
        f"/plans/{plan['id']}/revisions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revisions_response.status_code == 200
    assert revisions_response.json()["total"] == 1

    revision_detail = db_client.get(
        f"/plans/{plan['id']}/revisions/1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revision_detail.status_code == 200
    assert revision_detail.json()["before_snapshot"]["id"] == plan["id"]
    assert revision_detail.json()["after_snapshot"]["current_revision_number"] == 1


def test_adjustment_too_difficult_prefers_lower_difficulty_replacement(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(db_client, token)
    _seed_planner_exercises()
    plan = _generate_plan(db_client, token)
    target = _find_session_exercise(plan, "hinge_support")

    response = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_exercise_id": target["id"],
            "reason": "TOO_DIFFICULT",
            "detail_note": "This feels too advanced today.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["old_exercise"]["difficulty"] == "intermediate"
    assert payload["new_exercise"]["difficulty"] == "beginner"


def test_adjustment_supports_environment_and_equipment_overrides(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(
        db_client,
        token,
        preferred_environment="GYM",
        available_equipment=[],
    )
    _seed_planner_exercises()
    plan = _generate_plan(db_client, token, environment="GYM")
    target = _find_session_exercise(plan, "main_push")
    assert target["exercise"]["name"] == "Barbell Bench Press"

    response = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_exercise_id": target["id"],
            "reason": "ENVIRONMENT_MISMATCH",
            "override_environment": "HOME",
            "temporary_unavailable_equipment": ["barbell", "bench"],
            "detail_note": "I need a home-compatible option tonight.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["new_exercise"]["name"] == "Dumbbell Floor Press"


def test_adjustment_returns_404_for_non_owner_or_wrong_session_exercise(db_client) -> None:
    owner_token = _register_user(db_client)
    other_token = _register_user(db_client, email="other@example.com")
    _update_profile(db_client, owner_token)
    _update_profile(db_client, other_token)
    _seed_planner_exercises()
    owner_plan = _generate_plan(db_client, owner_token)
    other_plan = _generate_plan(db_client, other_token)
    target = _find_session_exercise(owner_plan, "main_push")
    wrong_target = _find_session_exercise(other_plan, "main_push")

    forbidden = db_client.post(
        f"/plans/{owner_plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
        },
    )
    assert forbidden.status_code == 404

    wrong_reference = db_client.post(
        f"/plans/{owner_plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "session_exercise_id": wrong_target["id"],
            "reason": "DISLIKE",
        },
    )
    assert wrong_reference.status_code == 404


def test_adjustment_returns_409_when_no_compatible_replacement_exists(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(db_client, token)
    _seed_planner_exercises()
    plan = _generate_plan(db_client, token, split="push_pull_legs")
    target = _find_session_exercise(plan, "hinge_accessory")

    response = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "session_exercise_id": target["id"],
            "reason": "PAIN_OR_DISCOMFORT",
            "temporary_discomfort_tags": ["lower_back_discomfort"],
            "detail_note": "My lower back is irritated today.",
        },
    )

    assert response.status_code == 409
