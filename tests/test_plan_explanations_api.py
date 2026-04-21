from __future__ import annotations

from app.core.config import get_settings
from app.data.exercise_import import import_exercises
from tests.helpers import (
    auth_headers,
    find_session_exercise,
    generate_plan,
    register_user,
    seed_planner_exercises,
    update_profile,
)


def _seed_explanation_alternative() -> None:
    import_exercises(
        [
            {
                "source_id": "h-2011",
                "source_name": "wger",
                "name": "Resistance Band Chest Press",
                "description": "Horizontal press with a band.",
                "primary_muscles": ["chest"],
                "secondary_muscles": ["triceps"],
                "movement_pattern": "horizontal_push",
                "equipment_tags": ["resistance_band"],
                "environment_tags": ["both"],
                "difficulty": "beginner",
                "impact_level": "low",
                "contraindication_tags": [],
                "is_custom": False,
            }
        ]
    )


def test_create_plan_explanation_and_list_history(db_client, monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    get_settings.cache_clear()
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)

    def _fake_generate(*args, **kwargs):
        return ("This weekly plan balances push, lower body, pull, and core work.", "Qwen/Qwen3-8B")

    monkeypatch.setattr("app.services.plan_explanations.generate_explanation_text", _fake_generate)

    response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["explanation_scope"] == "PLAN"
    assert payload["revision_number"] is None
    assert payload["provider"] == "siliconflow"
    assert payload["model_name"] == "Qwen/Qwen3-8B"
    assert payload["output_text"].startswith("This weekly plan")
    assert payload["input_snapshot"]["scope"] == "PLAN"
    assert payload["input_snapshot"]["plan"]["id"] == plan["id"]

    list_response = db_client.get(
        f"/plans/{plan['id']}/explanations",
        headers=auth_headers(token),
    )
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["explanation_scope"] == "PLAN"


def test_create_revision_explanation_and_enforce_owner_scope(db_client, monkeypatch) -> None:
    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    get_settings.cache_clear()
    token = register_user(db_client)
    other_token = register_user(db_client, email="other@example.com")
    update_profile(db_client, token)
    update_profile(db_client, other_token)
    seed_planner_exercises()
    _seed_explanation_alternative()
    plan = generate_plan(db_client, token)
    target = find_session_exercise(plan, "main_push")

    adjustment = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers=auth_headers(token),
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
        },
    )
    assert adjustment.status_code == 200

    def _fake_generate(*args, **kwargs):
        return ("This replacement avoids a previously disliked movement while preserving the same training intent.", "Qwen/Qwen3-8B")

    monkeypatch.setattr("app.services.plan_explanations.generate_explanation_text", _fake_generate)

    response = db_client.post(
        f"/plans/{plan['id']}/revisions/1/explain",
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["explanation_scope"] == "REVISION"
    assert payload["revision_number"] == 1
    assert payload["input_snapshot"]["scope"] == "REVISION"
    assert payload["input_snapshot"]["revision"]["revision_number"] == 1

    history = db_client.get(
        f"/plans/{plan['id']}/revisions/1/explanations",
        headers=auth_headers(token),
    )
    assert history.status_code == 200
    assert history.json()["total"] == 1

    denied = db_client.get(
        f"/plans/{plan['id']}/revisions/1/explanations",
        headers=auth_headers(other_token),
    )
    assert denied.status_code == 404


def test_plan_explanation_returns_service_error_when_provider_not_configured(db_client, monkeypatch) -> None:
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
