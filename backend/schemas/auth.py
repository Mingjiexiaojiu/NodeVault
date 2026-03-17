import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-z][a-z0-9_]{2,63}$")
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "Password must be at least 8 characters and contain uppercase, lowercase, and a digit"
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
