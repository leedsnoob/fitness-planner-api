from app.data.exercise_import import import_exercises


def register_user(client, email: str) -> str:
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


def seed_public_exercises() -> None:
    import_exercises(
        [
            {
                "source_id": "pub-1",
                "source_name": "wger",
                "name": "Barbell Bench Press",
                "description": "Press the barbell away from the chest.",
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
                "source_id": "pub-2",
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
            },
        ]
    )


def custom_exercise_payload(name: str) -> dict:
    return {
        "name": name,
        "description": "Custom movement for testing.",
        "primary_muscles": ["glutes"],
        "secondary_muscles": ["quads"],
        "movement_pattern": "lunge",
        "equipment_tags": ["resistance_band"],
        "environment_tags": ["both"],
        "difficulty": "beginner",
        "impact_level": "medium",
        "contraindication_tags": ["knee_discomfort"],
    }


def test_list_exercises_supports_filtering_and_visibility(db_client) -> None:
    seed_public_exercises()
    owner_token = register_user(db_client, "owner@example.com")
    other_token = register_user(db_client, "other@example.com")

    owner_create = db_client.post(
        "/me/custom-exercises",
        headers=auth_headers(owner_token),
        json=custom_exercise_payload("Resistance Band Split Squat"),
    )
    assert owner_create.status_code == 201

    other_create = db_client.post(
        "/me/custom-exercises",
        headers=auth_headers(other_token),
        json=custom_exercise_payload("Private Reverse Lunge"),
    )
    assert other_create.status_code == 201

    anonymous_response = db_client.get("/exercises")
    assert anonymous_response.status_code == 200
    anonymous_names = [item["name"] for item in anonymous_response.json()["items"]]
    assert "Barbell Bench Press" in anonymous_names
    assert "Bodyweight Squat" in anonymous_names
    assert "Resistance Band Split Squat" not in anonymous_names

    filtered_response = db_client.get(
        "/exercises",
        headers=auth_headers(owner_token),
        params={
            "difficulty": "beginner",
            "environment": "home",
            "movement_pattern": "lunge",
        },
    )

    assert filtered_response.status_code == 200
    payload = filtered_response.json()
    assert payload["total"] == 1
    assert [item["name"] for item in payload["items"]] == ["Resistance Band Split Squat"]


def test_get_exercise_detail_hides_other_users_custom_exercise(db_client) -> None:
    seed_public_exercises()
    owner_token = register_user(db_client, "owner@example.com")
    other_token = register_user(db_client, "other@example.com")

    create_response = db_client.post(
        "/me/custom-exercises",
        headers=auth_headers(owner_token),
        json=custom_exercise_payload("Owner Only Exercise"),
    )
    exercise_id = create_response.json()["id"]

    public_response = db_client.get("/exercises/1")
    assert public_response.status_code == 200

    owner_response = db_client.get(f"/exercises/{exercise_id}", headers=auth_headers(owner_token))
    assert owner_response.status_code == 200
    assert owner_response.json()["name"] == "Owner Only Exercise"

    other_response = db_client.get(f"/exercises/{exercise_id}", headers=auth_headers(other_token))
    assert other_response.status_code == 404


def test_create_and_update_custom_exercise_are_owner_scoped(db_client) -> None:
    seed_public_exercises()
    owner_token = register_user(db_client, "owner@example.com")
    other_token = register_user(db_client, "other@example.com")

    create_response = db_client.post(
        "/me/custom-exercises",
        headers=auth_headers(owner_token),
        json=custom_exercise_payload("Custom Step Up"),
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["name"] == "Custom Step Up"
    assert payload["source_name"] == "custom"
    assert payload["is_custom"] is True

    exercise_id = payload["id"]

    patch_response = db_client.patch(
        f"/me/custom-exercises/{exercise_id}",
        headers=auth_headers(owner_token),
        json={
            "name": "Custom Step Up Revised",
            "difficulty": "intermediate",
            "equipment_tags": ["dumbbell"],
        },
    )

    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Custom Step Up Revised"
    assert patch_response.json()["difficulty"] == "intermediate"
    assert patch_response.json()["equipment_tags"] == ["dumbbell"]

    forbidden_response = db_client.patch(
        f"/me/custom-exercises/{exercise_id}",
        headers=auth_headers(other_token),
        json={"name": "Should Not Work"},
    )
    assert forbidden_response.status_code == 404


def test_delete_custom_exercise_cleans_profile_blocked_references(db_client) -> None:
    owner_token = register_user(db_client, "owner@example.com")
    create_response = db_client.post(
        "/me/custom-exercises",
        headers=auth_headers(owner_token),
        json=custom_exercise_payload("Disposable Exercise"),
    )
    exercise_id = create_response.json()["id"]

    profile_update = db_client.put(
        "/me/profile",
        headers=auth_headers(owner_token),
        json={
            "display_name": "owner",
            "training_level": "BEGINNER",
            "preferred_environment": "HOME",
            "primary_goal": "GENERAL_FITNESS",
            "training_days_per_week": 3,
            "available_equipment": ["resistance_band"],
            "discomfort_tags": [],
            "blocked_exercise_ids": [exercise_id, 999],
        },
    )
    assert profile_update.status_code == 200

    delete_response = db_client.delete(
        f"/me/custom-exercises/{exercise_id}",
        headers=auth_headers(owner_token),
    )
    assert delete_response.status_code == 204

    profile_response = db_client.get("/me/profile", headers=auth_headers(owner_token))
    assert profile_response.status_code == 200
    assert profile_response.json()["profile"]["blocked_exercise_ids"] == [999]

    exercise_response = db_client.get(f"/exercises/{exercise_id}", headers=auth_headers(owner_token))
    assert exercise_response.status_code == 404
