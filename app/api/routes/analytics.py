from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.plan import TrainingPlan
from app.models.user import User
from app.schemas.log import AdherenceAnalyticsResponse, ReplacementAnalyticsResponse, VolumeAnalyticsResponse
from app.services.analytics import (
    build_adherence_analytics,
    build_replacement_analytics,
    build_volume_analytics,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _ensure_owned_plan(db: Session, user_id: int, plan_id: int) -> None:
    plan = db.execute(
        select(TrainingPlan.id).where(TrainingPlan.user_id == user_id, TrainingPlan.id == plan_id)
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")


@router.get("/volume", response_model=VolumeAnalyticsResponse)
def get_volume_analytics(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> VolumeAnalyticsResponse:
    return build_volume_analytics(db, current_user.id, days=days)


@router.get("/adherence", response_model=AdherenceAnalyticsResponse)
def get_adherence_analytics(
    plan_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> AdherenceAnalyticsResponse:
    if plan_id is not None:
        _ensure_owned_plan(db, current_user.id, plan_id)
    return build_adherence_analytics(db, current_user.id, plan_id=plan_id)


@router.get("/replacements", response_model=ReplacementAnalyticsResponse)
def get_replacement_analytics(
    plan_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReplacementAnalyticsResponse:
    if plan_id is not None:
        _ensure_owned_plan(db, current_user.id, plan_id)
    return build_replacement_analytics(db, current_user.id, plan_id=plan_id)
