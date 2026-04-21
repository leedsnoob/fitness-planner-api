from __future__ import annotations

from datetime import date

from tests.helpers import (
    auth_headers,
    find_session_exercise,
    generate_plan,
    register_user,
    seed_planner_exercises,
    update_profile,
)


def _create_log(client, token: str, *, plan_id: int, session_id: int, session_exercise_id: int, **overrides):
    payload = {
        "plan_id": plan_id,
        "session_id": session_id,
        "session_exercise_id": session_exercise_id,
        "completion_status": "COMPLETED",
        "completed_sets": 4,
        "completed_reps_total": 40,
        "effort_rating": 7,
        "note": "Solid session.",
        "performed_on": date.today().isoformat(),
    }
    payload.update(overrides)
    return client.post("/workout-logs", headers=auth_headers(token), json=payload)


def test_workout_log_crud_persists_snapshots(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    session = plan["sessions"][0]
    entry = session["exercises"][0]

    create_response = _create_log(
        db_client,
        token,
        plan_id=plan["id"],
        session_id=session["id"],
        session_exercise_id=entry["id"],
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["exercise_name_snapshot"] == entry["exercise"]["name"]
    assert created["slot_type_snapshot"] == entry["slot_type"]
    assert created["movement_pattern_snapshot"] == entry["exercise"]["movement_pattern"]
    assert created["planned_sets"] == entry["sets"]
    assert created["planned_reps"] == entry["reps"]

    list_response = db_client.get("/workout-logs", headers=auth_headers(token))
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    detail_response = db_client.get(f"/workout-logs/{created['id']}", headers=auth_headers(token))
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == created["id"]

    patch_response = db_client.patch(
        f"/workout-logs/{created['id']}",
        headers=auth_headers(token),
        json={
            "completion_status": "PARTIAL",
            "completed_sets": 2,
            "completed_reps_total": 18,
            "note": "Stopped early.",
        },
    )
    assert patch_response.status_code == 200
    patched = patch_response.json()
    assert patched["completion_status"] == "PARTIAL"
    assert patched["completed_sets"] == 2
    assert patched["completed_reps_total"] == 18
    assert patched["plan_id"] == plan["id"]
    assert patched["session_exercise_id"] == entry["id"]

    delete_response = db_client.delete(f"/workout-logs/{created['id']}", headers=auth_headers(token))
    assert delete_response.status_code == 204

    missing_response = db_client.get(f"/workout-logs/{created['id']}", headers=auth_headers(token))
    assert missing_response.status_code == 404


def test_workout_log_owner_scope_duplicate_and_validation_rules(db_client) -> None:
    owner_token = register_user(db_client)
    other_token = register_user(db_client, email="other@example.com")
    update_profile(db_client, owner_token)
    update_profile(db_client, other_token)
    seed_planner_exercises()
    owner_plan = generate_plan(db_client, owner_token)
    owner_session = owner_plan["sessions"][0]
    owner_entry = owner_session["exercises"][0]

    forbidden_create = _create_log(
        db_client,
        other_token,
        plan_id=owner_plan["id"],
        session_id=owner_session["id"],
        session_exercise_id=owner_entry["id"],
    )
    assert forbidden_create.status_code == 404

    skipped_invalid = _create_log(
        db_client,
        owner_token,
        plan_id=owner_plan["id"],
        session_id=owner_session["id"],
        session_exercise_id=owner_entry["id"],
        completion_status="SKIPPED",
        completed_sets=1,
        completed_reps_total=10,
    )
    assert skipped_invalid.status_code == 422

    invalid_effort = _create_log(
        db_client,
        owner_token,
        plan_id=owner_plan["id"],
        session_id=owner_session["id"],
        session_exercise_id=owner_entry["id"],
        effort_rating=11,
    )
    assert invalid_effort.status_code == 422

    create_response = _create_log(
        db_client,
        owner_token,
        plan_id=owner_plan["id"],
        session_id=owner_session["id"],
        session_exercise_id=owner_entry["id"],
    )
    assert create_response.status_code == 201
    log_id = create_response.json()["id"]

    duplicate_response = _create_log(
        db_client,
        owner_token,
        plan_id=owner_plan["id"],
        session_id=owner_session["id"],
        session_exercise_id=owner_entry["id"],
    )
    assert duplicate_response.status_code == 409

    assert db_client.get(f"/workout-logs/{log_id}", headers=auth_headers(other_token)).status_code == 404
    assert (
        db_client.patch(
            f"/workout-logs/{log_id}",
            headers=auth_headers(other_token),
            json={"completed_sets": 1},
        ).status_code
        == 404
    )
    assert db_client.delete(f"/workout-logs/{log_id}", headers=auth_headers(other_token)).status_code == 404


def test_workout_log_snapshot_remains_stable_after_plan_adjustment(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)
    target = find_session_exercise(plan, "main_push")
    session = next(session for session in plan["sessions"] if any(ex["id"] == target["id"] for ex in session["exercises"]))

    create_response = _create_log(
        db_client,
        token,
        plan_id=plan["id"],
        session_id=session["id"],
        session_exercise_id=target["id"],
    )
    assert create_response.status_code == 201
    original_name = create_response.json()["exercise_name_snapshot"]

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
    updated_plan = adjust_response.json()["updated_plan"]
    updated_target = find_session_exercise(updated_plan, "main_push")

    log_detail = db_client.get(
        f"/workout-logs/{create_response.json()['id']}",
        headers=auth_headers(token),
    )
    assert log_detail.status_code == 200
    assert log_detail.json()["exercise_name_snapshot"] == original_name
    assert log_detail.json()["exercise_name_snapshot"] != updated_target["exercise"]["name"]


def test_list_workout_logs_applies_limit_and_offset(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    plan = generate_plan(db_client, token)

    created_ids = []
    for session in plan["sessions"]:
        entry = session["exercises"][0]
        response = _create_log(
            db_client,
            token,
            plan_id=plan["id"],
            session_id=session["id"],
            session_exercise_id=entry["id"],
        )
        assert response.status_code == 201
        created_ids.append(response.json()["id"])

    list_response = db_client.get(
        "/workout-logs?limit=1&offset=1",
        headers=auth_headers(token),
    )

    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 3
    assert payload["limit"] == 1
    assert payload["offset"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] in created_ids
