def test_profile_requires_authentication(db_client) -> None:
    response = db_client.get("/me/profile")

    assert response.status_code == 401


def test_get_profile_returns_current_user_profile(db_client) -> None:
    register_response = db_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPass123!",
            "display_name": "Alex",
        },
    )
    token = register_response.json()["access_token"]

    response = db_client.get(
        "/me/profile",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "user@example.com"
    assert payload["profile"]["display_name"] == "Alex"
    assert payload["profile"]["training_level"] is None
    assert payload["profile"]["preferred_environment"] is None
    assert payload["profile"]["primary_goal"] is None


def test_update_profile_updates_current_user_fields(db_client) -> None:
    register_response = db_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPass123!",
            "display_name": "Alex",
        },
    )
    token = register_response.json()["access_token"]

    response = db_client.put(
        "/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "display_name": "Jordan",
            "training_level": "BEGINNER",
            "preferred_environment": "HOME",
            "primary_goal": "MUSCLE_GAIN",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["display_name"] == "Jordan"
    assert payload["profile"]["training_level"] == "BEGINNER"
    assert payload["profile"]["preferred_environment"] == "HOME"
    assert payload["profile"]["primary_goal"] == "MUSCLE_GAIN"
