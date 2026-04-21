from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AdjustmentReason, Environment, ExplanationScope, Goal, PlanSplit, WorkoutCompletionStatus
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
    current_revision_number: Mapped[int] = mapped_column(Integer, default=0)
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
    adjustment_requests: Mapped[list["AdjustmentRequest"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="AdjustmentRequest.id",
    )
    revisions: Mapped[list["PlanRevision"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanRevision.revision_number",
    )
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutLog.id",
    )
    explanations: Mapped[list["PlanExplanation"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanExplanation.id",
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
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkoutLog.id",
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
    workout_log: Mapped[Optional["WorkoutLog"]] = relationship(
        back_populates="session_exercise",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AdjustmentRequest(Base):
    __tablename__ = "adjustment_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("training_plans.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    session_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_session_exercises.id", ondelete="CASCADE"),
        index=True,
    )
    reason: Mapped[AdjustmentReason] = mapped_column(SqlEnum(AdjustmentReason, native_enum=False))
    detail_note: Mapped[str] = mapped_column(Text, default="")
    override_environment: Mapped[Optional[Environment]] = mapped_column(
        SqlEnum(Environment, native_enum=False),
        nullable=True,
    )
    temporary_unavailable_equipment: Mapped[list[str]] = mapped_column(JSON, default=list)
    temporary_discomfort_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped[TrainingPlan] = relationship(back_populates="adjustment_requests")
    session = relationship("WorkoutSession")
    session_exercise = relationship("WorkoutSessionExercise")
    revision: Mapped["PlanRevision"] = relationship(
        back_populates="adjustment_request",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PlanRevision(Base):
    __tablename__ = "plan_revisions"
    __table_args__ = (UniqueConstraint("plan_id", "revision_number", name="uq_plan_revision_number"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("training_plans.id", ondelete="CASCADE"), index=True)
    adjustment_request_id: Mapped[int] = mapped_column(
        ForeignKey("adjustment_requests.id", ondelete="CASCADE"),
        unique=True,
    )
    revision_number: Mapped[int] = mapped_column(Integer)
    old_exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    new_exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    explanation: Mapped[str] = mapped_column(Text, default="")
    before_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    after_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped[TrainingPlan] = relationship(back_populates="revisions")
    adjustment_request: Mapped[AdjustmentRequest] = relationship(back_populates="revision")
    old_exercise = relationship("Exercise", foreign_keys=[old_exercise_id])
    new_exercise = relationship("Exercise", foreign_keys=[new_exercise_id])
    explanations: Mapped[list["PlanExplanation"]] = relationship(
        back_populates="revision",
        order_by="PlanExplanation.id",
    )


class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    __table_args__ = (UniqueConstraint("session_exercise_id", name="uq_workout_log_session_exercise"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("training_plans.id", ondelete="CASCADE"), index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True)
    session_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_session_exercises.id", ondelete="CASCADE"),
        index=True,
    )
    exercise_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exercises.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    exercise_name_snapshot: Mapped[str] = mapped_column(String(255))
    slot_type_snapshot: Mapped[str] = mapped_column(String(64))
    movement_pattern_snapshot: Mapped[str] = mapped_column(String(64))
    planned_sets: Mapped[int] = mapped_column(Integer)
    planned_reps: Mapped[str] = mapped_column(String(32))
    planned_rest_seconds: Mapped[int] = mapped_column(Integer)
    completed_sets: Mapped[int] = mapped_column(Integer)
    completed_reps_total: Mapped[int] = mapped_column(Integer)
    completion_status: Mapped[WorkoutCompletionStatus] = mapped_column(
        SqlEnum(WorkoutCompletionStatus, native_enum=False),
        index=True,
    )
    effort_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    performed_on: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="workout_logs")
    plan: Mapped[TrainingPlan] = relationship(back_populates="workout_logs")
    session: Mapped[WorkoutSession] = relationship(back_populates="workout_logs")
    session_exercise: Mapped[WorkoutSessionExercise] = relationship(back_populates="workout_log")
    exercise = relationship("Exercise", passive_deletes=True)


class PlanExplanation(Base):
    __tablename__ = "plan_explanations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("training_plans.id", ondelete="CASCADE"), index=True)
    revision_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plan_revisions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    explanation_scope: Mapped[ExplanationScope] = mapped_column(
        SqlEnum(ExplanationScope, native_enum=False),
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(64))
    model_name: Mapped[str] = mapped_column(String(128))
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    output_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="plan_explanations")
    plan: Mapped[TrainingPlan] = relationship(back_populates="explanations")
    revision: Mapped[Optional[PlanRevision]] = relationship(back_populates="explanations")
