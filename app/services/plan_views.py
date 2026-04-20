from __future__ import annotations

from app.models.plan import TrainingPlan, WorkoutSession, WorkoutSessionExercise
from app.schemas.exercise import ExerciseResponse
from app.schemas.plan import (
    TrainingPlanDetailResponse,
    TrainingPlanSummaryResponse,
    WorkoutSessionExerciseResponse,
    WorkoutSessionResponse,
)


def build_session_exercise_response(entry: WorkoutSessionExercise) -> WorkoutSessionExerciseResponse:
    return WorkoutSessionExerciseResponse(
        id=entry.id,
        exercise=ExerciseResponse.model_validate(entry.exercise),
        slot_type=entry.slot_type,
        selection_score=entry.selection_score,
        score_breakdown=entry.score_breakdown,
        sets=entry.sets,
        reps=entry.reps,
        rest_seconds=entry.rest_seconds,
        notes=entry.notes,
    )


def build_session_response(session: WorkoutSession) -> WorkoutSessionResponse:
    return WorkoutSessionResponse(
        id=session.id,
        day_index=session.day_index,
        session_name=session.session_name,
        focus_summary=session.focus_summary,
        exercises=[build_session_exercise_response(entry) for entry in session.exercises],
    )


def build_plan_summary(plan: TrainingPlan) -> TrainingPlanSummaryResponse:
    return TrainingPlanSummaryResponse(
        id=plan.id,
        goal=plan.goal,
        split=plan.split,
        training_days_per_week=plan.training_days_per_week,
        environment=plan.environment,
        generation_mode=plan.generation_mode,
        status=plan.status,
        current_revision_number=plan.current_revision_number,
        session_count=len(plan.sessions),
        created_at=plan.created_at,
    )


def build_plan_detail(plan: TrainingPlan) -> TrainingPlanDetailResponse:
    summary = build_plan_summary(plan)
    return TrainingPlanDetailResponse(
        **summary.model_dump(),
        request_snapshot=plan.request_snapshot,
        sessions=[build_session_response(session) for session in plan.sessions],
    )
