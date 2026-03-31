import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.registry import NodeRegistry
from backend.core.search import NodeSearchIndex
from backend.core.versioning import VersionCompatibilityChecker
from backend.database.session import get_db
from backend.models.node import Node, NodeVersion
from backend.models.user import User
from backend.schemas.node import (
    CategoryBrief,
    NodeCreate,
    NodeDetailResponse,
    NodeResponse,
    NodeUpdate,
    NodeVersionCreate,
    NodeVersionResponse,
    NodeVersionUpdate,
)
from backend.schemas.response import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/nodes", tags=["Nodes"])


def _node_to_response(node: Node) -> NodeResponse:
    cat_brief = None
    if node.category_rel:
        cat_brief = CategoryBrief(id=node.category_rel.id, display_name=node.category_rel.display_name)

    # Extract credential_id from the default NodeVersion's runtime_config
    credential_id = None
    if node.versions:
        default_ver = next((v for v in node.versions if v.is_default), None)
        if default_ver and default_ver.runtime_config:
            raw_id = default_ver.runtime_config.get("credential_id")
            if raw_id:
                try:
                    import uuid as _uuid
                    credential_id = _uuid.UUID(raw_id)
                except (ValueError, AttributeError):
                    pass

    return NodeResponse(
        id=node.id,
        name=node.name,
        display_name=node.display_name,
        description=node.description,
        category_id=node.category_id,
        category=cat_brief,
        status=node.status,
        visibility=node.visibility,
        department_id=node.department_id,
        department_slug=node.department.slug if node.department else None,
        owner_id=node.owner_id,
        owner_username=node.owner.username if node.owner else None,
        tags=[t.tag for t in node.tags],
        credential_id=credential_id,
        source_credential_id=node.source_credential_id,
        source_path=node.source_path,
        source_service_name=node.source_credential.name if node.source_credential else None,
        created_at=node.created_at,
        updated_at=node.updated_at,
    )


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register_node(
    payload: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeResponse:
    registry = NodeRegistry(db)
    try:
        node = await registry.create_node(payload, owner=current_user)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Node name already exists in this department",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Sync to search index (non-blocking)
    try:
        NodeSearchIndex().upsert_node(
            {
                "id": str(node.id),
                "name": node.name,
                "display_name": node.display_name,
                "description": node.description,
                "category": node.category_rel.display_name if node.category_rel else "",
                "status": node.status,
                "department_id": str(node.department_id),
                "invocation_count": node.invocation_count,
                "tags": [t.tag for t in node.tags],
            }
        )
    except Exception as exc:
        logger.warning("search_index_sync_failed", node_id=str(node.id), error=str(exc))

    return ApiResponse(data=_node_to_response(node).model_dump(), message="Node 已注册")


@router.post("/batch", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def batch_create_nodes(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Batch create multiple Nodes in a single atomic transaction.

    Body: { department_id, base_url, credential_id?, items: [{name, endpoint, method, ...}] }
    """
    department_id = payload.get("department_id")
    if not department_id:
        raise HTTPException(status_code=400, detail="department_id required")

    items = payload.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="items required")

    registry = NodeRegistry(db)
    try:
        nodes = await registry.batch_register(
            items=[{**it, "base_url": payload.get("base_url", "")} for it in items],
            department_id=uuid.UUID(department_id),
            owner=current_user,
            credential_id=uuid.UUID(payload["credential_id"]) if payload.get("credential_id") else None,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # 同步到搜索索引
    search_index = NodeSearchIndex()
    for n in nodes:
        try:
            search_index.upsert_node({
                "id": str(n.id),
                "name": n.name,
                "display_name": n.display_name,
                "description": n.description,
                "category": n.category_rel.display_name if n.category_rel else "",
                "status": n.status,
                "department_id": str(n.department_id),
                "invocation_count": n.invocation_count,
                "tags": [t.tag for t in n.tags],
            })
        except Exception as exc:
            logger.warning("search_index_sync_failed", node_id=str(n.id), error=str(exc))

    return ApiResponse(
        data={"imported": len(nodes), "node_ids": [str(n.id) for n in nodes]},
        message=f"{len(nodes)} 个 Node 批量创建成功",
    )


@router.get("", response_model=ApiResponse)
async def list_nodes(
    category_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    tag: str | None = Query(None),
    mine: bool = Query(False, description="仅返回当前用户自己的节点"),
    source_credential_id: uuid.UUID | None = Query(None, description="按来源服务过滤"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NodeResponse]:
    registry = NodeRegistry(db)
    nodes = await registry.list_nodes(
        owner=current_user,
        category_id=category_id,
        status=status_filter,
        tag=tag,
        mine_only=mine,
        source_credential_id=source_credential_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse(data=[_node_to_response(n).model_dump() for n in nodes])


@router.get("/{node_id}", response_model=ApiResponse)
async def get_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeDetailResponse:
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    resp = _node_to_response(node)
    detail_resp = NodeDetailResponse(
        **resp.model_dump(),
        versions=[NodeVersionResponse.model_validate(v) for v in node.versions],
    )
    return ApiResponse(data=detail_resp.model_dump())


@router.patch("/{node_id}", response_model=ApiResponse)
async def update_node(
    node_id: uuid.UUID,
    payload: NodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NodeResponse:
    registry = NodeRegistry(db)
    try:
        # Use model_fields_set to detect explicitly-passed fields (including null credential_id for unbind)
        update_data = payload.model_dump(exclude_none=True)
        if "credential_id" in payload.model_fields_set:
            update_data["credential_id"] = payload.credential_id
        node = await registry.update_node(
            node_id, update_data, owner=current_user
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Sync updated metadata to search index
    try:
        NodeSearchIndex().upsert_node(
            {
                "id": str(node.id),
                "name": node.name,
                "display_name": node.display_name,
                "description": node.description,
                "category": node.category_rel.display_name if node.category_rel else "",
                "status": node.status,
                "department_id": str(node.department_id),
                "invocation_count": node.invocation_count,
                "tags": [t.tag for t in node.tags],
            }
        )
    except Exception as exc:
        logger.warning("search_index_sync_failed", node_id=str(node_id), error=str(exc))

    return ApiResponse(data=_node_to_response(node).model_dump())


@router.delete("/{node_id}", response_model=ApiResponse)
async def delete_node(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = NodeRegistry(db)
    try:
        await registry.archive_node(node_id, owner=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # Remove from search index
    try:
        NodeSearchIndex().delete_node(str(node_id))
    except Exception as exc:
        logger.warning("search_index_delete_failed", node_id=str(node_id), error=str(exc))

    return ApiResponse(message="Node 已删除")


@router.get("/{node_id}/versions", response_model=ApiResponse)
async def list_versions(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NodeVersionResponse]:
    registry = NodeRegistry(db)
    versions = await registry.list_versions(node_id)
    return ApiResponse(data=[NodeVersionResponse.model_validate(v).model_dump() for v in versions])


@router.post(
    "/{node_id}/versions",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse,
    summary="发布新版本",
    description="发布新版本时自动运行兼容性检查，结果附加在响应的 `compatibility` 字段中。",
)
async def create_version(
    node_id: uuid.UUID,
    payload: NodeVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = NodeRegistry(db)

    # Run compatibility check against current default version
    compatibility: dict = {"checked": False}
    current_default = await registry.get_version(node_id)
    if current_default is not None:
        checker = VersionCompatibilityChecker()
        is_compatible, issues = checker.check_compatibility(
            current_default.input_schema, payload.input_schema
        )
        has_new_features = bool(
            set(payload.input_schema.get("properties", {}).keys())
            - set(current_default.input_schema.get("properties", {}).keys())
        )
        suggested = checker.suggest_version_bump(
            current_default.version, is_compatible, has_new_features
        )
        compatibility = {
            "checked": True,
            "is_compatible": is_compatible,
            "breaking_changes": [i for i in issues if i.startswith("BREAKING")],
            "warnings": [i for i in issues if i.startswith("WARNING")],
            "suggested_version": suggested,
        }

    try:
        version = await registry.create_version(node_id, payload, owner=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    resp = NodeVersionResponse.model_validate(version)
    # Attach compatibility info via model extra
    resp_dict = resp.model_dump()
    resp_dict["compatibility"] = compatibility
    return ApiResponse(data=resp_dict)


@router.patch(
    "/{node_id}/versions/{version}",
    response_model=ApiResponse,
    summary="修改版本",
    description="修改已有版本的 schema、runtime 配置和变更日志。",
    responses={
        403: {"description": "非本部门成员"},
        404: {"description": "节点或版本不存在"},
    },
)
async def update_version(
    node_id: uuid.UUID,
    version: str,
    payload: NodeVersionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = NodeRegistry(db)
    try:
        ver = await registry.update_version(node_id, version, payload, owner=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail)
    return ApiResponse(data=NodeVersionResponse.model_validate(ver).model_dump())


@router.delete(
    "/{node_id}/versions/{version}",
    response_model=ApiResponse,
    summary="删除版本",
    description="永久删除指定版本。不允许删除当前默认版本；只有节点所有者可操作。",
    responses={
        400: {"description": "不允许删除默认版本"},
        403: {"description": "非节点所有者"},
        404: {"description": "节点或版本不存在"},
    },
)
async def delete_version(
    node_id: uuid.UUID,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    registry = NodeRegistry(db)
    try:
        await registry.delete_version(node_id, version, owner=current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        detail = str(exc)
        code = status.HTTP_404_NOT_FOUND if "不存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=detail)
    return ApiResponse(message=f"版本 {version} 已删除")


@router.post(
    "/{node_id}/versions/{version}/set-default",
    summary="版本回滚",
    description="将指定版本设为该 Node 的默认版本（版本回滚）。",
    responses={
        403: {"description": "非 Node 所有者"},
        404: {"description": "Node 或版本不存在"},
    },
)
async def set_default_version(
    node_id: uuid.UUID,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    try:
        await registry._check_namespace_permission(node, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    target = await db.execute(
        select(NodeVersion).where(
            NodeVersion.node_id == node_id, NodeVersion.version == version
        )
    )
    target_version = target.scalar_one_or_none()
    if target_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"版本 {version} 不存在")

    # Reset all versions' is_default, then set the target
    try:
        await db.execute(
            update(NodeVersion).where(NodeVersion.node_id == node_id).values(is_default=False)
        )
        await db.execute(
            update(NodeVersion)
            .where(NodeVersion.node_id == node_id, NodeVersion.version == version)
            .values(is_default=True)
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="并发写入冲突，请重试",
        )

    return ApiResponse(data={"node_id": str(node_id), "default_version": version})


@router.post(
    "/{node_id}/versions/{version}/deprecate",
    summary="弃用版本",
    description="将指定版本标记为 deprecated。不允许弃用当前默认版本。",
    responses={
        400: {"description": "不允许弃用当前默认版本"},
        403: {"description": "非 Node 所有者"},
        404: {"description": "Node 或版本不存在"},
    },
)
async def deprecate_version(
    node_id: uuid.UUID,
    version: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="节点不存在")
    try:
        await registry._check_namespace_permission(node, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    target = await db.execute(
        select(NodeVersion).where(
            NodeVersion.node_id == node_id, NodeVersion.version == version
        )
    )
    target_version = target.scalar_one_or_none()
    if target_version is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"版本 {version} 不存在")
    if target_version.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能弃用当前默认版本，请先将其他版本设为默认版本后再操作。",
        )

    await db.execute(
        update(NodeVersion)
        .where(NodeVersion.node_id == node_id, NodeVersion.version == version)
        .values(is_deprecated=True)
    )
    await db.commit()

    return ApiResponse(data={"node_id": str(node_id), "version": version, "status": "deprecated"})


@router.get(
    "/{node_id}/changelog",
    summary="版本变更记录",
    description="返回该 Node 所有版本的发布记录，按版本发布时间倒序排列。",
)
async def get_changelog(
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    node = await NodeRegistry(db).get_node(node_id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    result = await db.execute(
        select(NodeVersion)
        .where(NodeVersion.node_id == node_id)
        .order_by(NodeVersion.created_at.desc())
    )
    versions = list(result.scalars().all())
    return ApiResponse(data=[
        {
            "version": v.version,
            "created_at": v.created_at.isoformat(),
            "is_default": v.is_default,
            "is_deprecated": v.is_deprecated,
            "changelog": v.changelog,
        }
        for v in versions
    ])
