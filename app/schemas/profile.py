from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import Environment, Goal, TrainingLevel


class ProfilePayload(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: Optional[str] = None
    training_level: Optional[TrainingLevel] = None
    preferred_environment: Optional[Environment] = None
    primary_goal: Optional[Goal] = None
    training_days_per_week: Optional[int] = None
    available_equipment: list[str] = Field(default_factory=list)
    discomfort_tags: list[str] = Field(default_factory=list)
    blocked_exercise_ids: list[int] = Field(default_factory=list)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    profile: ProfilePayload


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=120)
    training_level: Optional[TrainingLevel] = None
    preferred_environment: Optional[Environment] = None
    primary_goal: Optional[Goal] = None
    training_days_per_week: Optional[int] = Field(default=None, ge=3, le=4)
    available_equipment: list[str] = Field(default_factory=list)
    discomfort_tags: list[str] = Field(default_factory=list)
    blocked_exercise_ids: list[int] = Field(default_factory=list)
