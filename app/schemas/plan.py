from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import Environment, Goal, PlanSplit
from app.schemas.exercise import ExerciseResponse


class GeneratePlanRequest(BaseModel):
    split: PlanSplit
    goal: Goal
    training_days_per_week: int = Field(ge=3, le=4)
    environment: Environment
    note: Optional[str] = Field(default=None, max_length=1000)


class WorkoutSessionExerciseResponse(BaseModel):
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
