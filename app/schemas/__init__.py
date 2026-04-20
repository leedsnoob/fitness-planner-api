"""Pydantic schemas."""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.exercise import (
    CreateCustomExerciseRequest,
    ExerciseListResponse,
    ExerciseResponse,
    UpdateCustomExerciseRequest,
)
from app.schemas.plan import GeneratePlanRequest, TrainingPlanDetailResponse, TrainingPlanListResponse
from app.schemas.profile import ProfilePayload, UpdateProfileRequest, UserResponse

__all__ = [
    "CreateCustomExerciseRequest",
    "ExerciseListResponse",
    "ExerciseResponse",
    "GeneratePlanRequest",
    "LoginRequest",
    "ProfilePayload",
    "RegisterRequest",
    "TokenResponse",
    "TrainingPlanDetailResponse",
    "TrainingPlanListResponse",
    "UpdateCustomExerciseRequest",
    "UpdateProfileRequest",
    "UserResponse",
]
