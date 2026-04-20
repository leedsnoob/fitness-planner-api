from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import AdjustmentReason, Environment, Goal, PlanSplit
from app.schemas.exercise import ExerciseResponse


class GeneratePlanRequest(BaseModel):
    split: PlanSplit
    goal: Goal
    training_days_per_week: int = Field(ge=3, le=4)
    environment: Environment
    note: Optional[str] = Field(default=None, max_length=1000)


class WorkoutSessionExerciseResponse(BaseModel):
    id: int
    exercise: ExerciseResponse
    slot_type: str
    selection_score: float
    score_breakdown: dict[str, float]
    sets: int
    reps: str
    rest_seconds: int
    notes: str


class WorkoutSessionResponse(BaseModel):
    id: int
    day_index: int
    session_name: str
    focus_summary: str
    exercises: list[WorkoutSessionExerciseResponse]


class TrainingPlanSummaryResponse(BaseModel):
    id: int
    goal: Goal
    split: PlanSplit
    training_days_per_week: int
    environment: Environment
    generation_mode: str
    status: str
    current_revision_number: int
    session_count: int
    created_at: datetime


class TrainingPlanDetailResponse(TrainingPlanSummaryResponse):
    request_snapshot: dict
    sessions: list[WorkoutSessionResponse]


class TrainingPlanListResponse(BaseModel):
    items: list[TrainingPlanSummaryResponse]
    total: int
    limit: int
    offset: int


class CreateAdjustmentRequest(BaseModel):
    session_exercise_id: int
    reason: AdjustmentReason
    detail_note: Optional[str] = Field(default=None, max_length=1000)
    override_environment: Optional[Environment] = None
    temporary_unavailable_equipment: list[str] = Field(default_factory=list)
    temporary_discomfort_tags: list[str] = Field(default_factory=list)


class PlanAdjustmentResponse(BaseModel):
    revision_number: int
    old_exercise: ExerciseResponse
    new_exercise: ExerciseResponse
    score_breakdown: dict[str, float]
    explanation: str
    updated_plan: TrainingPlanDetailResponse


class PlanRevisionSummaryResponse(BaseModel):
    revision_number: int
    reason: AdjustmentReason
    detail_note: str
    old_exercise: ExerciseResponse
    new_exercise: ExerciseResponse
    created_at: datetime


class PlanRevisionListResponse(BaseModel):
    items: list[PlanRevisionSummaryResponse]
    total: int


class PlanRevisionDetailResponse(PlanRevisionSummaryResponse):
    score_breakdown: dict[str, float]
    explanation: str
    before_snapshot: dict
    after_snapshot: dict
