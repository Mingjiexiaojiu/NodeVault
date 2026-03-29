import uuid
from datetime import datetime

from pydantic import BaseModel


class PendingRoleApplication(BaseModel):
    """嵌套在 UserResponse 中，表示用户当前的待审批申请"""
    requested_role: int
    created_at: datetime


class RoleApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str | None = None
    email: str | None = None
    requested_role: int
    status: str
    reason: str | None = None
    review_note: str | None = None
    reviewed_by: uuid.UUID | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class RoleApplicationReviewPayload(BaseModel):
    department_id: uuid.UUID
    review_note: str | None = None
