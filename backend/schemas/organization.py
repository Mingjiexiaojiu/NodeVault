import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    team_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
