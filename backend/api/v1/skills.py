"""Skill 技能集 API 路由。

提供技能集的 CRUD、版本管理、SKILL.md 生成和 ZIP 导出功能。
"""
import io
import uuid
import zipfile

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy import func, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.skill_md_generator import LLMConfig, generate_skill_md
from backend.core.skill_registry import SkillRegistry
from backend.database.session import get_db
from backend.models.ai_config import UserAIConfig
from backend.models.skill import Skill, SkillVersion
from backend.models.skill_node import SkillNode
from backend.models.user import User
from backend.schemas.response import ApiResponse
from backend.schemas.skill import (
    SkillCreate,
    SkillDetailResponse,
    SkillNodeCreate,
    SkillNodeItem,
    SkillNodeUpdate,
    SkillResponse,
    SkillUpdate,
    SkillVersionCreate,
    SkillVersionResponse,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/skills", tags=["Skills"])

_SETUP_MD = """\
# NodeVault Skill 环境配置

## 所需环境变量

```bash
# NodeVault 服务地址
export NODEVAULT_URL=https://your-nodevault-host

# NodeVault API Key（在 NodeVault 平台 → 个人设置 → API Keys 中生成）
export NODEVAULT_API_KEY=nv_xxxxxxxxxxxxxxxxxxxx
```

## 验证连通性

```bash
curl -H "Authorization: Bearer $NODEVAULT_API_KEY" \\
     "$NODEVAULT_URL/api/v1/health"
```

响应 `{"status": "ok"}` 即表示配置成功。
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skill_to_response(skill: Skill, node_count: int = 0, latest_version: str | None = None) -> SkillResponse:
    return SkillResponse(
        id=skill.id,
        name=skill.name,
        display_name=skill.display_name,
        description=skill.description,
        namespace_id=skill.namespace_id,
        owner_id=skill.owner_id,
        status=skill.status,
        is_system=skill.is_system,
        is_stale=skill.is_stale,
        node_count=node_count,
        latest_version=latest_version,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
    )


def _skill_to_detail(skill: Skill) -> SkillDetailResponse:
    default_ver = next(
        (v for v in (skill.versions or []) if v.is_default),
        skill.versions[0] if skill.versions else None,
    )
    nodes = [
        SkillNodeItem(
            id=sn.node.id,
            name=sn.node.name,
            display_name=sn.node.display_name,
            usage_hint=sn.usage_hint,
            category_name=sn.node.category_rel.display_name if sn.node.category_rel else None,
        )
        for sn in (skill.skill_nodes or [])
        if sn.node is not None
    ]
    versions = [_version_to_response(v) for v in (skill.versions or [])]
    return SkillDetailResponse(
        id=skill.id,
        name=skill.name,
        display_name=skill.display_name,
        description=skill.description,
        namespace_id=skill.namespace_id,
        owner_id=skill.owner_id,
        status=skill.status,
        is_system=skill.is_system,
        is_stale=skill.is_stale,
        node_count=len(nodes),
        latest_version=default_ver.version if default_ver else None,
        created_at=skill.created_at,
        updated_at=skill.updated_at,
        nodes=nodes,
        versions=versions,
    )


def _version_to_response(ver: SkillVersion) -> SkillVersionResponse:
    return SkillVersionResponse(
        id=ver.id,
        skill_id=ver.skill_id,
        version=ver.version,
        skill_md=ver.skill_md,
        node_snapshot=ver.node_snapshot,
        release_notes=ver.release_notes,
        is_default=ver.is_default,
        created_at=ver.created_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ApiResponse)
async def list_skills(
    namespace_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    items = await registry.list_skills(namespace_id=namespace_id, user=current_user, skip=skip, limit=limit)
    responses = [
        _skill_to_response(skill, node_count=node_count, latest_version=latest_version)
        for skill, node_count, latest_version in items
    ]
    return ApiResponse(data=responses)


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    payload: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    try:
        skill = await registry.create_skill(payload, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(data=_skill_to_detail(skill), message="技能集创建成功")


@router.get("/{skill_id}", response_model=ApiResponse)
async def get_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    skill = await registry.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")
    return ApiResponse(data=_skill_to_detail(skill))


@router.patch("/{skill_id}", response_model=ApiResponse)
async def update_skill(
    skill_id: uuid.UUID,
    payload: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    try:
        skill = await registry.update_skill(skill_id, payload, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return ApiResponse(data=_skill_to_detail(skill))


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    # Protect system skills from deletion
    result = await db.execute(sa_select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")
    if skill.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="系统技能集不可删除")

    registry = SkillRegistry(db)
    try:
        await registry.archive_skill(skill_id, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{skill_id}/versions", response_model=ApiResponse)
async def list_versions(
    skill_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    skill = await registry.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")
    versions = await registry.list_versions(skill_id)
    return ApiResponse(data=[_version_to_response(v) for v in versions])


@router.post("/{skill_id}/versions", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    skill_id: uuid.UUID,
    payload: SkillVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = SkillRegistry(db)
    try:
        version = await registry.create_version(skill_id, payload, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ApiResponse(data=_version_to_response(version), message="版本发布成功")


class _GenerateRequest(BaseModel):
    config_id: uuid.UUID | None = None


@router.post("/{skill_id}/generate", response_model=ApiResponse)
async def generate_skill_md_endpoint(
    skill_id: uuid.UUID,
    payload: _GenerateRequest = Body(default_factory=_GenerateRequest),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """调用 LLM 生成 SKILL.md 草稿。可选传 config_id 指定 AI 提供商配置。"""
    registry = SkillRegistry(db)
    skill = await registry.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")

    llm_config: LLMConfig | None = None
    if payload.config_id is not None:
        result_row = await db.execute(
            sa_select(UserAIConfig).where(
                UserAIConfig.id == payload.config_id,
                UserAIConfig.user_id == current_user.id,
            )
        )
        ai_cfg = result_row.scalar_one_or_none()
        if ai_cfg is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI 配置不存在")
        llm_config = LLMConfig(
            provider=ai_cfg.provider,
            model=ai_cfg.model,
            api_key=ai_cfg.api_key,
            base_url=ai_cfg.base_url,
        )

    try:
        result = await generate_skill_md(db, skill_id, llm_config=llm_config)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("skill_md_generation_failed", skill_id=str(skill_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM 调用失败：{str(e)}",
        )
    return ApiResponse(data=result, message="SKILL.md 草稿已生成")


@router.get("/{skill_id}/export")
async def export_skill_zip(
    skill_id: uuid.UUID,
    version: str | None = Query(None, description="指定版本号，默认使用默认版本"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """导出技能集 ZIP 包（SKILL.md + references/setup.md）。"""
    registry = SkillRegistry(db)
    skill = await registry.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")

    # Select version
    if version:
        skill_ver = next(
            (v for v in (skill.versions or []) if v.version == version),
            None,
        )
        if skill_ver is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"版本 {version} 不存在")
    else:
        skill_ver = next(
            (v for v in (skill.versions or []) if v.is_default),
            skill.versions[0] if skill.versions else None,
        )
        if skill_ver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="该技能集暂无已发布版本，请先发布一个版本",
            )

    # Build zip in memory
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SKILL.md", skill_ver.skill_md)
        zf.writestr("references/setup.md", _SETUP_MD)

    buf.seek(0)
    filename = f"{skill.name}-{skill_ver.version}.zip"
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Skill-Node M2M Management
# ---------------------------------------------------------------------------

@router.post("/{skill_id}/nodes", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def add_skill_node(
    skill_id: uuid.UUID,
    payload: SkillNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """向技能集添加节点（创建 SkillNode 关联）。"""
    registry = SkillRegistry(db)
    skill = await registry.get_skill(skill_id)
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="技能集不存在")

    # Check duplicate
    existing = await db.execute(
        sa_select(SkillNode).where(
            SkillNode.skill_id == skill_id,
            SkillNode.node_id == payload.node_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该节点已在此技能集中")

    # Verify node exists
    from backend.models.node import Node
    node_result = await db.execute(sa_select(Node).where(Node.id == payload.node_id))
    if node_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="节点不存在")

    max_sort = await db.execute(
        sa_select(func.coalesce(func.max(SkillNode.sort_order), 0)).where(
            SkillNode.skill_id == skill_id,
        )
    )
    next_sort = max_sort.scalar() + 1

    sn = SkillNode(
        skill_id=skill_id,
        node_id=payload.node_id,
        usage_hint=payload.usage_hint,
        sort_order=next_sort,
    )
    db.add(sn)

    # Mark skill as stale
    skill.is_stale = True
    await db.commit()
    await db.refresh(sn)

    return ApiResponse(
        data={"id": str(sn.id), "skill_id": str(sn.skill_id), "node_id": str(sn.node_id),
              "usage_hint": sn.usage_hint, "sort_order": sn.sort_order},
        message="节点已添加到技能集",
    )


@router.delete("/{skill_id}/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill_node(
    skill_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """从技能集移除节点。"""
    result = await db.execute(
        sa_select(SkillNode).where(
            SkillNode.skill_id == skill_id,
            SkillNode.node_id == node_id,
        )
    )
    sn = result.scalar_one_or_none()
    if sn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该节点不在此技能集中")

    await db.delete(sn)

    # Mark skill as stale
    skill_result = await db.execute(sa_select(Skill).where(Skill.id == skill_id))
    skill = skill_result.scalar_one_or_none()
    if skill:
        skill.is_stale = True

    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{skill_id}/nodes/{node_id}", response_model=ApiResponse)
async def update_skill_node(
    skill_id: uuid.UUID,
    node_id: uuid.UUID,
    payload: SkillNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    """更新技能集中某节点的 usage_hint。"""
    result = await db.execute(
        sa_select(SkillNode).where(
            SkillNode.skill_id == skill_id,
            SkillNode.node_id == node_id,
        )
    )
    sn = result.scalar_one_or_none()
    if sn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该节点不在此技能集中")

    if payload.usage_hint is not None:
        sn.usage_hint = payload.usage_hint

    # Mark skill as stale
    skill_result = await db.execute(sa_select(Skill).where(Skill.id == skill_id))
    skill = skill_result.scalar_one_or_none()
    if skill:
        skill.is_stale = True

    await db.commit()
    await db.refresh(sn)

    return ApiResponse(
        data={"id": str(sn.id), "skill_id": str(sn.skill_id), "node_id": str(sn.node_id),
              "usage_hint": sn.usage_hint, "sort_order": sn.sort_order},
        message="usage_hint 已更新",
    )
