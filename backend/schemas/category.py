import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    display_name: str = Field(..., min_length=1, max_length=128)
    icon: str | None = None
    sort_order: int = 0

    @field_validator("name")
    @classmethod
    def name_must_be_snake_case(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z][a-z0-9_]{0,63}$", v):
            raise ValueError("name 必须为 snake_case 格式（小写字母、数字和下划线）")
        return v


class CategoryUpdate(BaseModel):
    display_name: str | None = None
    icon: str | None = None
    sort_order: int | None = None


class CategoryRead(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str
    icon: str | None
    sort_order: int
    is_default: bool
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
