from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.plan import TrainingPlan, WorkoutSession, WorkoutSessionExercise
from app.models.user import User
from app.schemas.exercise import ExerciseResponse
from app.schemas.plan import (
    GeneratePlanRequest,
    TrainingPlanDetailResponse,
    TrainingPlanListResponse,
    TrainingPlanSummaryResponse,
    WorkoutSessionExerciseResponse,
    WorkoutSessionResponse,
)
from app.services.planner import PlanGenerationError, generate_plan

router = APIRouter(prefix="/plans", tags=["plans"])


def _plan_query(plan_id: int | None = None):
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
    return statement


def _build_session_exercise_response(entry: WorkoutSessionExercise) -> WorkoutSessionExerciseResponse:
    return WorkoutSessionExerciseResponse(
        exercise=ExerciseResponse.model_validate(entry.exercise),
        slot_type=entry.slot_type,
        selection_score=entry.selection_score,
        score_breakdown=entry.score_breakdown,
        sets=entry.sets,
        reps=entry.reps,
        rest_seconds=entry.rest_seconds,
        notes=entry.notes,
    )


def _build_session_response(session: WorkoutSession) -> WorkoutSessionResponse:
    return WorkoutSessionResponse(
        id=session.id,
        day_index=session.day_index,
        session_name=session.session_name,
        focus_summary=session.focus_summary,
        exercises=[_build_session_exercise_response(entry) for entry in session.exercises],
    )


def _build_plan_summary(plan: TrainingPlan) -> TrainingPlanSummaryResponse:
    return TrainingPlanSummaryResponse(
        id=plan.id,
        goal=plan.goal,
        split=plan.split,
        training_days_per_week=plan.training_days_per_week,
        environment=plan.environment,
        generation_mode=plan.generation_mode,
        status=plan.status,
        session_count=len(plan.sessions),
        created_at=plan.created_at,
    )


def _build_plan_detail(plan: TrainingPlan) -> TrainingPlanDetailResponse:
    summary = _build_plan_summary(plan)
    return TrainingPlanDetailResponse(
        **summary.model_dump(),
        request_snapshot=plan.request_snapshot,
        sessions=[_build_session_response(session) for session in plan.sessions],
    )


def _get_owned_plan(db: Session, user_id: int, plan_id: int) -> TrainingPlan:
    plan = db.execute(_plan_query(plan_id).where(TrainingPlan.user_id == user_id)).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    return plan


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
    return _build_plan_detail(plan)


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
        items=[_build_plan_summary(plan) for plan in items],
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
    return _build_plan_detail(_get_owned_plan(db, current_user.id, plan_id))


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
