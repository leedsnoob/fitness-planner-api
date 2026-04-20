from __future__ import annotations

from datetime import date, timedelta

from tests.helpers import auth_headers, find_session_exercise, generate_plan, register_user, seed_planner_exercises, update_profile
from tests.test_workout_logs_api import _create_log


def test_volume_and_adherence_analytics_return_expected_aggregates(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    session_one = plan["sessions"][0]
    session_two = plan["sessions"][1]
    first_entry = session_one["exercises"][0]
    second_entry = session_two["exercises"][0]

    create_one = _create_log(
        db_client,
        token,
        plan_id=plan["id"],
        session_id=session_one["id"],
        session_exercise_id=first_entry["id"],
        completion_status="COMPLETED",
        completed_sets=4,
        completed_reps_total=40,
        performed_on=date.today().isoformat(),
    )
    assert create_one.status_code == 201

    create_two = _create_log(
        db_client,
        token,
        plan_id=plan["id"],
        session_id=session_two["id"],
        session_exercise_id=second_entry["id"],
        completion_status="SKIPPED",
        completed_sets=0,
        completed_reps_total=0,
        performed_on=(date.today() - timedelta(days=1)).isoformat(),
    )
    assert create_two.status_code == 201

    volume_response = db_client.get("/analytics/volume", headers=auth_headers(token), params={"days": 7})
    assert volume_response.status_code == 200
    volume = volume_response.json()
    assert volume["total_logged_sessions"] == 2
    assert volume["total_completed_sets"] == 4
    assert volume["total_completed_reps"] == 40
    assert len(volume["daily_points"]) == 2

    adherence_response = db_client.get(
        "/analytics/adherence",
        headers=auth_headers(token),
        params={"plan_id": plan["id"]},
    )
    assert adherence_response.status_code == 200
    adherence = adherence_response.json()
    assert adherence["planned_exercises"] == 15
    assert adherence["logged_exercises"] == 2
    assert adherence["completed_exercises"] == 1
    assert adherence["partial_exercises"] == 0
    assert adherence["skipped_exercises"] == 1
    assert adherence["adherence_rate"] == 1 / 15


def test_replacement_analytics_reads_revision_history(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    target = find_session_exercise(plan, "main_push")

    adjust_response = db_client.post(
        f"/plans/{plan['id']}/adjustments",
        headers=auth_headers(token),
        json={
            "session_exercise_id": target["id"],
            "reason": "DISLIKE",
            "detail_note": "Prefer a different press.",
        },
    )
    assert adjust_response.status_code == 200

    replacement_response = db_client.get(
        "/analytics/replacements",
        headers=auth_headers(token),
        params={"plan_id": plan["id"]},
    )
    assert replacement_response.status_code == 200
    payload = replacement_response.json()
    assert payload["total_revisions"] == 1
    assert payload["by_reason"]["DISLIKE"] == 1
    assert len(payload["latest_revisions"]) == 1
    assert payload["latest_revisions"][0]["old_exercise_name"] != payload["latest_revisions"][0]["new_exercise_name"]
