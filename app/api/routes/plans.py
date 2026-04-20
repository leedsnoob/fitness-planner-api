from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.plan import PlanRevision, TrainingPlan, WorkoutSession, WorkoutSessionExercise
from app.models.user import User
from app.schemas.exercise import ExerciseResponse
from app.schemas.plan import (
    CreateAdjustmentRequest,
    GeneratePlanRequest,
    PlanAdjustmentResponse,
    PlanRevisionDetailResponse,
    PlanRevisionListResponse,
    PlanRevisionSummaryResponse,
    TrainingPlanDetailResponse,
    TrainingPlanListResponse,
)
from app.services.plan_adjustments import PlanAdjustmentError, adjust_plan_exercise
from app.services.plan_views import build_plan_detail, build_plan_summary
from app.services.planner import PlanGenerationError, generate_plan

router = APIRouter(prefix="/plans", tags=["plans"])


def _plan_query(plan_id: int | None = None, *, for_update: bool = False):
    statement = (
        select(TrainingPlan)
        .options(
            selectinload(TrainingPlan.sessions)
            .selectinload(WorkoutSession.exercises)
            .selectinload(WorkoutSessionExercise.exercise)
        )
        .order_by(TrainingPlan.id.desc())
    )
    if plan_id is not None:
        statement = statement.where(TrainingPlan.id == plan_id)
    if for_update:
        statement = statement.with_for_update()
    return statement


def _get_owned_plan(db: Session, user_id: int, plan_id: int, *, for_update: bool = False) -> TrainingPlan:
    plan = (
        db.execute(_plan_query(plan_id, for_update=for_update).where(TrainingPlan.user_id == user_id))
        .scalar_one_or_none()
    )
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    return plan


def _revision_query(plan_id: int, revision_number: int | None = None):
    statement = (
        select(PlanRevision)
        .join(TrainingPlan, PlanRevision.plan_id == TrainingPlan.id)
        .where(TrainingPlan.id == plan_id)
        .options(
            selectinload(PlanRevision.old_exercise),
            selectinload(PlanRevision.new_exercise),
        )
        .order_by(PlanRevision.revision_number.asc())
    )
    if revision_number is not None:
        statement = statement.where(PlanRevision.revision_number == revision_number)
    return statement


def _get_owned_revision(db: Session, user_id: int, plan_id: int, revision_number: int) -> PlanRevision:
    revision = (
        db.execute(
            _revision_query(plan_id, revision_number).where(TrainingPlan.user_id == user_id)
        )
        .scalar_one_or_none()
    )
    if revision is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found.")
    return revision


def _build_revision_summary(revision: PlanRevision) -> PlanRevisionSummaryResponse:
    return PlanRevisionSummaryResponse(
        revision_number=revision.revision_number,
        reason=revision.adjustment_request.reason,
        detail_note=revision.adjustment_request.detail_note,
        old_exercise=ExerciseResponse.model_validate(revision.old_exercise),
        new_exercise=ExerciseResponse.model_validate(revision.new_exercise),
        created_at=revision.created_at,
    )


def _build_revision_detail(revision: PlanRevision) -> PlanRevisionDetailResponse:
    summary = _build_revision_summary(revision)
    return PlanRevisionDetailResponse(
        **summary.model_dump(),
        score_breakdown=revision.score_breakdown,
        explanation=revision.explanation,
        before_snapshot=revision.before_snapshot,
        after_snapshot=revision.after_snapshot,
    )


@router.post("/generate", response_model=TrainingPlanDetailResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    payload: GeneratePlanRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TrainingPlanDetailResponse:
    try:
        plan = generate_plan(db, current_user, payload)
    except PlanGenerationError as exc:
        detail = str(exc)
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT if "supported" in detail else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=detail) from exc

    plan = _get_owned_plan(db, current_user.id, plan.id)
    return build_plan_detail(plan)


@router.get("", response_model=TrainingPlanListResponse)
def list_plans(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TrainingPlanListResponse:
    plans = db.execute(_plan_query().where(TrainingPlan.user_id == current_user.id)).scalars().all()
    total = len(plans)
    items = plans[offset : offset + limit]
    return TrainingPlanListResponse(
        items=[build_plan_summary(plan) for plan in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{plan_id}", response_model=TrainingPlanDetailResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> TrainingPlanDetailResponse:
    return build_plan_detail(_get_owned_plan(db, current_user.id, plan_id))


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    plan = _get_owned_plan(db, current_user.id, plan_id)
    db.delete(plan)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{plan_id}/adjustments", response_model=PlanAdjustmentResponse)
def create_adjustment(
    plan_id: int,
    payload: CreateAdjustmentRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PlanAdjustmentResponse:
    plan = _get_owned_plan(db, current_user.id, plan_id, for_update=True)
    try:
        result = adjust_plan_exercise(
            db=db,
            current_user=current_user,
            plan=plan,
            payload=payload,
        )
    except PlanAdjustmentError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail) from exc
        if "required" in detail.lower():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=detail) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail) from exc

    updated_plan = _get_owned_plan(db, current_user.id, plan_id)
    return PlanAdjustmentResponse(
        revision_number=result.revision_number,
        old_exercise=ExerciseResponse.model_validate(result.old_exercise),
        new_exercise=ExerciseResponse.model_validate(result.new_exercise),
        score_breakdown=result.score_breakdown,
        explanation=result.explanation,
        updated_plan=build_plan_detail(updated_plan),
    )


@router.get("/{plan_id}/revisions", response_model=PlanRevisionListResponse)
def list_plan_revisions(
    plan_id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PlanRevisionListResponse:
    _get_owned_plan(db, current_user.id, plan_id)
    revisions = (
        db.execute(_revision_query(plan_id).where(TrainingPlan.user_id == current_user.id))
        .scalars()
        .all()
    )
    return PlanRevisionListResponse(
        items=[_build_revision_summary(revision) for revision in revisions],
        total=len(revisions),
    )


@router.get("/{plan_id}/revisions/{revision_number}", response_model=PlanRevisionDetailResponse)
def get_plan_revision(
    plan_id: int,
    revision_number: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> PlanRevisionDetailResponse:
    revision = _get_owned_revision(db, current_user.id, plan_id, revision_number)
    return _build_revision_detail(revision)
