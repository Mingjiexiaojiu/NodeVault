import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base
from backend.schemas.enums import NodeStatus, NodeVisibility



class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=NodeStatus.DRAFT.value, nullable=False, index=True
    )
    visibility: Mapped[str] = mapped_column(
        String(32), default=NodeVisibility.INTERNAL.value, nullable=False
    )
    invocation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_credential_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_credentials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    discovery_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    department: Mapped["Department"] = relationship(  # noqa: F821
        "Department", back_populates="nodes"
    )
    owner: Mapped["User"] = relationship(  # noqa: F821
        "User", foreign_keys=[owner_id], lazy="joined",
    )
    category_rel: Mapped["Category"] = relationship(  # noqa: F821
        "Category", back_populates="nodes", foreign_keys=[category_id], lazy="joined"
    )
    source_credential: Mapped["ServiceCredential | None"] = relationship(  # noqa: F821
        "ServiceCredential", foreign_keys=[source_credential_id], lazy="joined"
    )
    skill_nodes: Mapped[list["SkillNode"]] = relationship(  # noqa: F821
        "SkillNode", back_populates="node", cascade="all, delete-orphan"
    )
    discovery_session: Mapped["DiscoverySession | None"] = relationship(  # noqa: F821
        "DiscoverySession", foreign_keys=[discovery_session_id], back_populates="nodes"
    )
    versions: Mapped[list["NodeVersion"]] = relationship(
        "NodeVersion", back_populates="node", cascade="all, delete-orphan"
    )
    tags: Mapped[list["NodeTag"]] = relationship(
        "NodeTag", back_populates="node", cascade="all, delete-orphan"
    )
    invocation_logs: Mapped[list["NodeInvocationLog"]] = relationship(
        "NodeInvocationLog", back_populates="node"
    )

    __table_args__ = (
        UniqueConstraint("name", "department_id", name="uq_node_name_department"),
    )


class NodeVersion(Base):
    __tablename__ = "node_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    runtime_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deprecated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    node: Mapped["Node"] = relationship("Node", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("node_id", "version", name="uq_node_version"),
    )


class NodeTag(Base):
    __tablename__ = "node_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    node: Mapped["Node"] = relationship("Node", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("node_id", "tag", name="uq_node_tag"),
    )


class NodeInvocationLog(Base):
    __tablename__ = "node_invocation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    invoked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    input_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    node: Mapped["Node"] = relationship("Node", back_populates="invocation_logs")

    __table_args__ = (
        Index("ix_invocation_logs_node_created", "node_id", "created_at"),
    )


__all__ = ["Node", "NodeVersion", "NodeTag", "NodeInvocationLog"]
