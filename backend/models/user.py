import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 身份：0=超级管理员, 1=主管级, 2=普通用户
    role: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    # 个人资料
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owned_namespaces: Mapped[list["Namespace"]] = relationship(  # noqa: F821
        "Namespace", back_populates="owner", foreign_keys="Namespace.owner_id"
    )
    memberships: Mapped[list["NamespaceMember"]] = relationship(  # noqa: F821
        "NamespaceMember", back_populates="user"
    )
    api_keys: Mapped[list["ApiKey"]] = relationship(  # noqa: F821
        "ApiKey", back_populates="owner", cascade="all, delete-orphan"
    )
    credentials: Mapped[list["ServiceCredential"]] = relationship(  # noqa: F821
        "ServiceCredential", back_populates="owner", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("email", name="uq_user_email"),)

    ROLE_LABELS = {0: "超级管理员", 1: "主管", 2: "普通用户"}
