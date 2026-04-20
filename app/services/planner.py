from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.enums import DifficultyLevel, Environment, Goal, PlanSplit, TrainingLevel
from app.models.exercise import Exercise
from app.models.plan import TrainingPlan, WorkoutSession, WorkoutSessionExercise
from app.models.user import User
from app.schemas.plan import GeneratePlanRequest


class PlanGenerationError(Exception):
    pass


@dataclass(frozen=True)
class SlotTemplate:
    slot_type: str
    allowed_patterns: tuple[str, ...]
    preferred_patterns: tuple[str, ...]
    focus_muscles: tuple[str, ...]
    prescription_type: str


@dataclass(frozen=True)
class SessionTemplate:
    session_name: str
    focus_summary: str
    slots: tuple[SlotTemplate, ...]


TEMPLATES: dict[PlanSplit, tuple[SessionTemplate, ...]] = {
    PlanSplit.FULL_BODY: (
        SessionTemplate(
            session_name="Full Body A",
            focus_summary="Push, squat, pull, hinge, core",
            slots=(
                SlotTemplate("main_push", ("horizontal_push", "vertical_push"), ("horizontal_push",), ("chest", "triceps", "shoulders"), "main"),
                SlotTemplate("lower_main", ("squat", "lunge"), ("squat",), ("quads", "glutes", "hamstrings"), "main"),
                SlotTemplate("main_pull", ("horizontal_pull", "vertical_pull"), ("horizontal_pull",), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("hinge_support", ("hinge", "lunge", "squat"), ("hinge",), ("glutes", "hamstrings", "lower_back"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Full Body B",
            focus_summary="Vertical push, hinge, pull, lunge, core",
            slots=(
                SlotTemplate("main_push", ("vertical_push", "horizontal_push"), ("vertical_push",), ("shoulders", "triceps", "chest"), "main"),
                SlotTemplate("lower_main", ("hinge", "squat", "lunge"), ("hinge",), ("glutes", "hamstrings", "lower_back"), "main"),
                SlotTemplate("main_pull", ("vertical_pull", "horizontal_pull"), ("vertical_pull",), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("lower_support", ("lunge", "squat"), ("lunge",), ("quads", "glutes", "hamstrings"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Full Body C",
            focus_summary="Push, lower body, pull, unilateral leg, core",
            slots=(
                SlotTemplate("main_push", ("horizontal_push", "vertical_push"), ("horizontal_push",), ("chest", "shoulders", "triceps"), "main"),
                SlotTemplate("lower_main", ("squat", "hinge", "lunge"), ("squat", "hinge"), ("quads", "glutes", "hamstrings"), "main"),
                SlotTemplate("main_pull", ("horizontal_pull", "vertical_pull"), ("horizontal_pull", "vertical_pull"), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("lower_support", ("lunge", "hinge", "squat"), ("lunge",), ("glutes", "quads", "hamstrings"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
    ),
    PlanSplit.PUSH_PULL_LEGS: (
        SessionTemplate(
            session_name="Push Day",
            focus_summary="Chest, shoulders and triceps",
            slots=(
                SlotTemplate("main_push", ("horizontal_push", "vertical_push"), ("horizontal_push",), ("chest", "triceps", "shoulders"), "main"),
                SlotTemplate("secondary_push", ("vertical_push", "horizontal_push"), ("vertical_push",), ("shoulders", "triceps", "chest"), "secondary"),
                SlotTemplate("push_accessory", ("horizontal_push", "vertical_push"), ("horizontal_push", "vertical_push"), ("chest", "triceps", "shoulders"), "accessory"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Pull Day",
            focus_summary="Back and biceps",
            slots=(
                SlotTemplate("main_pull", ("horizontal_pull", "vertical_pull"), ("horizontal_pull",), ("lats", "biceps", "trapezius"), "main"),
                SlotTemplate("secondary_pull", ("vertical_pull", "horizontal_pull"), ("vertical_pull",), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("hinge_accessory", ("hinge",), ("hinge",), ("glutes", "hamstrings", "lower_back"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Leg Day",
            focus_summary="Quads, glutes and hamstrings",
            slots=(
                SlotTemplate("main_squat", ("squat", "lunge"), ("squat",), ("quads", "glutes", "hamstrings"), "main"),
                SlotTemplate("main_hinge", ("hinge", "lunge"), ("hinge",), ("glutes", "hamstrings", "lower_back"), "secondary"),
                SlotTemplate("leg_accessory", ("lunge", "squat"), ("lunge",), ("glutes", "quads", "hamstrings"), "accessory"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
    ),
    PlanSplit.UPPER_LOWER: (
        SessionTemplate(
            session_name="Upper A",
            focus_summary="Horizontal push and pull emphasis",
            slots=(
                SlotTemplate("main_push", ("horizontal_push", "vertical_push"), ("horizontal_push",), ("chest", "triceps", "shoulders"), "main"),
                SlotTemplate("main_pull", ("horizontal_pull", "vertical_pull"), ("horizontal_pull",), ("lats", "biceps", "trapezius"), "main"),
                SlotTemplate("secondary_push", ("vertical_push", "horizontal_push"), ("vertical_push",), ("shoulders", "triceps", "chest"), "secondary"),
                SlotTemplate("secondary_pull", ("vertical_pull", "horizontal_pull"), ("vertical_pull",), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Lower A",
            focus_summary="Squat and hinge emphasis",
            slots=(
                SlotTemplate("main_squat", ("squat", "lunge"), ("squat",), ("quads", "glutes", "hamstrings"), "main"),
                SlotTemplate("main_hinge", ("hinge", "lunge"), ("hinge",), ("glutes", "hamstrings", "lower_back"), "main"),
                SlotTemplate("leg_accessory", ("lunge", "squat"), ("lunge",), ("glutes", "quads", "hamstrings"), "accessory"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Upper B",
            focus_summary="Vertical push and pull emphasis",
            slots=(
                SlotTemplate("main_push", ("vertical_push", "horizontal_push"), ("vertical_push",), ("shoulders", "triceps", "chest"), "main"),
                SlotTemplate("main_pull", ("vertical_pull", "horizontal_pull"), ("vertical_pull",), ("lats", "biceps", "trapezius"), "main"),
                SlotTemplate("secondary_push", ("horizontal_push", "vertical_push"), ("horizontal_push",), ("chest", "triceps", "shoulders"), "secondary"),
                SlotTemplate("secondary_pull", ("horizontal_pull", "vertical_pull"), ("horizontal_pull",), ("lats", "biceps", "trapezius"), "secondary"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
        SessionTemplate(
            session_name="Lower B",
            focus_summary="Unilateral leg work and posterior chain",
            slots=(
                SlotTemplate("main_lunge", ("lunge", "squat"), ("lunge",), ("glutes", "quads", "hamstrings"), "main"),
                SlotTemplate("main_hinge", ("hinge", "squat"), ("hinge",), ("glutes", "hamstrings", "lower_back"), "main"),
                SlotTemplate("leg_accessory", ("squat", "lunge"), ("squat",), ("quads", "glutes", "hamstrings"), "accessory"),
                SlotTemplate("core_finish", ("core",), ("core",), ("core", "abs", "obliques"), "core"),
            ),
        ),
    ),
}

GOAL_PRESCRIPTIONS = {
    Goal.MUSCLE_GAIN: {
        "main": {"sets": 4, "reps": "8-12", "rest_seconds": 90},
        "secondary": {"sets": 3, "reps": "10-12", "rest_seconds": 75},
        "accessory": {"sets": 3, "reps": "12-15", "rest_seconds": 60},
        "core": {"sets": 3, "reps": "12-15", "rest_seconds": 45},
    },
    Goal.STRENGTH: {
        "main": {"sets": 5, "reps": "4-6", "rest_seconds": 120},
        "secondary": {"sets": 4, "reps": "6-8", "rest_seconds": 90},
        "accessory": {"sets": 3, "reps": "8-10", "rest_seconds": 75},
        "core": {"sets": 3, "reps": "10-12", "rest_seconds": 45},
    },
    Goal.GENERAL_FITNESS: {
        "main": {"sets": 3, "reps": "10-12", "rest_seconds": 75},
        "secondary": {"sets": 3, "reps": "12-15", "rest_seconds": 60},
        "accessory": {"sets": 2, "reps": "12-15", "rest_seconds": 45},
        "core": {"sets": 2, "reps": "30-45s", "rest_seconds": 30},
    },
}

TRAINING_LEVEL_CAP = {
    TrainingLevel.BEGINNER: 1,
    TrainingLevel.INTERMEDIATE: 2,
    TrainingLevel.ADVANCED: 3,
}

DIFFICULTY_RANK = {
    DifficultyLevel.BEGINNER.value: 1,
    DifficultyLevel.INTERMEDIATE.value: 2,
    DifficultyLevel.ADVANCED.value: 3,
}


def generate_plan(db: Session, current_user: User, request: GeneratePlanRequest) -> TrainingPlan:
    _validate_split(request.split, request.training_days_per_week)
    profile = current_user.profile
    constraints = {
        "training_level": profile.training_level.value if profile.training_level else None,
        "available_equipment": profile.available_equipment,
        "discomfort_tags": profile.discomfort_tags,
        "blocked_exercise_ids": profile.blocked_exercise_ids,
    }
    candidates = _load_candidate_scope(db, current_user.id)
    plan = TrainingPlan(
        user_id=current_user.id,
        goal=request.goal,
        split=request.split,
        training_days_per_week=request.training_days_per_week,
        environment=request.environment,
        generation_mode="rule_based_v1",
        request_snapshot={
            "request": request.model_dump(mode="json"),
            "profile_constraints": constraints,
        },
        status="active",
    )

    used_exercise_ids: set[int] = set()
    for day_index, session_template in enumerate(TEMPLATES[request.split], start=1):
        session = WorkoutSession(
            day_index=day_index,
            session_name=session_template.session_name,
            focus_summary=session_template.focus_summary,
        )
        for slot in session_template.slots:
            exercise, score, breakdown = _select_exercise(
                candidates=candidates,
                slot=slot,
                environment=request.environment,
                profile=profile,
                used_exercise_ids=used_exercise_ids,
            )
            prescription = GOAL_PRESCRIPTIONS[request.goal][slot.prescription_type]
            session.exercises.append(
                WorkoutSessionExercise(
                    exercise_id=exercise.id,
                    slot_type=slot.slot_type,
                    selection_score=score,
                    score_breakdown=breakdown,
                    sets=prescription["sets"],
                    reps=prescription["reps"],
                    rest_seconds=prescription["rest_seconds"],
                    notes=f"Selected by rule-based planner for {slot.slot_type}.",
                )
            )
            used_exercise_ids.add(exercise.id)
        plan.sessions.append(session)

    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def _validate_split(split: PlanSplit, training_days_per_week: int) -> None:
    valid_days = {
        PlanSplit.FULL_BODY: 3,
        PlanSplit.PUSH_PULL_LEGS: 3,
        PlanSplit.UPPER_LOWER: 4,
    }
    expected_days = valid_days[split]
    if expected_days != training_days_per_week:
        raise PlanGenerationError(
            f"Split '{split.value}' is only supported for {expected_days}-day plans."
        )


def _load_candidate_scope(db: Session, user_id: int) -> list[Exercise]:
    statement = (
        select(Exercise)
        .where(or_(Exercise.owner_user_id.is_(None), Exercise.owner_user_id == user_id))
        .order_by(Exercise.id)
    )
    return list(db.execute(statement).scalars().all())


def _select_exercise(
    *,
    candidates: list[Exercise],
    slot: SlotTemplate,
    environment: Environment,
    profile,
    used_exercise_ids: set[int],
) -> tuple[Exercise, float, dict[str, float]]:
    filtered = [
        exercise
        for exercise in candidates
        if _matches_slot_constraints(
            exercise=exercise,
            slot=slot,
            environment=environment,
            profile=profile,
        )
        and exercise.id not in used_exercise_ids
    ]
    if not filtered:
        filtered = [
            exercise
            for exercise in candidates
            if _matches_slot_constraints(
                exercise=exercise,
                slot=slot,
                environment=environment,
                profile=profile,
            )
        ]
    if not filtered:
        raise PlanGenerationError(f"No compatible exercise found for slot '{slot.slot_type}'.")

    ranked: list[tuple[float, int, Exercise, dict[str, float]]] = []
    for exercise in filtered:
        score, breakdown = _score_exercise(exercise, slot, environment, profile)
        ranked.append((score, -exercise.id, exercise, breakdown))
    ranked.sort(reverse=True)
    best_score, _, best_exercise, best_breakdown = ranked[0]
    return best_exercise, best_score, best_breakdown


def _matches_slot_constraints(*, exercise: Exercise, slot: SlotTemplate, environment: Environment, profile) -> bool:
    if exercise.movement_pattern not in slot.allowed_patterns:
        return False
    if exercise.id in set(profile.blocked_exercise_ids):
        return False
    if set(profile.discomfort_tags).intersection(exercise.contraindication_tags):
        return False
    if not _matches_environment(exercise, environment):
        return False
    if not _matches_equipment(exercise, environment, profile.available_equipment):
        return False
    if not _matches_training_level(exercise, profile.training_level):
        return False
    return True


def _matches_environment(exercise: Exercise, environment: Environment) -> bool:
    tags = set(exercise.environment_tags)
    if environment == Environment.HOME:
        return bool(tags.intersection({"both", "home"}))
    return bool(tags.intersection({"both", "gym"}))


def _matches_equipment(exercise: Exercise, environment: Environment, available_equipment: list[str]) -> bool:
    tags = set(exercise.equipment_tags)
    if not tags:
        return True

    always_available = {"bodyweight", "gym_mat"}
    if tags.issubset(always_available):
        return True

    allowed_equipment = set(available_equipment).union(always_available)
    if environment == Environment.GYM and not available_equipment:
        return True
    return tags.issubset(allowed_equipment)


def _matches_training_level(exercise: Exercise, training_level: TrainingLevel | None) -> bool:
    if training_level is None:
        return True
    allowed_rank = TRAINING_LEVEL_CAP[training_level]
    return DIFFICULTY_RANK[exercise.difficulty] <= allowed_rank


def _score_exercise(
    exercise: Exercise,
    slot: SlotTemplate,
    environment: Environment,
    profile,
) -> tuple[float, dict[str, float]]:
    primary_overlap = len(set(exercise.primary_muscles).intersection(slot.focus_muscles))
    secondary_overlap = len(set(exercise.secondary_muscles).intersection(slot.focus_muscles))
    preferred_index = (
        slot.preferred_patterns.index(exercise.movement_pattern)
        if exercise.movement_pattern in slot.preferred_patterns
        else len(slot.preferred_patterns)
    )
    pattern_match = max(12.0, 30.0 - (preferred_index * 6.0))
    muscle_match = float((primary_overlap * 10) + (secondary_overlap * 5))

    target_rank = TRAINING_LEVEL_CAP.get(profile.training_level, 2) if profile.training_level is not None else 2
    exercise_rank = DIFFICULTY_RANK[exercise.difficulty]
    difficulty_fit = float(max(4, 18 - (abs(target_rank - exercise_rank) * 6)))
    environment_fit = 10.0 if environment == Environment.HOME else 8.0
    equipment_fit = 12.0 if set(exercise.equipment_tags).issubset({"bodyweight", "gym_mat"}) else 8.0

    total = pattern_match + muscle_match + difficulty_fit + environment_fit + equipment_fit
    breakdown = {
        "pattern_match": pattern_match,
        "muscle_match": muscle_match,
        "difficulty_fit": difficulty_fit,
        "environment_fit": environment_fit,
        "equipment_fit": equipment_fit,
        "total": total,
    }
    return total, breakdown
