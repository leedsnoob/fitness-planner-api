from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import Environment, Goal, PlanSplit
from app.db.session import Base


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal: Mapped[Goal] = mapped_column(SqlEnum(Goal, native_enum=False))
    split: Mapped[PlanSplit] = mapped_column(SqlEnum(PlanSplit, native_enum=False))
    training_days_per_week: Mapped[int] = mapped_column(Integer)
    environment: Mapped[Environment] = mapped_column(SqlEnum(Environment, native_enum=False))
    generation_mode: Mapped[str] = mapped_column(String(64), default="rule_based_v1")
    request_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="training_plans")
    sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutSession.day_index",
    )


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (UniqueConstraint("plan_id", "day_index", name="uq_plan_day_index"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("training_plans.id", ondelete="CASCADE"), index=True)
    day_index: Mapped[int] = mapped_column(Integer)
    session_name: Mapped[str] = mapped_column(String(120))
    focus_summary: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped[TrainingPlan] = relationship(back_populates="sessions")
    exercises: Mapped[list["WorkoutSessionExercise"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkoutSessionExercise.id",
    )


class WorkoutSessionExercise(Base):
    __tablename__ = "workout_session_exercises"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    slot_type: Mapped[str] = mapped_column(String(64))
    selection_score: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    sets: Mapped[int] = mapped_column(Integer)
    reps: Mapped[str] = mapped_column(String(32))
    rest_seconds: Mapped[int] = mapped_column(Integer)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    session: Mapped[WorkoutSession] = relationship(back_populates="exercises")
    exercise = relationship("Exercise")
