from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class ServiceCredential(Base):
    __tablename__ = "service_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    auth_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # bearer_login, bearer_static, api_key, basic

    # --- bearer_login fields ---
    login_endpoint: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    login_method: Mapped[str | None] = mapped_column(
        String(8), nullable=True, default="POST"
    )
    login_body_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    credential_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    credential_nonce: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    token_json_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    token_ttl: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- bearer_static fields ---
    static_token_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    static_token_nonce: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )

    # --- api_key fields ---
    api_key_header: Mapped[str | None] = mapped_column(
        String(128), nullable=True, default="X-API-Key"
    )
    api_key_encrypted: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    api_key_nonce: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="credentials")
    token_cache: Mapped[list["CredentialTokenCache"]] = relationship(
        "CredentialTokenCache",
        back_populates="credential",
        cascade="all, delete-orphan",
    )


class CredentialTokenCache(Base):
    __tablename__ = "credential_token_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    credential_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("service_credentials.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    credential: Mapped["ServiceCredential"] = relationship(
        "ServiceCredential", back_populates="token_cache"
    )
