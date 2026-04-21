from __future__ import annotations

from datetime import date

import httpx

from tests.helpers import (
    auth_headers,
    find_session_exercise,
    generate_plan,
    register_user,
    seed_planner_exercises,
    update_profile,
)
from tests.test_workout_logs_api import _create_log


def test_plan_explanation_failure_does_not_persist_and_plan_flow_continues(db_client, monkeypatch) -> None:
    token = register_user(db_client, email="story-plan@example.com")
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    target = find_session_exercise(plan, "main_push")

    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setattr("app.services.plan_explanations.time.sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "app.services.plan_explanations._request_chat_completion",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(httpx.ReadTimeout("timed out")),
    )

    explain_response = db_client.post(
        f"/plans/{plan['id']}/explain",
        headers=auth_headers(token),
    )
    assert explain_response.status_code == 503
    assert explain_response.json()["code"] == "provider_timeout"

    explanation_history = db_client.get(
        f"/plans/{plan['id']}/explanations",
        headers=auth_headers(token),
    )
    assert explanation_history.status_code == 200
    assert explanation_history.json()["total"] == 0

    plan_detail = db_client.get(f"/plans/{plan['id']}", headers=auth_headers(token))
    assert plan_detail.status_code == 200

    adjustment = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers=auth_headers(token),
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
        },
    )
    assert adjustment.status_code == 200

    revisions = db_client.get(f"/plans/{plan['id']}/revisions", headers=auth_headers(token))
    assert revisions.status_code == 200
    assert revisions.json()["total"] == 1


def test_revision_explanation_failure_does_not_persist_and_logs_analytics_continue(db_client, monkeypatch) -> None:
    token = register_user(db_client, email="story-revision@example.com")
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    target = find_session_exercise(plan, "main_push")
    session = next(
        session for session in plan["sessions"] if any(exercise["id"] == target["id"] for exercise in session["exercises"])
    )

    adjustment = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers=auth_headers(token),
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
        },
    )
    assert adjustment.status_code == 200

    class _BrokenResponse:
        status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"choices": []}

    monkeypatch.setenv("SILICONFLOW_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.plan_explanations._request_chat_completion",
        lambda *_args, **_kwargs: _BrokenResponse(),
    )

    explain_response = db_client.post(
        f"/plans/{plan['id']}/revisions/1/explain",
        headers=auth_headers(token),
    )
    assert explain_response.status_code == 502
    assert explain_response.json()["code"] == "provider_bad_response"

    explanation_history = db_client.get(
        f"/plans/{plan['id']}/revisions/1/explanations",
        headers=auth_headers(token),
    )
    assert explanation_history.status_code == 200
    assert explanation_history.json()["total"] == 0

    revision_detail = db_client.get(
        f"/plans/{plan['id']}/revisions/1",
        headers=auth_headers(token),
    )
    assert revision_detail.status_code == 200

    log_response = _create_log(
        db_client,
        token,
        plan_id=plan["id"],
        session_id=session["id"],
        session_exercise_id=target["id"],
        completion_status="COMPLETED",
        completed_sets=4,
        completed_reps_total=40,
        effort_rating=7,
        note="Main flow still works.",
        performed_on=date.today().isoformat(),
    )
    assert log_response.status_code == 201

    volume = db_client.get("/analytics/volume", headers=auth_headers(token))
    replacements = db_client.get(
        f"/analytics/replacements?plan_id={plan['id']}",
        headers=auth_headers(token),
    )
    assert volume.status_code == 200
    assert replacements.status_code == 200
    assert replacements.json()["total_revisions"] == 1


def test_two_user_story_preserves_owner_scope_for_explanations_and_logs(db_client, monkeypatch) -> None:
    token_one = register_user(db_client, email="story-one@example.com")
    token_two = register_user(db_client, email="story-two@example.com")
    update_profile(db_client, token_one)
    update_profile(db_client, token_two)
    seed_planner_exercises()

    plan_one = generate_plan(db_client, token_one)
    plan_two = generate_plan(db_client, token_two)
    target_one = find_session_exercise(plan_one, "main_push")
    session_one = next(
        session for session in plan_one["sessions"] if any(exercise["id"] == target_one["id"] for exercise in session["exercises"])
    )

    monkeypatch.setattr(
        "app.services.plan_explanations.generate_explanation_text",
        lambda *_args, **_kwargs: ("Stored explanation.", "Qwen/Qwen3.6-35B-A3B"),
    )

    create_explanation = db_client.post(
        f"/plans/{plan_one['id']}/explain",
        headers=auth_headers(token_one),
    )
    assert create_explanation.status_code == 201

    create_log = _create_log(
        db_client,
        token_one,
        plan_id=plan_one["id"],
        session_id=session_one["id"],
        session_exercise_id=target_one["id"],
        completion_status="COMPLETED",
        completed_sets=4,
        completed_reps_total=40,
        effort_rating=6,
        performed_on=date.today().isoformat(),
    )
    assert create_log.status_code == 201

    own_explanations = db_client.get(
        f"/plans/{plan_one['id']}/explanations",
        headers=auth_headers(token_one),
    )
    assert own_explanations.status_code == 200
    assert own_explanations.json()["total"] == 1

    other_explanations = db_client.get(
        f"/plans/{plan_one['id']}/explanations",
        headers=auth_headers(token_two),
    )
    assert other_explanations.status_code == 404

    other_log_detail = db_client.get(
        f"/workout-logs/{create_log.json()['id']}",
        headers=auth_headers(token_two),
    )
    assert other_log_detail.status_code == 404

    other_plan_detail = db_client.get(
        f"/plans/{plan_two['id']}",
        headers=auth_headers(token_two),
    )
    assert other_plan_detail.status_code == 200
