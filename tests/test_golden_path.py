from __future__ import annotations

from datetime import date

from tests.helpers import auth_headers, find_session_exercise, generate_plan, register_user, seed_planner_exercises, update_profile


def test_full_user_journey_golden_path(db_client, monkeypatch) -> None:
    token = register_user(db_client, email="golden@example.com")
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
    updated_plan = adjustment.json()["updated_plan"]

    create_log = db_client.post(
        "/workout-logs",
        headers=auth_headers(token),
        json={
            "plan_id": updated_plan["id"],
            "session_id": session["id"],
            "session_exercise_id": target["id"],
            "completion_status": "COMPLETED",
            "completed_sets": 4,
            "completed_reps_total": 40,
            "effort_rating": 7,
            "note": "Good session.",
            "performed_on": date.today().isoformat(),
        },
    )
    assert create_log.status_code == 201

    volume = db_client.get("/analytics/volume", headers=auth_headers(token))
    adherence = db_client.get(f"/analytics/adherence?plan_id={plan['id']}", headers=auth_headers(token))
    replacements = db_client.get(f"/analytics/replacements?plan_id={plan['id']}", headers=auth_headers(token))

    assert volume.status_code == 200
    assert adherence.status_code == 200
    assert replacements.status_code == 200

    monkeypatch.setattr(
        "app.services.plan_explanations.generate_explanation_text",
        lambda *_args, **_kwargs: ("This plan and revision explanation is stored successfully.", "Qwen/Qwen3.6-35B-A3B"),
    )

    plan_explanation = db_client.post(f"/plans/{plan['id']}/explain", headers=auth_headers(token))
    revision_explanation = db_client.post(
        f"/plans/{plan['id']}/revisions/1/explain",
        headers=auth_headers(token),
    )

    assert plan_explanation.status_code == 201
    assert revision_explanation.status_code == 201

    explanation_history = db_client.get(f"/plans/{plan['id']}/explanations", headers=auth_headers(token))
    revision_history = db_client.get(
        f"/plans/{plan['id']}/revisions/1/explanations",
        headers=auth_headers(token),
    )

    assert explanation_history.status_code == 200
    assert revision_history.status_code == 200
    assert explanation_history.json()["total"] >= 1
    assert revision_history.json()["total"] == 1
