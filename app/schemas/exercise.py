from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DifficultyLevel, ImpactLevel, MovementPattern


class ExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[str] = None
    source_name: str
    name: str
    description: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    movement_pattern: str
    equipment_tags: list[str]
    environment_tags: list[str]
    difficulty: str
    impact_level: str
    contraindication_tags: list[str]
    is_custom: bool


class ExerciseListResponse(BaseModel):
    items: list[ExerciseResponse]
    total: int
    limit: int
    offset: int


class CreateCustomExerciseRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=5000)
    primary_muscles: list[str] = Field(default_factory=list)
    secondary_muscles: list[str] = Field(default_factory=list)
    movement_pattern: MovementPattern
    equipment_tags: list[str] = Field(default_factory=list)
    environment_tags: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    impact_level: ImpactLevel
    contraindication_tags: list[str] = Field(default_factory=list)


class UpdateCustomExerciseRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=5000)
    primary_muscles: Optional[list[str]] = None
    secondary_muscles: Optional[list[str]] = None
    movement_pattern: Optional[MovementPattern] = None
    equipment_tags: Optional[list[str]] = None
    environment_tags: Optional[list[str]] = None
    difficulty: Optional[DifficultyLevel] = None
    impact_level: Optional[ImpactLevel] = None
    contraindication_tags: Optional[list[str]] = None
