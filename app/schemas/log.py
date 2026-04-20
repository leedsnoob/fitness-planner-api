from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.enums import AdjustmentReason, WorkoutCompletionStatus


class CreateWorkoutLogRequest(BaseModel):
    plan_id: int
    session_id: int
    session_exercise_id: int
    completion_status: WorkoutCompletionStatus
    completed_sets: int = Field(ge=0)
    completed_reps_total: int = Field(ge=0)
    effort_rating: Optional[int] = Field(default=None, ge=1, le=10)
    note: Optional[str] = Field(default=None, max_length=1000)
    performed_on: date


class UpdateWorkoutLogRequest(BaseModel):
    completion_status: Optional[WorkoutCompletionStatus] = None
    completed_sets: Optional[int] = Field(default=None, ge=0)
    completed_reps_total: Optional[int] = Field(default=None, ge=0)
    effort_rating: Optional[int] = Field(default=None, ge=1, le=10)
    note: Optional[str] = Field(default=None, max_length=1000)
    performed_on: Optional[date] = None


class WorkoutLogResponse(BaseModel):
    id: int
    plan_id: int
    session_id: int
    session_exercise_id: int
    exercise_id: Optional[int]
    exercise_name_snapshot: str
    slot_type_snapshot: str
    movement_pattern_snapshot: str
    planned_sets: int
    planned_reps: str
    planned_rest_seconds: int
    completed_sets: int
    completed_reps_total: int
    completion_status: WorkoutCompletionStatus
    effort_rating: Optional[int]
    note: str
    performed_on: date
    created_at: datetime
    updated_at: datetime


class WorkoutLogListResponse(BaseModel):
    items: list[WorkoutLogResponse]
    total: int
    limit: int
    offset: int


class VolumeDailyPoint(BaseModel):
    date: date
    completed_sets: int
    completed_reps: int
    logged_exercises: int


class VolumeAnalyticsResponse(BaseModel):
    total_logged_sessions: int
    total_completed_sets: int
    total_completed_reps: int
    daily_points: list[VolumeDailyPoint]


class AdherenceAnalyticsResponse(BaseModel):
    planned_exercises: int
    logged_exercises: int
    completed_exercises: int
    partial_exercises: int
    skipped_exercises: int
    adherence_rate: float


class ReplacementAnalyticsItem(BaseModel):
    revision_number: int
    reason: AdjustmentReason
    old_exercise_name: str
    new_exercise_name: str
    created_at: datetime


class ReplacementAnalyticsResponse(BaseModel):
    total_revisions: int
    by_reason: dict[str, int]
    latest_revisions: list[ReplacementAnalyticsItem]
