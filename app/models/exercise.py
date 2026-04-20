from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        UniqueConstraint("source_name", "source_id", name="uq_exercises_source_record"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    source_name: Mapped[str] = mapped_column(String(64), default="wger", index=True)
    owner_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    primary_muscles: Mapped[list[str]] = mapped_column(JSON, default=list)
    secondary_muscles: Mapped[list[str]] = mapped_column(JSON, default=list)
    movement_pattern: Mapped[str] = mapped_column(String(64), index=True)
    equipment_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    environment_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(32), index=True)
    impact_level: Mapped[str] = mapped_column(String(32), index=True)
    contraindication_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
