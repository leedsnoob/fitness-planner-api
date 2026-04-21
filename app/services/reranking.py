from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import AdjustmentReason, Environment, WorkoutCompletionStatus
from app.models.exercise import Exercise
from app.models.plan import PlanRevision, WorkoutLog, TrainingPlan


@dataclass(frozen=True)
class RerankingRequestContext:
    override_environment: Environment | None = None
    temporary_unavailable_equipment: tuple[str, ...] = ()
    temporary_discomfort_tags: tuple[str, ...] = ()


@dataclass
class UserHistoryContext:
    completed_exercise_counts: Counter[int] = field(default_factory=Counter)
    noncompleted_exercise_counts: Counter[int] = field(default_factory=Counter)
    high_effort_exercise_counts: Counter[int] = field(default_factory=Counter)
    disliked_exercise_ids: set[int] = field(default_factory=set)
    painful_exercise_ids: set[int] = field(default_factory=set)
    difficult_exercise_ids: set[int] = field(default_factory=set)
    recent_exercise_ids: tuple[int, ...] = ()


def build_user_history_context(db: Session, user_id: int) -> UserHistoryContext:
    logs = (
        db.execute(
            select(WorkoutLog)
            .where(WorkoutLog.user_id == user_id)
            .order_by(WorkoutLog.performed_on.desc(), WorkoutLog.id.desc())
        )
        .scalars()
        .all()
    )
    revisions = (
        db.execute(
            select(PlanRevision)
            .join(TrainingPlan, PlanRevision.plan_id == TrainingPlan.id)
            .where(TrainingPlan.user_id == user_id)
            .options(selectinload(PlanRevision.adjustment_request))
            .order_by(PlanRevision.created_at.desc())
        )
        .scalars()
        .all()
    )

    context = UserHistoryContext()
    recent_exercise_ids: list[int] = []

    for log in logs:
        if log.exercise_id is not None and len(recent_exercise_ids) < 10:
            recent_exercise_ids.append(log.exercise_id)
        if log.exercise_id is None:
            continue
        if log.completion_status == WorkoutCompletionStatus.COMPLETED:
            context.completed_exercise_counts[log.exercise_id] += 1
        else:
            context.noncompleted_exercise_counts[log.exercise_id] += 1
        if log.effort_rating is not None and log.effort_rating >= 8:
            context.high_effort_exercise_counts[log.exercise_id] += 1

    for revision in revisions:
        reason = revision.adjustment_request.reason
        if reason == AdjustmentReason.DISLIKE:
            context.disliked_exercise_ids.add(revision.old_exercise_id)
        elif reason == AdjustmentReason.PAIN_OR_DISCOMFORT:
            context.painful_exercise_ids.add(revision.old_exercise_id)
        elif reason == AdjustmentReason.TOO_DIFFICULT:
            context.difficult_exercise_ids.add(revision.old_exercise_id)

    context.recent_exercise_ids = tuple(recent_exercise_ids)
    return context


def compute_context_breakdown(
    exercise: Exercise,
    *,
    history: UserHistoryContext,
    request_context: RerankingRequestContext | None = None,
) -> tuple[float, dict[str, float]]:
    history_adherence_bonus = min(6.0, float(history.completed_exercise_counts[exercise.id] * 3))
    history_effort_penalty = -min(
        8.0,
        float(
            (history.noncompleted_exercise_counts[exercise.id] * 4)
            + (history.high_effort_exercise_counts[exercise.id] * 2)
        ),
    )

    revision_reason_penalty = 0.0
    if exercise.id in history.disliked_exercise_ids:
        revision_reason_penalty -= 8.0
    if exercise.id in history.painful_exercise_ids:
        revision_reason_penalty -= 10.0
    if exercise.id in history.difficult_exercise_ids:
        revision_reason_penalty -= 6.0

    novelty_bonus = 0.0 if exercise.id in history.recent_exercise_ids else 4.0

    context_override_bonus = 0.0
    if request_context is not None:
        tags = set(exercise.environment_tags)
        equipment_tags = set(exercise.equipment_tags)
        if request_context.override_environment is not None:
            if request_context.override_environment == Environment.HOME and "home" in tags:
                context_override_bonus += 2.0
            elif request_context.override_environment == Environment.GYM and "gym" in tags:
                context_override_bonus += 2.0
            elif "both" in tags:
                context_override_bonus += 1.0
        if request_context.temporary_unavailable_equipment and equipment_tags.issubset({"bodyweight", "gym_mat"}):
            context_override_bonus += 2.0
        if request_context.temporary_discomfort_tags and exercise.impact_level == "low":
            context_override_bonus += 2.0

    total = (
        history_adherence_bonus
        + history_effort_penalty
        + revision_reason_penalty
        + novelty_bonus
        + context_override_bonus
    )
    return total, {
        "history_adherence_bonus": history_adherence_bonus,
        "history_effort_penalty": history_effort_penalty,
        "revision_reason_penalty": revision_reason_penalty,
        "novelty_bonus": novelty_bonus,
        "context_override_bonus": context_override_bonus,
    }
