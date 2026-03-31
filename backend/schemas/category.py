import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128)
    icon: str | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    display_name: str | None = None
    icon: str | None = None
    sort_order: int | None = None


class CategoryRead(BaseModel):
    id: uuid.UUID
    display_name: str
    icon: str | None
    sort_order: int
    is_default: bool
    created_by: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
