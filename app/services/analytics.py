from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import WorkoutCompletionStatus
from app.models.plan import PlanRevision, TrainingPlan, WorkoutLog, WorkoutSession, WorkoutSessionExercise
from app.schemas.log import (
    AdherenceAnalyticsResponse,
    ReplacementAnalyticsItem,
    ReplacementAnalyticsResponse,
    VolumeAnalyticsResponse,
    VolumeDailyPoint,
)


def build_volume_analytics(db: Session, user_id: int, *, days: int) -> VolumeAnalyticsResponse:
    start_date = date.today() - timedelta(days=days - 1)
    logs = (
        db.execute(
            select(WorkoutLog)
            .where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.performed_on >= start_date,
            )
            .order_by(WorkoutLog.performed_on.asc(), WorkoutLog.id.asc())
        )
        .scalars()
        .all()
    )

    daily = defaultdict(lambda: {"completed_sets": 0, "completed_reps": 0, "logged_exercises": 0})
    total_completed_sets = 0
    total_completed_reps = 0
    session_ids: set[int] = set()

    for log in logs:
        session_ids.add(log.session_id)
        total_completed_sets += log.completed_sets
        total_completed_reps += log.completed_reps_total
        point = daily[log.performed_on]
        point["completed_sets"] += log.completed_sets
        point["completed_reps"] += log.completed_reps_total
        point["logged_exercises"] += 1

    return VolumeAnalyticsResponse(
        total_logged_sessions=len(session_ids),
        total_completed_sets=total_completed_sets,
        total_completed_reps=total_completed_reps,
        daily_points=[
            VolumeDailyPoint(
                date=logged_date,
                completed_sets=values["completed_sets"],
                completed_reps=values["completed_reps"],
                logged_exercises=values["logged_exercises"],
            )
            for logged_date, values in sorted(daily.items())
        ],
    )


def build_adherence_analytics(db: Session, user_id: int, *, plan_id: int | None = None) -> AdherenceAnalyticsResponse:
    planned_statement = (
        select(WorkoutSessionExercise.id)
        .join(WorkoutSessionExercise.session)
        .join(WorkoutSession.plan)
        .where(TrainingPlan.user_id == user_id)
    )
    log_statement = select(WorkoutLog).where(WorkoutLog.user_id == user_id)
    if plan_id is not None:
        planned_statement = planned_statement.where(TrainingPlan.id == plan_id)
        log_statement = log_statement.where(WorkoutLog.plan_id == plan_id)

    planned_exercise_ids = db.execute(planned_statement).scalars().all()
    logs = db.execute(log_statement).scalars().all()

    completed_exercises = sum(log.completion_status == WorkoutCompletionStatus.COMPLETED for log in logs)
    partial_exercises = sum(log.completion_status == WorkoutCompletionStatus.PARTIAL for log in logs)
    skipped_exercises = sum(log.completion_status == WorkoutCompletionStatus.SKIPPED for log in logs)
    planned_exercises = len(planned_exercise_ids)
    logged_exercises = len(logs)
    adherence_rate = completed_exercises / planned_exercises if planned_exercises else 0.0

    return AdherenceAnalyticsResponse(
        planned_exercises=planned_exercises,
        logged_exercises=logged_exercises,
        completed_exercises=completed_exercises,
        partial_exercises=partial_exercises,
        skipped_exercises=skipped_exercises,
        adherence_rate=adherence_rate,
    )


def build_replacement_analytics(
    db: Session,
    user_id: int,
    *,
    plan_id: int | None = None,
) -> ReplacementAnalyticsResponse:
    statement = (
        select(PlanRevision)
        .join(TrainingPlan, PlanRevision.plan_id == TrainingPlan.id)
        .where(TrainingPlan.user_id == user_id)
        .options(
            selectinload(PlanRevision.adjustment_request),
            selectinload(PlanRevision.old_exercise),
            selectinload(PlanRevision.new_exercise),
        )
        .order_by(PlanRevision.created_at.desc())
    )
    if plan_id is not None:
        statement = statement.where(TrainingPlan.id == plan_id)

    revisions = db.execute(statement).scalars().all()
    by_reason = Counter(revision.adjustment_request.reason.value for revision in revisions)
    latest_revisions = [
        ReplacementAnalyticsItem(
            revision_number=revision.revision_number,
            reason=revision.adjustment_request.reason,
            old_exercise_name=revision.old_exercise.name,
            new_exercise_name=revision.new_exercise.name,
            created_at=revision.created_at,
        )
        for revision in revisions[:5]
    ]
    return ReplacementAnalyticsResponse(
        total_revisions=len(revisions),
        by_reason=dict(by_reason),
        latest_revisions=latest_revisions,
    )
