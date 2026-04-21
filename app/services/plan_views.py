from __future__ import annotations

from app.models.plan import PlanExplanation, PlanRevision, TrainingPlan, WorkoutSession, WorkoutSessionExercise
from app.schemas.exercise import ExerciseResponse
from app.schemas.plan import (
    PlanExplanationResponse,
    PlanRevisionDetailResponse,
    PlanRevisionSummaryResponse,
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


def build_revision_summary(revision: PlanRevision) -> PlanRevisionSummaryResponse:
    return PlanRevisionSummaryResponse(
        revision_number=revision.revision_number,
        reason=revision.adjustment_request.reason,
        detail_note=revision.adjustment_request.detail_note,
        old_exercise=ExerciseResponse.model_validate(revision.old_exercise),
        new_exercise=ExerciseResponse.model_validate(revision.new_exercise),
        created_at=revision.created_at,
    )


def build_revision_detail(revision: PlanRevision) -> PlanRevisionDetailResponse:
    summary = build_revision_summary(revision)
    return PlanRevisionDetailResponse(
        **summary.model_dump(),
        score_breakdown=revision.score_breakdown,
        explanation=revision.explanation,
        before_snapshot=revision.before_snapshot,
        after_snapshot=revision.after_snapshot,
    )


def build_plan_explanation_response(explanation: PlanExplanation) -> PlanExplanationResponse:
    return PlanExplanationResponse(
        id=explanation.id,
        explanation_scope=explanation.explanation_scope,
        plan_id=explanation.plan_id,
        revision_id=explanation.revision_id,
        revision_number=explanation.revision.revision_number if explanation.revision is not None else None,
        provider=explanation.provider,
        model_name=explanation.model_name,
        input_snapshot=explanation.input_snapshot,
        output_text=explanation.output_text,
        created_at=explanation.created_at,
    )
