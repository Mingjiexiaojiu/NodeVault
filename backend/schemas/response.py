from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    NODE_NOT_FOUND = "NODE_NOT_FOUND"
    NODE_ALREADY_EXISTS = "NODE_ALREADY_EXISTS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVOKE_TIMEOUT = "INVOKE_TIMEOUT"
    INVOKE_FAILED = "INVOKE_FAILED"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "操作成功"
    request_id: str = Field(default_factory=lambda: str(uuid4()))


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
    request_id: str = Field(default_factory=lambda: str(uuid4()))
