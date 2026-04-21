from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Environment, Goal, TrainingLevel
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    training_plans = relationship(
        "TrainingPlan",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workout_logs = relationship(
        "WorkoutLog",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="WorkoutLog.id",
    )
    plan_explanations = relationship(
        "PlanExplanation",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="PlanExplanation.id",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    training_level: Mapped[Optional[TrainingLevel]] = mapped_column(
        SqlEnum(TrainingLevel, native_enum=False),
        nullable=True,
    )
    preferred_environment: Mapped[Optional[Environment]] = mapped_column(
        SqlEnum(Environment, native_enum=False),
        nullable=True,
    )
    primary_goal: Mapped[Optional[Goal]] = mapped_column(
        SqlEnum(Goal, native_enum=False),
        nullable=True,
    )
    training_days_per_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    available_equipment: Mapped[list[str]] = mapped_column(JSON, default=list)
    discomfort_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    blocked_exercise_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[User] = relationship(back_populates="profile")
