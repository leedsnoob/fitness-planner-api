"""Pydantic schemas."""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.exercise import (
    CreateCustomExerciseRequest,
    ExerciseListResponse,
    ExerciseResponse,
    UpdateCustomExerciseRequest,
)
from app.schemas.log import (
    AdherenceAnalyticsResponse,
    CreateWorkoutLogRequest,
    ReplacementAnalyticsResponse,
    UpdateWorkoutLogRequest,
    VolumeAnalyticsResponse,
    WorkoutLogListResponse,
    WorkoutLogResponse,
)
from app.schemas.plan import GeneratePlanRequest, TrainingPlanDetailResponse, TrainingPlanListResponse
from app.schemas.plan import (
    CreateAdjustmentRequest,
    PlanAdjustmentResponse,
    PlanExplanationListResponse,
    PlanExplanationResponse,
    PlanRevisionDetailResponse,
    PlanRevisionListResponse,
)
from app.schemas.profile import ProfilePayload, UpdateProfileRequest, UserResponse

__all__ = [
    "AdherenceAnalyticsResponse",
    "CreateCustomExerciseRequest",
    "CreateAdjustmentRequest",
    "CreateWorkoutLogRequest",
    "ExerciseListResponse",
    "ExerciseResponse",
    "GeneratePlanRequest",
    "LoginRequest",
    "PlanAdjustmentResponse",
    "PlanExplanationListResponse",
    "PlanExplanationResponse",
    "PlanRevisionDetailResponse",
    "PlanRevisionListResponse",
    "ProfilePayload",
    "ReplacementAnalyticsResponse",
    "RegisterRequest",
    "TokenResponse",
    "TrainingPlanDetailResponse",
    "TrainingPlanListResponse",
    "UpdateCustomExerciseRequest",
    "UpdateWorkoutLogRequest",
    "UpdateProfileRequest",
    "UserResponse",
    "VolumeAnalyticsResponse",
    "WorkoutLogListResponse",
    "WorkoutLogResponse",
]
