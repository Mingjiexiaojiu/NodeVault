import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    nodes: Mapped[list["Node"]] = relationship(  # noqa: F821
        "Node", back_populates="category_rel", foreign_keys="Node.category_id"
    )


# Default categories matching the old NodeType enum
DEFAULT_CATEGORIES = [
    {"display_name": "数据清洗", "icon": "broom", "sort_order": 0},
    {"display_name": "数据分析", "icon": "chart-bar", "sort_order": 1},
    {"display_name": "风控", "icon": "shield", "sort_order": 2},
    {"display_name": "自然语言处理", "icon": "message-square", "sort_order": 3},
    {"display_name": "计算机视觉", "icon": "eye", "sort_order": 4},
    {"display_name": "机器学习", "icon": "cpu", "sort_order": 5},
    {"display_name": "工具", "icon": "wrench", "sort_order": 6},
    {"display_name": "通用", "icon": "box", "sort_order": 7},
]
