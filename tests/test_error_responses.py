from __future__ import annotations

from app.core.config import get_settings
from tests.helpers import auth_headers, generate_plan, register_user, seed_planner_exercises, update_profile


def test_validation_error_response_is_unified(client) -> None:
    response = client.post(
        "/auth/register",
        json={
            "email": "broken@example.com",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["message"] == "Request validation failed."
    assert isinstance(payload["details"], list)


def test_conflict_error_response_is_unified(db_client) -> None:
    first = db_client.post(
        "/auth/register",
        json={
            "email": "dup@example.com",
            "password": "StrongPass123!",
            "display_name": "dup",
        },
    )
    assert first.status_code == 201

    duplicate = db_client.post(
        "/auth/register",
        json={
            "email": "dup@example.com",
            "password": "StrongPass123!",
            "display_name": "dup",
        },
    )
    assert duplicate.status_code == 409
    payload = duplicate.json()
    assert payload["code"] == "conflict"
    assert payload["message"] == "Email is already registered."
    assert payload["details"] is None


def test_unauthorized_error_response_is_unified(db_client) -> None:
    response = db_client.get("/plans")

    assert response.status_code == 401
    payload = response.json()
    assert payload["code"] == "unauthorized"
    assert payload["message"] == "Not authenticated."


def test_provider_not_configured_response_is_unified(db_client, monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "")
    get_settings.cache_clear()

    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 503
    payload = response.json()
    assert payload["code"] == "provider_not_configured"
    assert payload["message"] == "SILICONFLOW_API_KEY is not configured."
    assert payload["details"] is None
