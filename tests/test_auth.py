def test_register_returns_access_token_and_profile(db_client) -> None:
    response = db_client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "StrongPass123!",
            "display_name": "Alex",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "user@example.com"
    assert payload["user"]["profile"]["display_name"] == "Alex"


def test_register_rejects_duplicate_email(db_client) -> None:
    payload = {
        "email": "user@example.com",
        "password": "StrongPass123!",
        "display_name": "Alex",
    }

    first_response = db_client.post("/auth/register", json=payload)
    second_response = db_client.post("/auth/register", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered."


def test_login_returns_access_token_for_valid_credentials(db_client) -> None:
    register_payload = {
        "email": "user@example.com",
        "password": "StrongPass123!",
        "display_name": "Alex",
    }
    db_client.post("/auth/register", json=register_payload)

    response = db_client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["email"] == "user@example.com"


def test_login_rejects_invalid_credentials(db_client) -> None:
    response = db_client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
