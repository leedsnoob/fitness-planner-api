from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AdjustmentReason, Environment
from app.models.exercise import Exercise
from app.models.plan import AdjustmentRequest, PlanRevision, TrainingPlan, WorkoutSessionExercise
from app.models.user import User
from app.schemas.plan import CreateAdjustmentRequest
from app.services.planner import (
    DIFFICULTY_RANK,
    PlanGenerationError,
    get_slot_rule,
    load_candidate_scope,
    score_exercise,
)
from app.services.plan_views import build_plan_detail


class PlanAdjustmentError(Exception):
    pass


@dataclass(frozen=True)
class AdjustmentResult:
    revision_number: int
    old_exercise: Exercise
    new_exercise: Exercise
    score_breakdown: dict[str, float]
    explanation: str


def adjust_plan_exercise(
    db: Session,
    current_user: User,
    plan: TrainingPlan,
    payload: CreateAdjustmentRequest,
) -> AdjustmentResult:
    _validate_adjustment_payload(payload)

    target_entry = _get_locked_target_entry(db, plan.id, payload.session_exercise_id)
    slot_rule = get_slot_rule(target_entry.slot_type)
    current_exercise = target_entry.exercise
    current_session = target_entry.session
    before_snapshot = build_plan_detail(plan).model_dump(mode="json")

    effective_environment = payload.override_environment or plan.environment
    effective_profile = _build_effective_profile(
        profile=current_user.profile,
        payload=payload,
    )
    candidates = load_candidate_scope(db, current_user.id)
    replacement, replacement_score, score_breakdown = _select_replacement(
        candidates=candidates,
        plan=plan,
        current_exercise=current_exercise,
        target_entry=target_entry,
        slot_rule=slot_rule,
        environment=effective_environment,
        effective_profile=effective_profile,
        reason=payload.reason,
    )

    adjustment_request = AdjustmentRequest(
        plan_id=plan.id,
        session_id=current_session.id,
        session_exercise_id=target_entry.id,
        reason=payload.reason,
        detail_note=payload.detail_note or "",
        override_environment=payload.override_environment,
        temporary_unavailable_equipment=payload.temporary_unavailable_equipment,
        temporary_discomfort_tags=payload.temporary_discomfort_tags,
    )
    db.add(adjustment_request)
    db.flush()

    target_entry.exercise_id = replacement.id
    target_entry.exercise = replacement
    target_entry.selection_score = replacement_score
    target_entry.score_breakdown = score_breakdown
    target_entry.notes = _build_replacement_note(current_exercise.name, replacement.name, payload.reason)
    plan.current_revision_number += 1

    after_snapshot = build_plan_detail(plan).model_dump(mode="json")
    explanation = _build_explanation(current_exercise.name, replacement.name, payload.reason, score_breakdown)
    revision = PlanRevision(
        plan_id=plan.id,
        adjustment_request_id=adjustment_request.id,
        revision_number=plan.current_revision_number,
        old_exercise_id=current_exercise.id,
        new_exercise_id=replacement.id,
        score_breakdown=score_breakdown,
        explanation=explanation,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
    )
    db.add(revision)
    db.commit()
    db.refresh(plan)
    return AdjustmentResult(
        revision_number=revision.revision_number,
        old_exercise=current_exercise,
        new_exercise=replacement,
        score_breakdown=score_breakdown,
        explanation=explanation,
    )


def _validate_adjustment_payload(payload: CreateAdjustmentRequest) -> None:
    if payload.reason == AdjustmentReason.ENVIRONMENT_MISMATCH and payload.override_environment is None:
        raise PlanAdjustmentError("override_environment is required for ENVIRONMENT_MISMATCH.")
    if payload.reason == AdjustmentReason.EQUIPMENT_UNAVAILABLE and not payload.temporary_unavailable_equipment:
        raise PlanAdjustmentError(
            "temporary_unavailable_equipment is required for EQUIPMENT_UNAVAILABLE."
        )
    if payload.reason == AdjustmentReason.PAIN_OR_DISCOMFORT and not payload.temporary_discomfort_tags:
        raise PlanAdjustmentError("temporary_discomfort_tags is required for PAIN_OR_DISCOMFORT.")


def _get_locked_target_entry(db: Session, plan_id: int, session_exercise_id: int) -> WorkoutSessionExercise:
    entry = (
        db.execute(
            select(WorkoutSessionExercise)
            .join(WorkoutSessionExercise.session)
            .where(
                WorkoutSessionExercise.id == session_exercise_id,
                WorkoutSessionExercise.session.has(plan_id=plan_id),
            )
            .with_for_update()
        )
        .scalar_one_or_none()
    )
    if entry is None:
        raise PlanAdjustmentError("Session exercise not found for this plan.")
    return entry


def _build_effective_profile(*, profile, payload: CreateAdjustmentRequest):
    discomfort_tags = list(dict.fromkeys([*profile.discomfort_tags, *payload.temporary_discomfort_tags]))
    return SimpleNamespace(
        training_level=profile.training_level,
        available_equipment=list(profile.available_equipment),
        discomfort_tags=discomfort_tags,
        blocked_exercise_ids=list(profile.blocked_exercise_ids),
        temporary_unavailable_equipment=list(payload.temporary_unavailable_equipment),
    )


def _select_replacement(
    *,
    candidates: list[Exercise],
    plan: TrainingPlan,
    current_exercise: Exercise,
    target_entry: WorkoutSessionExercise,
    slot_rule,
    environment: Environment,
    effective_profile,
    reason: AdjustmentReason,
) -> tuple[Exercise, float, dict[str, float]]:
    used_exercise_ids = {
        entry.exercise_id
        for session in plan.sessions
        for entry in session.exercises
        if entry.id != target_entry.id
    }
    compatible = [
        exercise
        for exercise in candidates
        if _matches_replacement_constraints(
            exercise=exercise,
            current_exercise=current_exercise,
            slot_rule=slot_rule,
            environment=environment,
            effective_profile=effective_profile,
        )
    ]
    fresh_compatible = [exercise for exercise in compatible if exercise.id not in used_exercise_ids]
    pool = fresh_compatible or compatible
    if not pool:
        raise PlanAdjustmentError(f"No compatible replacement found for slot '{target_entry.slot_type}'.")

    ranked: list[tuple[float, int, Exercise, dict[str, float]]] = []
    for exercise in pool:
        base_score, base_breakdown = score_exercise(
            exercise=exercise,
            slot=slot_rule,
            environment=environment,
            profile=effective_profile,
        )
        reason_bonus = _replacement_reason_bonus(
            reason=reason,
            candidate=exercise,
            current_exercise=current_exercise,
        )
        total = base_score + reason_bonus
        breakdown = {
            **base_breakdown,
            "replacement_reason_bonus": reason_bonus,
            "total": total,
        }
        ranked.append((total, -exercise.id, exercise, breakdown))
    ranked.sort(reverse=True)
    best_total, _, best_exercise, best_breakdown = ranked[0]
    return best_exercise, best_total, best_breakdown


def _matches_replacement_constraints(
    *,
    exercise: Exercise,
    current_exercise: Exercise,
    slot_rule,
    environment: Environment,
    effective_profile,
) -> bool:
    if exercise.id == current_exercise.id:
        return False
    if exercise.id in set(effective_profile.blocked_exercise_ids):
        return False
    if exercise.movement_pattern not in slot_rule.allowed_patterns:
        return False
    if set(effective_profile.discomfort_tags).intersection(exercise.contraindication_tags):
        return False
    if not _matches_environment(exercise, environment):
        return False
    if not _matches_adjustment_equipment(exercise, environment, effective_profile):
        return False
    if not _matches_training_level(exercise, effective_profile.training_level):
        return False
    return True


def _matches_environment(exercise: Exercise, environment: Environment) -> bool:
    tags = set(exercise.environment_tags)
    if environment == Environment.HOME:
        return bool(tags.intersection({"both", "home"}))
    return bool(tags.intersection({"both", "gym"}))


def _matches_adjustment_equipment(exercise: Exercise, environment: Environment, effective_profile) -> bool:
    tags = set(exercise.equipment_tags)
    if not tags:
        return True

    always_available = {"bodyweight", "gym_mat"}
    if tags.issubset(always_available):
        return True

    unavailable = set(effective_profile.temporary_unavailable_equipment)
    if tags.intersection(unavailable):
        return False

    available_equipment = set(effective_profile.available_equipment).union(always_available)
    if environment == Environment.GYM and not effective_profile.available_equipment:
        return True
    if not effective_profile.available_equipment and unavailable:
        return True
    return tags.issubset(available_equipment)


def _matches_training_level(exercise: Exercise, training_level) -> bool:
    if training_level is None:
        return True
    allowed_rank = {
        "BEGINNER": 1,
        "INTERMEDIATE": 2,
        "ADVANCED": 3,
    }[training_level.value]
    return DIFFICULTY_RANK[exercise.difficulty] <= allowed_rank


def _replacement_reason_bonus(
    *,
    reason: AdjustmentReason,
    candidate: Exercise,
    current_exercise: Exercise,
) -> float:
    if reason == AdjustmentReason.DISLIKE:
        return 6.0
    if reason == AdjustmentReason.WANTS_VARIETY:
        bonus = 6.0
        if candidate.movement_pattern != current_exercise.movement_pattern:
            bonus += 4.0
        if set(candidate.equipment_tags) != set(current_exercise.equipment_tags):
            bonus += 2.0
        return bonus
    if reason == AdjustmentReason.TOO_DIFFICULT:
        candidate_rank = DIFFICULTY_RANK[candidate.difficulty]
        current_rank = DIFFICULTY_RANK[current_exercise.difficulty]
        if candidate_rank < current_rank:
            return 12.0
        if candidate_rank == current_rank:
            return 4.0
        return -4.0
    if reason == AdjustmentReason.PAIN_OR_DISCOMFORT:
        return 8.0 if candidate.impact_level == "low" else 2.0
    if reason == AdjustmentReason.EQUIPMENT_UNAVAILABLE:
        return 6.0 if set(candidate.equipment_tags).issubset({"bodyweight", "gym_mat"}) else 3.0
    if reason == AdjustmentReason.ENVIRONMENT_MISMATCH:
        return 5.0 if "both" in candidate.environment_tags else 3.0
    return 0.0


def _build_replacement_note(old_name: str, new_name: str, reason: AdjustmentReason) -> str:
    return f"Replaced {old_name} with {new_name} due to {reason.value.lower()}."


def _build_explanation(
    old_name: str,
    new_name: str,
    reason: AdjustmentReason,
    score_breakdown: dict[str, float],
) -> str:
    return (
        f"Replaced {old_name} with {new_name} for {reason.value.lower()}. "
        f"Pattern {score_breakdown['pattern_match']:.0f}, muscle {score_breakdown['muscle_match']:.0f}, "
        f"difficulty {score_breakdown['difficulty_fit']:.0f}, environment {score_breakdown['environment_fit']:.0f}, "
        f"equipment {score_breakdown['equipment_fit']:.0f}, reason bonus {score_breakdown['replacement_reason_bonus']:.0f}."
    )
