"""Organization API — 组织管理端点。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.database.session import get_db
from backend.models.department import Department
from backend.models.organization import Organization
from backend.models.user import User
from backend.schemas.organization import OrganizationCreate, OrganizationResponse
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=ApiResponse, summary="组织列表")
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """返回所有组织及其下属团队数量。"""
    stmt = (
        select(
            Organization,
            func.count(Department.id).label("team_count"),
        )
        .outerjoin(Department, Department.org_id == Organization.id)
        .group_by(Organization.id)
        .order_by(Organization.name)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = [
        OrganizationResponse(
            id=org.id,
            name=org.name,
            team_count=team_count,
            created_at=org.created_at,
        ).model_dump()
        for org, team_count in rows
    ]
    return ApiResponse(data={"items": items})


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建组织")
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """创建新组织，仅超管(0)和主管(1)可操作。"""
    if current_user.role > 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅主管及以上身份可创建组织",
        )

    existing = await db.execute(
        select(Organization).where(Organization.name == payload.name)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="组织名称已存在",
        )

    org = Organization(name=payload.name)
    db.add(org)
    await db.commit()
    await db.refresh(org)

    return ApiResponse(
        data=OrganizationResponse(
            id=org.id,
            name=org.name,
            team_count=0,
            created_at=org.created_at,
        ).model_dump(),
        message="组织已创建",
    )
