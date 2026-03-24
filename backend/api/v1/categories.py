"""Category CRUD endpoints — role == 0 (超管) can create/update/delete."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user, get_superadmin_user
from backend.database.session import get_db
from backend.models.category import Category
from backend.models.user import User
from backend.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[CategoryRead]:
    result = await db.execute(
        select(Category).order_by(Category.sort_order, Category.created_at)
    )
    return [CategoryRead.model_validate(c) for c in result.scalars().all()]


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> CategoryRead:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    return CategoryRead.model_validate(cat)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_superadmin_user),
) -> CategoryRead:
    # Check name uniqueness
    existing = await db.execute(select(Category).where(Category.name == payload.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="分类名称已存在")

    cat = Category(
        name=payload.name,
        display_name=payload.display_name,
        icon=payload.icon,
        sort_order=payload.sort_order,
        is_default=False,
        created_by=user.id,
    )
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryRead.model_validate(cat)


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_superadmin_user),
) -> CategoryRead:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")

    if payload.display_name is not None:
        cat.display_name = payload.display_name
    if payload.icon is not None:
        cat.icon = payload.icon
    if payload.sort_order is not None:
        cat.sort_order = payload.sort_order

    await db.commit()
    await db.refresh(cat)
    return CategoryRead.model_validate(cat)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_superadmin_user),
) -> None:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if cat is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.is_default:
        raise HTTPException(status_code=400, detail="不能删除系统默认分类")

    # Check if any nodes still reference this category
    from backend.models.node import Node
    count_result = await db.execute(
        select(func.count()).select_from(Node).where(Node.category_id == category_id)
    )
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="该分类下仍有节点，请先移动或删除节点")

    await db.delete(cat)
    await db.commit()
