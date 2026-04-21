from __future__ import annotations

from app.data.exercise_import import import_exercises
from tests.helpers import (
    auth_headers,
    find_session_exercise,
    generate_plan,
    register_user,
    seed_planner_exercises,
    update_profile,
)


def _seed_equal_push_alternatives() -> None:
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


def test_history_penalty_pushes_generation_away_from_skipped_exercise(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    _seed_equal_push_alternatives()

    first_plan = generate_plan(db_client, token)
    first_main_push = find_session_exercise(first_plan, "main_push")
    assert first_main_push["exercise"]["name"] == "Dumbbell Floor Press"

    create_log = db_client.post(
        "/workout-logs",
        headers=auth_headers(token),
        json={
            "plan_id": first_plan["id"],
            "session_id": first_plan["sessions"][0]["id"],
            "session_exercise_id": first_main_push["id"],
            "completion_status": "SKIPPED",
            "completed_sets": 0,
            "completed_reps_total": 0,
            "performed_on": "2026-04-21",
        },
    )
    assert create_log.status_code == 201

    second_plan = generate_plan(db_client, token)
    second_main_push = find_session_exercise(second_plan, "main_push")
    assert second_main_push["exercise"]["name"] != "Dumbbell Floor Press"
    assert second_main_push["score_breakdown"]["history_effort_penalty"] == 0.0
    assert second_main_push["score_breakdown"]["novelty_bonus"] > 0.0


def test_revision_reason_penalty_avoids_previously_disliked_exercise(db_client) -> None:
    token = register_user(db_client)
    update_profile(db_client, token)
    seed_planner_exercises()
    _seed_equal_push_alternatives()

    first_plan = generate_plan(db_client, token)
    first_main_push = find_session_exercise(first_plan, "main_push")
    assert first_main_push["exercise"]["name"] == "Dumbbell Floor Press"

    adjustment = db_client.post(
        f"/plans/{first_plan['id']}/adjustments",
        headers=auth_headers(token),
        json={
            "session_exercise_id": first_main_push["id"],
            "reason": "DISLIKE",
        },
    )
    assert adjustment.status_code == 200
    assert adjustment.json()["new_exercise"]["name"] != "Dumbbell Floor Press"

    second_plan = generate_plan(db_client, token)
    second_main_push = find_session_exercise(second_plan, "main_push")
    assert second_main_push["exercise"]["name"] != "Dumbbell Floor Press"
    assert second_main_push["score_breakdown"]["revision_reason_penalty"] == 0.0
