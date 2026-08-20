"""Operation model — records one cleanup run."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OperationType(str, enum.Enum):
    CLEANUP_FOLLOWING = "cleanup_following"
    CLEANUP_FOLLOWERS = "cleanup_followers"


class OperationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class Operation(Base):
    """A single cleanup operation (unfollow non-followers / remove followers)."""

    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False
    )
    tiktok_account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tiktok_accounts.id", ondelete="CASCADE"), nullable=False
    )
    operation_type: Mapped[OperationType] = mapped_column(
        Enum(
            OperationType,
            name="operation_type",
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    status: Mapped[OperationStatus] = mapped_column(
        Enum(
            OperationStatus,
            name="operation_status",
            values_callable=lambda e: [x.value for x in e],
        ),
        default=OperationStatus.PENDING,
        nullable=False,
    )
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["OperationResult"]] = relationship(  # noqa: F821
        back_populates="operation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Operation id={self.id} type={self.operation_type} status={self.status}>"
