from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import WorkoutCompletionStatus
from app.models.plan import TrainingPlan, WorkoutLog, WorkoutSession, WorkoutSessionExercise
from app.schemas.log import CreateWorkoutLogRequest, UpdateWorkoutLogRequest, WorkoutLogResponse


class WorkoutLogError(Exception):
    pass


@dataclass(frozen=True)
class WorkoutLogFilters:
    plan_id: int | None = None
    session_id: int | None = None
    performed_from: date | None = None
    performed_to: date | None = None
    completion_status: WorkoutCompletionStatus | None = None
    limit: int = 20
    offset: int = 0


def build_workout_log_response(log: WorkoutLog) -> WorkoutLogResponse:
    return WorkoutLogResponse(
        id=log.id,
        plan_id=log.plan_id,
        session_id=log.session_id,
        session_exercise_id=log.session_exercise_id,
        exercise_id=log.exercise_id,
        exercise_name_snapshot=log.exercise_name_snapshot,
        slot_type_snapshot=log.slot_type_snapshot,
        movement_pattern_snapshot=log.movement_pattern_snapshot,
        planned_sets=log.planned_sets,
        planned_reps=log.planned_reps,
        planned_rest_seconds=log.planned_rest_seconds,
        completed_sets=log.completed_sets,
        completed_reps_total=log.completed_reps_total,
        completion_status=log.completion_status,
        effort_rating=log.effort_rating,
        note=log.note,
        performed_on=log.performed_on,
        created_at=log.created_at,
        updated_at=log.updated_at,
    )


def get_owned_workout_log(db: Session, user_id: int, log_id: int) -> WorkoutLog | None:
    return (
        db.execute(_workout_log_query().where(WorkoutLog.user_id == user_id, WorkoutLog.id == log_id))
        .scalar_one_or_none()
    )


def list_owned_workout_logs(db: Session, user_id: int, filters: WorkoutLogFilters) -> tuple[list[WorkoutLog], int]:
    statement = _workout_log_query().where(WorkoutLog.user_id == user_id)
    if filters.plan_id is not None:
        statement = statement.where(WorkoutLog.plan_id == filters.plan_id)
    if filters.session_id is not None:
        statement = statement.where(WorkoutLog.session_id == filters.session_id)
    if filters.performed_from is not None:
        statement = statement.where(WorkoutLog.performed_on >= filters.performed_from)
    if filters.performed_to is not None:
        statement = statement.where(WorkoutLog.performed_on <= filters.performed_to)
    if filters.completion_status is not None:
        statement = statement.where(WorkoutLog.completion_status == filters.completion_status)

    logs = db.execute(statement).scalars().all()
    total = len(logs)
    items = logs[filters.offset : filters.offset + filters.limit]
    return items, total


def create_workout_log(db: Session, user_id: int, payload: CreateWorkoutLogRequest) -> WorkoutLog:
    _validate_completion(
        completion_status=payload.completion_status,
        completed_sets=payload.completed_sets,
        completed_reps_total=payload.completed_reps_total,
        effort_rating=payload.effort_rating,
    )
    session_exercise = _get_owned_session_exercise(
        db=db,
        user_id=user_id,
        plan_id=payload.plan_id,
        session_id=payload.session_id,
        session_exercise_id=payload.session_exercise_id,
    )
    existing_log = (
        db.execute(
            select(WorkoutLog).where(
                WorkoutLog.user_id == user_id,
                WorkoutLog.session_exercise_id == payload.session_exercise_id,
            )
        )
        .scalar_one_or_none()
    )
    if existing_log is not None:
        raise WorkoutLogError("Workout log already exists for this planned exercise.")

    log = WorkoutLog(
        user_id=user_id,
        plan_id=payload.plan_id,
        session_id=payload.session_id,
        session_exercise_id=payload.session_exercise_id,
        exercise_id=session_exercise.exercise_id,
        exercise_name_snapshot=session_exercise.exercise.name,
        slot_type_snapshot=session_exercise.slot_type,
        movement_pattern_snapshot=session_exercise.exercise.movement_pattern,
        planned_sets=session_exercise.sets,
        planned_reps=session_exercise.reps,
        planned_rest_seconds=session_exercise.rest_seconds,
        completed_sets=payload.completed_sets,
        completed_reps_total=payload.completed_reps_total,
        completion_status=payload.completion_status,
        effort_rating=payload.effort_rating,
        note=payload.note or "",
        performed_on=payload.performed_on,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_workout_log(db: Session, log: WorkoutLog, payload: UpdateWorkoutLogRequest) -> WorkoutLog:
    next_completion_status = payload.completion_status or log.completion_status
    next_completed_sets = payload.completed_sets if payload.completed_sets is not None else log.completed_sets
    next_completed_reps_total = (
        payload.completed_reps_total if payload.completed_reps_total is not None else log.completed_reps_total
    )
    next_effort_rating = payload.effort_rating if payload.effort_rating is not None else log.effort_rating
    _validate_completion(
        completion_status=next_completion_status,
        completed_sets=next_completed_sets,
        completed_reps_total=next_completed_reps_total,
        effort_rating=next_effort_rating,
    )

    log.completion_status = next_completion_status
    log.completed_sets = next_completed_sets
    log.completed_reps_total = next_completed_reps_total
    log.effort_rating = next_effort_rating
    if payload.note is not None:
        log.note = payload.note
    if payload.performed_on is not None:
        log.performed_on = payload.performed_on

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _workout_log_query():
    return select(WorkoutLog).order_by(WorkoutLog.performed_on.desc(), WorkoutLog.id.desc())


def _get_owned_session_exercise(
    *,
    db: Session,
    user_id: int,
    plan_id: int,
    session_id: int,
    session_exercise_id: int,
) -> WorkoutSessionExercise:
    entry = (
        db.execute(
            select(WorkoutSessionExercise)
            .join(WorkoutSessionExercise.session)
            .join(WorkoutSession.plan)
            .options(selectinload(WorkoutSessionExercise.exercise))
            .where(
                TrainingPlan.user_id == user_id,
                TrainingPlan.id == plan_id,
                WorkoutSession.id == session_id,
                WorkoutSessionExercise.id == session_exercise_id,
            )
        )
        .scalar_one_or_none()
    )
    if entry is None:
        raise WorkoutLogError("Session exercise not found for this user and plan.")
    return entry


def _validate_completion(
    *,
    completion_status: WorkoutCompletionStatus,
    completed_sets: int,
    completed_reps_total: int,
    effort_rating: int | None,
) -> None:
    if completed_sets < 0 or completed_reps_total < 0:
        raise WorkoutLogError("Completed values must be non-negative.")
    if effort_rating is not None and not 1 <= effort_rating <= 10:
        raise WorkoutLogError("effort_rating must be between 1 and 10.")
    if completion_status == WorkoutCompletionStatus.SKIPPED and (
        completed_sets != 0 or completed_reps_total != 0
    ):
        raise WorkoutLogError("SKIPPED logs must have zero completed sets and reps.")
