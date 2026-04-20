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


def _seed_public_exercises() -> None:
    import_exercises(
        [
            {
                "source_id": "1001",
                "source_name": "wger",
                "name": "Bench Press",
                "description": "Barbell chest press.",
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
                "source_id": "1002",
                "source_name": "wger",
                "name": "Band Row",
                "description": "Band-based horizontal pull.",
                "primary_muscles": ["lats"],
                "secondary_muscles": ["biceps"],
                "movement_pattern": "horizontal_pull",
                "equipment_tags": ["resistance_band"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            },
        ]
    )


def test_list_exercises_supports_filters(db_client) -> None:
    _seed_public_exercises()

    response = db_client.get(
        "/exercises",
        params={"movement_pattern": "horizontal_pull", "environment": "HOME"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "Band Row"


def test_get_exercise_returns_public_exercise(db_client) -> None:
    _seed_public_exercises()

    response = db_client.get("/exercises/1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Bench Press"
    assert payload["movement_pattern"] == "horizontal_push"


def test_create_custom_exercise_requires_authentication(db_client) -> None:
    response = db_client.post(
        "/me/custom-exercises",
        json={
            "name": "Custom Floor Press",
            "description": "A home pressing variation.",
            "primary_muscles": ["chest"],
            "secondary_muscles": ["triceps"],
            "movement_pattern": "horizontal_push",
            "equipment_tags": ["dumbbell"],
            "environment_tags": ["both"],
            "difficulty": "beginner",
            "impact_level": "low",
            "contraindication_tags": ["shoulder_discomfort"],
        },
    )

    assert response.status_code == 401


def test_custom_exercise_crud_is_owner_scoped(db_client) -> None:
    owner_token = _register_user(db_client)
    other_token = _register_user(db_client, email="other@example.com")

    create_response = db_client.post(
        "/me/custom-exercises",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Custom Floor Press",
            "description": "A home pressing variation.",
            "primary_muscles": ["chest"],
            "secondary_muscles": ["triceps"],
            "movement_pattern": "horizontal_push",
            "equipment_tags": ["dumbbell"],
            "environment_tags": ["both"],
            "difficulty": "beginner",
            "impact_level": "low",
            "contraindication_tags": ["shoulder_discomfort"],
        },
    )

    assert create_response.status_code == 201
    exercise_id = create_response.json()["id"]
    assert create_response.json()["is_custom"] is True

    list_response = db_client.get(
        "/exercises",
        headers={"Authorization": f"Bearer {owner_token}"},
        params={"include_custom": "true"},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    forbidden_update = db_client.patch(
        f"/me/custom-exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"description": "Updated by someone else."},
    )
    assert forbidden_update.status_code == 404

    update_response = db_client.patch(
        f"/me/custom-exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"description": "Updated by owner."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["description"] == "Updated by owner."

    delete_response = db_client.delete(
        f"/me/custom-exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert delete_response.status_code == 204

    fetch_deleted = db_client.get(
        f"/exercises/{exercise_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert fetch_deleted.status_code == 404
