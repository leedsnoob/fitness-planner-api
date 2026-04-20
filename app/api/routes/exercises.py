from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_current_user
from app.core.enums import DifficultyLevel, MovementPattern
from app.db.session import get_db_session
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.exercise import (
    CreateCustomExerciseRequest,
    ExerciseListResponse,
    ExerciseResponse,
    UpdateCustomExerciseRequest,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])
custom_router = APIRouter(prefix="/me/custom-exercises", tags=["custom-exercises"])


def _build_exercise_response(exercise: Exercise) -> ExerciseResponse:
    return ExerciseResponse.model_validate(exercise)


def _get_custom_exercise_for_update(db: Session, exercise_id: int) -> Exercise | None:
    exercise = db.get(Exercise, exercise_id)
    if exercise is None or not exercise.is_custom:
        return None
    return exercise


def _normalize_environment(environment: Optional[str]) -> Optional[str]:
    if environment is None:
        return None
    normalized = environment.strip().lower()
    if normalized not in {"home", "gym"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Environment filter must be 'home' or 'gym'.",
        )
    return normalized


def _matches_environment(exercise: Exercise, environment: Optional[str]) -> bool:
    if environment is None:
        return True
    tags = set(exercise.environment_tags)
    if environment == "home":
        return bool(tags.intersection({"home", "both"}))
    return bool(tags.intersection({"gym", "both"}))


def _matches_equipment(exercise: Exercise, equipment_tag: Optional[str]) -> bool:
    if not equipment_tag:
        return True
    return equipment_tag.strip().lower() in set(exercise.equipment_tags)


@router.get("", response_model=ExerciseListResponse, summary="List exercises")
def list_exercises(
    movement_pattern: Optional[MovementPattern] = None,
    difficulty: Optional[DifficultyLevel] = None,
    environment: Optional[str] = Query(default=None),
    equipment_tag: Optional[str] = None,
    include_custom: bool = True,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ExerciseListResponse:
    normalized_environment = _normalize_environment(environment)
    scope_filter = Exercise.owner_user_id.is_(None)
    if include_custom and current_user is not None:
        scope_filter = or_(Exercise.owner_user_id.is_(None), Exercise.owner_user_id == current_user.id)

    conditions = [scope_filter]

    if movement_pattern is not None:
        conditions.append(Exercise.movement_pattern == movement_pattern.value)
    if difficulty is not None:
        conditions.append(Exercise.difficulty == difficulty.value)
    statement = select(Exercise).where(*conditions).order_by(Exercise.id)
    items = db.execute(statement).scalars().all()
    filtered = [
        item
        for item in items
        if _matches_environment(item, normalized_environment) and _matches_equipment(item, equipment_tag)
    ]
    total = len(filtered)
    items = filtered[offset : offset + limit]

    return ExerciseListResponse(
        items=[_build_exercise_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{exercise_id}", response_model=ExerciseResponse, summary="Get exercise by id")
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db_session),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ExerciseResponse:
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found.")
    if exercise.owner_user_id is not None and (current_user is None or exercise.owner_user_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found.")
    return _build_exercise_response(exercise)


@custom_router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_custom_exercise(
    payload: CreateCustomExerciseRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExerciseResponse:
    exercise = Exercise(
        source_name="custom",
        owner_user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        primary_muscles=payload.primary_muscles,
        secondary_muscles=payload.secondary_muscles,
        movement_pattern=payload.movement_pattern.value,
        equipment_tags=payload.equipment_tags,
        environment_tags=payload.environment_tags,
        difficulty=payload.difficulty.value,
        impact_level=payload.impact_level.value,
        contraindication_tags=payload.contraindication_tags,
        is_custom=True,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return _build_exercise_response(exercise)


@custom_router.patch("/{exercise_id}", response_model=ExerciseResponse)
def update_custom_exercise(
    exercise_id: int,
    payload: UpdateCustomExerciseRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExerciseResponse:
    exercise = _get_custom_exercise_for_update(db, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom exercise not found.")
    if exercise.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom exercise not found.")

    for key, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(value, "value"):
            value = value.value
        setattr(exercise, key, value)

    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return _build_exercise_response(exercise)


@custom_router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_exercise(
    exercise_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    exercise = _get_custom_exercise_for_update(db, exercise_id)
    if exercise is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom exercise not found.")
    if exercise.owner_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom exercise not found.")
    profile = current_user.profile
    profile.blocked_exercise_ids = [
        blocked_id for blocked_id in profile.blocked_exercise_ids if blocked_id != exercise_id
    ]
    db.add(profile)
    db.delete(exercise)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
