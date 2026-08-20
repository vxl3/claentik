"""OperationResult model — per-target outcome of an operation."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OperationResult(Base):
    """The outcome of a single action (unfollow/block) against one account."""

    __tablename__ = "operation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("operations.id", ondelete="CASCADE"), nullable=False
    )
    target_username: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # unfollow / block
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    operation: Mapped["Operation"] = relationship(back_populates="results")  # noqa: F821

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OperationResult id={self.id} target={self.target_username} ok={self.success}>"
