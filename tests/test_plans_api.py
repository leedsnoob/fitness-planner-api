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


def test_generate_full_body_plan_persists_sessions_and_scores(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(db_client, token)
    _seed_planner_exercises()

    response = db_client.post(
        "/plans/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "split": "full_body",
            "goal": "MUSCLE_GAIN",
            "training_days_per_week": 3,
            "environment": "HOME",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["goal"] == "MUSCLE_GAIN"
    assert payload["split"] == "full_body"
    assert payload["training_days_per_week"] == 3
    assert len(payload["sessions"]) == 3
    assert all(len(session["exercises"]) == 5 for session in payload["sessions"])
    first_session_exercise = payload["sessions"][0]["exercises"][0]
    assert first_session_exercise["selection_score"] > 0
    assert "pattern_match" in first_session_exercise["score_breakdown"]

    list_response = db_client.get(
        "/plans",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    detail_response = db_client.get(
        f"/plans/{payload['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == payload["id"]


def test_generate_plan_rejects_invalid_split_for_training_days(db_client) -> None:
    token = _register_user(db_client)
    _update_profile(db_client, token, training_days_per_week=3)
    _seed_planner_exercises()

    response = db_client.post(
        "/plans/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "split": "upper_lower",
            "goal": "MUSCLE_GAIN",
            "training_days_per_week": 3,
            "environment": "HOME",
        },
    )

    assert response.status_code == 422
    assert "upper_lower" in response.json()["detail"]


def test_generate_plan_respects_profile_constraints(db_client) -> None:
    token = _register_user(db_client)
    _seed_planner_exercises()
    _update_profile(
        db_client,
        token,
        available_equipment=["dumbbell", "resistance_band"],
        blocked_exercise_ids=[1],
    )

    response = db_client.post(
        "/plans/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "split": "full_body",
            "goal": "GENERAL_FITNESS",
            "training_days_per_week": 3,
            "environment": "HOME",
        },
    )

    assert response.status_code == 201
    selected_names = [
        exercise["exercise"]["name"]
        for session in response.json()["sessions"]
        for exercise in session["exercises"]
    ]
    assert "Barbell Bench Press" not in selected_names
    assert "Dumbbell Floor Press" in selected_names


def test_plan_detail_is_owner_scoped_and_delete_cascades(db_client) -> None:
    owner_token = _register_user(db_client)
    other_token = _register_user(db_client, email="other@example.com")
    _update_profile(db_client, owner_token)
    _seed_planner_exercises()

    create_response = db_client.post(
        "/plans/generate",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "split": "full_body",
            "goal": "MUSCLE_GAIN",
            "training_days_per_week": 3,
            "environment": "HOME",
        },
    )
    assert create_response.status_code == 201
    plan_id = create_response.json()["id"]

    forbidden_response = db_client.get(
        f"/plans/{plan_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_response.status_code == 404

    delete_response = db_client.delete(
        f"/plans/{plan_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert delete_response.status_code == 204

    fetch_deleted = db_client.get(
        f"/plans/{plan_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert fetch_deleted.status_code == 404
