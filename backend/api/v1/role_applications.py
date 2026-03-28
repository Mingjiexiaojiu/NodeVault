"""Role Application API — superadmin-only endpoints for reviewing supervisor applications."""

import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.auth.deps import get_superadmin_user
from backend.database.session import get_db
from backend.models.role_application import RoleApplication
from backend.models.user import User
from backend.schemas.admin import AdminRoleApplicationListItem, PaginatedResponse
from backend.schemas.response import ApiResponse
from backend.schemas.role_application import RoleApplicationReviewPayload

router = APIRouter(prefix="/admin/role-applications", tags=["Admin - Role Applications"])


def _to_item(app: RoleApplication, user: User | None) -> AdminRoleApplicationListItem:
    role_labels = {1: "主管"}
    return AdminRoleApplicationListItem(
        id=app.id,
        user_id=app.user_id,
        username=user.username if user else None,
        email=user.email if user else None,
        display_name=user.display_name if user else None,
        requested_role=app.requested_role,
        requested_role_label=role_labels.get(app.requested_role, str(app.requested_role)),
        status=app.status,
        reason=app.reason,
        review_note=app.review_note,
        reviewed_by=app.reviewed_by,
        created_at=app.created_at,
        reviewed_at=app.reviewed_at,
    )


@router.get("", response_model=ApiResponse)
async def list_role_applications(
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    page: int = 1,
    page_size: int = 20,
    _admin: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    q = select(RoleApplication).options(joinedload(RoleApplication.applicant))
    if status_filter:
        q = q.where(RoleApplication.status == status_filter)
    q = q.order_by(RoleApplication.created_at.desc())

    total_res = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_res.scalar_one()

    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    apps = result.unique().scalars().all()

    items = [_to_item(a, a.applicant) for a in apps]
    return ApiResponse(data=PaginatedResponse(items=[i.model_dump() for i in items], total=total, page=page, page_size=page_size).model_dump())


@router.post("/{app_id}/approve", response_model=ApiResponse)
async def approve_application(
    app_id: uuid.UUID,
    payload: RoleApplicationReviewPayload,
    admin: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(
        select(RoleApplication).where(RoleApplication.id == app_id).options(joinedload(RoleApplication.applicant))
    )
    app = result.unique().scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请不存在")
    if app.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该申请已处理")

    app.status = "approved"
    app.reviewed_by = admin.id
    app.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    app.review_note = payload.review_note

    # 升级用户角色
    user_result = await db.execute(select(User).where(User.id == app.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.role = app.requested_role

    await db.commit()
    return ApiResponse(message="申请已批准，用户角色已升级")


@router.post("/{app_id}/reject", response_model=ApiResponse)
async def reject_application(
    app_id: uuid.UUID,
    payload: RoleApplicationReviewPayload,
    admin: User = Depends(get_superadmin_user),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse:
    result = await db.execute(
        select(RoleApplication).where(RoleApplication.id == app_id)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申请不存在")
    if app.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该申请已处理")

    app.status = "rejected"
    app.reviewed_by = admin.id
    app.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    app.review_note = payload.review_note

    await db.commit()
    return ApiResponse(message="申请已拒绝")
