from __future__ import annotations

from app.services.plan_explanations import build_explanation_messages


def test_build_explanation_messages_includes_project_context_for_plan_scope() -> None:
    messages = build_explanation_messages(
        {
            "scope": "PLAN",
            "plan": {
                "id": 1,
                "goal": "MUSCLE_GAIN",
                "split": "full_body",
                "request_snapshot": {
                    "profile_constraints": {
                        "available_equipment": ["dumbbell"],
                        "discomfort_tags": ["shoulder_discomfort"],
                    }
                },
            },
        }
    )

    assert messages[0]["role"] == "system"
    assert "constraint-aware fitness planning API" in messages[0]["content"]
    assert "Use only the provided data" in messages[0]["content"]
    assert "say it is not shown instead of inferring it" in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Explain a full weekly training plan" in messages[1]["content"]
    assert '"scope": "PLAN"' in messages[1]["content"]
