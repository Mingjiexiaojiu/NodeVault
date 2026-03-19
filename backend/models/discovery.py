"""DiscoverySession model — tracks each service probe / import session."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class DiscoverySession(Base):
    __tablename__ = "discovery_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False, default="")
    # "probe" | "upload"
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="probe")
    # "probing" | "found" | "failed" | "completed"
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="probing", index=True)
    spec_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    total_operations: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imported_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[user_id], lazy="joined"
    )
    nodes: Mapped[list["Node"]] = relationship(  # noqa: F821
        "Node", back_populates="discovery_session", foreign_keys="Node.discovery_session_id"
    )
