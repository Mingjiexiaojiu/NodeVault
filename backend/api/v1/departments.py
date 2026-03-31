import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth.deps import get_current_user
from backend.database.session import get_db
from backend.models.department import Department, DepartmentMember
from backend.models.node import Node
from backend.models.organization import Organization
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.response import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/departments", tags=["Departments"])


# ── schemas (local) ──────────────────────────────────────────────
from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    org_name: str = Field(..., min_length=1, max_length=128)
    team_name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None


class DepartmentUpdate(BaseModel):
    team_name: str | None = None
    description: str | None = None


class MemberAdd(BaseModel):
    username: str
    role: str = Field(default="member", pattern=r"^(admin|member)$")


# ── endpoints ────────────────────────────────────────────────────


@router.get("/public", response_model=ApiResponse, summary="公开部门列表（注册时使用，无需登录）")
async def list_departments_public(
    db: AsyncSession = Depends(get_db),
):
    """返回已有主管（User.role==1 且 DepartmentMember.role=='admin'）的部门列表，用于注册页面选择部门，无需身份验证。"""
    supervisor_exists = (
        select(DepartmentMember.department_id)
        .join(User, DepartmentMember.user_id == User.id)
        .where(
            DepartmentMember.department_id == Department.id,
            DepartmentMember.role == "admin",
            User.role == 1,
        )
        .exists()
    )

    # Query supervisor username for each department
    supervisor_sq = (
        select(
            DepartmentMember.department_id,
            User.username.label("admin_username"),
        )
        .join(User, DepartmentMember.user_id == User.id)
        .where(DepartmentMember.role == "admin", User.role == 1)
        .subquery()
    )

    result = await db.execute(
        select(
            Department.id,
            Organization.name.label("organization_name"),
            Department.team_name,
            supervisor_sq.c.admin_username,
        )
        .join(Organization, Department.org_id == Organization.id)
        .outerjoin(supervisor_sq, supervisor_sq.c.department_id == Department.id)
        .where(supervisor_exists)
        .order_by(Organization.name, Department.team_name)
    )
    rows = result.all()
    items = [
        {
            "id": str(r.id),
            "organization_name": r.organization_name,
            "team_name": r.team_name,
            "admin_username": r.admin_username,
        }
        for r in rows
    ]
    return ApiResponse(data={"items": items})


@router.get("", response_model=ApiResponse, summary="所有部门列表")
async def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询部门列表，附带成员数和节点数
    stmt = (
        select(
            Department,
            Organization.name.label("organization_name"),
            func.count(DepartmentMember.id.distinct()).label("member_count"),
        )
        .join(Organization, Department.org_id == Organization.id)
        .outerjoin(DepartmentMember, DepartmentMember.department_id == Department.id)
        .group_by(Department.id, Organization.name)
        .order_by(Department.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()

    # 单独查节点数
    node_count_stmt = (
        select(Node.department_id, func.count(Node.id))
        .where(Node.status != NodeStatus.ARCHIVED.value)
        .group_by(Node.department_id)
    )
    nc_result = await db.execute(node_count_stmt)
    node_counts = dict(nc_result.all())

    data = []
    for dept, organization_name, member_count in rows:
        data.append({
            "id": str(dept.id),
            "organization_name": organization_name,
            "team_name": dept.team_name,
            "description": dept.description,
            "owner_id": str(dept.owner_id),
            "member_count": member_count,
            "node_count": node_counts.get(dept.id, 0),
            "created_at": dept.created_at.isoformat(),
        })

    total_stmt = select(func.count(Department.id))
    total = (await db.execute(total_stmt)).scalar() or 0

    return ApiResponse(data={"items": data, "total": total})


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED, summary="创建部门")
async def create_department(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 仅超级管理员(0)和主管(1)可创建部门
    if current_user.role > 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅主管及以上身份可创建部门")

    # 查找或创建 Organization
    org_result = await db.execute(
        select(Organization).where(Organization.name == payload.org_name)
    )
    org = org_result.scalar_one_or_none()
    if org is None:
        org = Organization(name=payload.org_name)
        db.add(org)
        await db.flush()

    # 检查同一组织下团队名唯一
    existing = await db.execute(
        select(Department).where(
            Department.org_id == org.id,
            Department.team_name == payload.team_name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该组织下已存在同名团队")

    dept = Department(
        org_id=org.id,
        team_name=payload.team_name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(dept)
    await db.flush()

    # 创建者自动成为管理员
    db.add(DepartmentMember(department_id=dept.id, user_id=current_user.id, role="admin"))
    await db.commit()
    await db.refresh(dept)

    return ApiResponse(
        data={"id": str(dept.id), "organization_name": org.name, "team_name": dept.team_name},
        message="部门已创建",
    )


@router.get("/{dept_id}", response_model=ApiResponse, summary="部门详情")
async def get_department(
    dept_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Department)
        .where(Department.id == dept_id)
        .options(
            selectinload(Department.organization),
            selectinload(Department.members).selectinload(DepartmentMember.user),
        )
    )
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 获取部门内的节点
    nodes_stmt = (
        select(Node)
        .where(Node.department_id == dept_id, Node.status != NodeStatus.ARCHIVED.value)
        .options(selectinload(Node.tags))
        .order_by(Node.updated_at.desc())
        .limit(100)
    )
    nodes_result = await db.execute(nodes_stmt)
    nodes = nodes_result.scalars().all()

    # 获取创建者信息
    owner_result = await db.execute(select(User).where(User.id == dept.owner_id))
    owner = owner_result.scalar_one_or_none()

    # 统计数据
    from backend.models.node import NodeInvocationLog
    node_ids = [n.id for n in nodes]
    total_invocations = 0
    if node_ids:
        inv_count = await db.execute(
            select(func.count(NodeInvocationLog.id)).where(NodeInvocationLog.node_id.in_(node_ids))
        )
        total_invocations = inv_count.scalar() or 0

    status_counts = {}
    for n in nodes:
        status_counts[n.status] = status_counts.get(n.status, 0) + 1

    type_counts = {}
    for n in nodes:
        type_counts[n.visibility] = type_counts.get(n.visibility, 0) + 1

    return ApiResponse(data={
        "id": str(dept.id),
        "organization_name": dept.organization.name if dept.organization else None,
        "team_name": dept.team_name,
        "description": dept.description,
        "owner_id": str(dept.owner_id),
        "owner_username": owner.username if owner else None,
        "created_at": dept.created_at.isoformat(),
        "stats": {
            "node_count": len(nodes),
            "member_count": len(dept.members),
            "total_invocations": total_invocations,
            "status_distribution": status_counts,
            "type_distribution": type_counts,
        },
        "members": [
            {
                "user_id": str(m.user_id),
                "username": m.user.username,
                "email": m.user.email,
                "role": m.role,
                "joined_at": m.joined_at.isoformat(),
            }
            for m in dept.members
        ],
        "nodes": [
            {
                "id": str(n.id),
                "name": n.name,
                "display_name": n.display_name,
                "type": n.visibility,
                "status": n.status,
                "tags": [t.tag for t in n.tags],
                "created_at": n.created_at.isoformat(),
            }
            for n in nodes
        ],
    })


@router.patch("/{dept_id}", response_model=ApiResponse, summary="更新部门信息")
async def update_department(
    dept_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可修改
    membership = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == dept_id,
            DepartmentMember.user_id == current_user.id,
            DepartmentMember.role == "admin",
            DepartmentMember.status == "active",
        )
    )).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可修改部门信息")

    if payload.team_name is not None:
        dept.team_name = payload.team_name
    if payload.description is not None:
        dept.description = payload.description
    await db.commit()

    return ApiResponse(data={"id": str(dept.id), "team_name": dept.team_name, "description": dept.description})


@router.post("/{dept_id}/members", response_model=ApiResponse, summary="添加部门成员")
async def add_member(
    dept_id: uuid.UUID,
    payload: MemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 验证部门存在
    dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可添加成员
    admin_check = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == dept_id,
            DepartmentMember.user_id == current_user.id,
            DepartmentMember.role == "admin",
            DepartmentMember.status == "active",
        )
    )).scalar_one_or_none()
    if admin_check is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可添加成员")

    # 查找目标用户
    target_user = (await db.execute(
        select(User).where(User.username == payload.username)
    )).scalar_one_or_none()
    if target_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"用户 {payload.username} 不存在")

    # role="admin" 额外校验
    if payload.role == "admin":
        if target_user.role != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只有平台主管（role=1）才能担任部门管理员",
            )
        existing_supervisor = (await db.execute(
            select(DepartmentMember)
            .join(User, DepartmentMember.user_id == User.id)
            .where(
                DepartmentMember.department_id == dept_id,
                DepartmentMember.role == "admin",
                User.role == 1,
            )
        )).scalar_one_or_none()
        if existing_supervisor is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该部门已有主管")

    # 检查是否已是成员
    existing = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == dept_id,
            DepartmentMember.user_id == target_user.id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该用户已是部门成员")

    db.add(DepartmentMember(department_id=dept_id, user_id=target_user.id, role=payload.role))
    await db.commit()

    return ApiResponse(message=f"已将 {payload.username} 添加为部门{payload.role}")


@router.delete("/{dept_id}/members/{user_id}", response_model=ApiResponse, summary="移除部门成员")
async def remove_member(
    dept_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dept = (await db.execute(select(Department).where(Department.id == dept_id))).scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部门不存在")

    # 仅管理员可操作
    admin_check = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == dept_id,
            DepartmentMember.user_id == current_user.id,
            DepartmentMember.role == "admin",
            DepartmentMember.status == "active",
        )
    )).scalar_one_or_none()
    if admin_check is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅部门管理员可移除成员")

    # 不能移除部门创建者
    if user_id == dept.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能移除部门创建者")

    membership = (await db.execute(
        select(DepartmentMember).where(
            DepartmentMember.department_id == dept_id,
            DepartmentMember.user_id == user_id,
        )
    )).scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不是部门成员")

    await db.delete(membership)
    await db.commit()

    return ApiResponse(message="成员已移除")
