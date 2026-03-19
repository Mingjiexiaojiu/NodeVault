import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class UserAIConfig(Base):
    """用户自定义 AI 提供商配置，用于 SKILL.md 生成。"""

    __tablename__ = "user_ai_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # 用户给该配置取的名字，如"我的 Claude Opus"
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # 提供商类型：openai / claude / custom
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="openai")
    # 模型名称，如 gpt-4o、claude-opus-4-5
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    # API Key（明文存储，与 ApiKey 模型同等对待）
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    # 自定义 Base URL（openai-compatible API 用，可为空）
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # 是否为默认配置
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
