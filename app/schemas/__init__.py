"""Pydantic schemas."""

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.exercise import (
    CreateCustomExerciseRequest,
    ExerciseListResponse,
    ExerciseResponse,
    UpdateCustomExerciseRequest,
)
from app.schemas.profile import ProfilePayload, UpdateProfileRequest, UserResponse

__all__ = [
    "CreateCustomExerciseRequest",
    "ExerciseListResponse",
    "ExerciseResponse",
    "LoginRequest",
    "ProfilePayload",
    "RegisterRequest",
    "TokenResponse",
    "UpdateCustomExerciseRequest",
    "UpdateProfileRequest",
    "UserResponse",
]
