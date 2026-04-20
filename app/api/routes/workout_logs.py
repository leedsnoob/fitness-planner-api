from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.enums import WorkoutCompletionStatus
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.log import (
    CreateWorkoutLogRequest,
    UpdateWorkoutLogRequest,
    WorkoutLogListResponse,
    WorkoutLogResponse,
)
from app.services.workout_logs import (
    WorkoutLogError,
    WorkoutLogFilters,
    build_workout_log_response,
    create_workout_log,
    get_owned_workout_log,
    list_owned_workout_logs,
    update_workout_log,
)

router = APIRouter(prefix="/workout-logs", tags=["workout-logs"])


def _raise_for_workout_log_error(exc: WorkoutLogError) -> None:
    detail = str(exc)
    if "not found" in detail.lower():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
    if "already exists" in detail.lower():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail) from exc


def _get_owned_log_or_404(db: Session, user_id: int, log_id: int):
    log = get_owned_workout_log(db, user_id, log_id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found.")
    return log


@router.post("", response_model=WorkoutLogResponse, status_code=status.HTTP_201_CREATED)
def create_log(
    payload: CreateWorkoutLogRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutLogResponse:
    try:
        log = create_workout_log(db, current_user.id, payload)
    except WorkoutLogError as exc:
        _raise_for_workout_log_error(exc)
    return build_workout_log_response(log)


@router.get("", response_model=WorkoutLogListResponse)
def list_logs(
    plan_id: Optional[int] = Query(default=None),
    session_id: Optional[int] = Query(default=None),
    performed_from: Optional[date] = Query(default=None),
    performed_to: Optional[date] = Query(default=None),
    completion_status: Optional[WorkoutCompletionStatus] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutLogListResponse:
    filters = WorkoutLogFilters(
        plan_id=plan_id,
        session_id=session_id,
        performed_from=performed_from,
        performed_to=performed_to,
        completion_status=completion_status,
        limit=limit,
        offset=offset,
    )
    logs, total = list_owned_workout_logs(db, current_user.id, filters)
    return WorkoutLogListResponse(
        items=[build_workout_log_response(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{log_id}", response_model=WorkoutLogResponse)
def get_log(
    log_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutLogResponse:
    return build_workout_log_response(_get_owned_log_or_404(db, current_user.id, log_id))


@router.patch("/{log_id}", response_model=WorkoutLogResponse)
def patch_log(
    log_id: int,
    payload: UpdateWorkoutLogRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> WorkoutLogResponse:
    log = _get_owned_log_or_404(db, current_user.id, log_id)
    try:
        updated_log = update_workout_log(db, log, payload)
    except WorkoutLogError as exc:
        _raise_for_workout_log_error(exc)
    return build_workout_log_response(updated_log)


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(
    log_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    log = _get_owned_log_or_404(db, current_user.id, log_id)
    db.delete(log)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
