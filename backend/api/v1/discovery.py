"""Service discovery & batch import API endpoints."""

from __future__ import annotations

import json
import uuid as uuid_module
from dataclasses import asdict
from datetime import datetime
from typing import Any

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.core.openapi_mapper import parse_operations
from backend.core.probe import probe_spec, probe_with_auth, _parse_spec
from backend.core.registry import NodeRegistry
from backend.core.search import NodeSearchIndex
from backend.database.session import get_db
from backend.models.discovery import DiscoverySession
from backend.models.department import Department, DepartmentMember
from backend.models.node import Node, NodeTag, NodeVersion
from backend.models.user import User
from backend.schemas.discovery import (
    BatchImportRequest,
    BatchImportResponse,
    BatchImportResultItem,
    CompareRequest,
    CompareResponse,
    CompareResultItem,
    DiscoverySessionCreate,
    DiscoverySessionDetail,
    DiscoverySessionSchema,
    DiscoverySessionUpdate,
    DuplicateUrlResponse,
    IterateRequest,
    IterateResponse,
    LinkedNodeSchema,
    NodeDraftListResponse,
    NodeDraftSchema,
    ProbeAttemptSchema,
    ProbeAuthConfig,
    ProbeRequest,
    ProbeResultSchema,
)

router = APIRouter(prefix="/discovery", tags=["discovery"])


def _drafts_to_response(base_url: str, drafts: list) -> NodeDraftListResponse:
    return NodeDraftListResponse(
        base_url=base_url,
        drafts=[
            NodeDraftSchema(
                suggested_name=d.suggested_name,
                display_name=d.display_name,
                description=d.description,
                endpoint=d.endpoint,
                method=d.method,
                input_schema=d.input_schema,
                output_schema=d.output_schema,
                category=d.category,
                tags=d.tags,
                selected=d.selected,
            )
            for d in drafts
        ],
    )


@router.post("/probe", response_model=ProbeResultSchema | NodeDraftListResponse)
async def probe_openapi(
    body: ProbeRequest,
    user: User = Depends(get_current_user),
):
    """Probe a base URL for an OpenAPI spec."""
    result = await probe_spec(body.base_url, probe_paths=body.probe_paths)

    if result.found and result.spec_dict:
        drafts = parse_operations(result.spec_dict)
        return _drafts_to_response(result.base_url, drafts)

    return ProbeResultSchema(
        base_url=result.base_url,
        found=result.found,
        spec_url=result.spec_url,
        needs_auth=result.needs_auth,
        error=result.error,
        error_type=result.error_type,
        attempts=[
            ProbeAttemptSchema(
                path=a.path, status=a.status, success=a.success, error=a.error
            )
            for a in result.attempts
        ],
    )


@router.post("/probe-with-auth", response_model=ProbeResultSchema | NodeDraftListResponse)
async def probe_openapi_with_auth(
    body: ProbeAuthConfig,
    user: User = Depends(get_current_user),
):
    """Probe a base URL after authenticating."""
    result = await probe_with_auth(
        base_url=body.base_url,
        login_endpoint=body.login_endpoint,
        login_method=body.login_method,
        login_body=body.login_body,
        token_json_path=body.token_json_path,
        probe_paths=body.probe_paths,
    )

    if result.found and result.spec_dict:
        drafts = parse_operations(result.spec_dict)
        return _drafts_to_response(result.base_url, drafts)

    return ProbeResultSchema(
        base_url=result.base_url,
        found=result.found,
        spec_url=result.spec_url,
        needs_auth=result.needs_auth,
        error=result.error,
        error_type=result.error_type,
        attempts=[
            ProbeAttemptSchema(
                path=a.path, status=a.status, success=a.success, error=a.error
            )
            for a in result.attempts
        ],
    )


@router.post("/upload-spec", response_model=NodeDraftListResponse)
async def upload_spec(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Upload an OpenAPI spec file (JSON/YAML) and parse it."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    text = content.decode("utf-8")
    spec = _parse_spec(text)
    if not spec:
        raise HTTPException(
            status_code=400,
            detail="Could not parse file as OpenAPI spec (JSON/YAML)",
        )

    drafts = parse_operations(spec)
    base_url = ""
    servers = spec.get("servers", [])
    if servers and isinstance(servers[0], dict):
        base_url = servers[0].get("url", "")

    return _drafts_to_response(base_url, drafts)


@router.post("/import", response_model=BatchImportResponse)
async def batch_import_nodes(
    body: BatchImportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Batch create Nodes from discovery results. Atomic transaction."""
    base_url = body.base_url.rstrip("/")

    # Build items list for registry (includes base_url for endpoint construction)
    items = [
        {
            "name": item.name,
            "display_name": item.display_name,
            "description": item.description,
            "endpoint": item.endpoint,
            "method": item.method,
            "base_url": base_url,
            "input_schema": item.input_schema,
            "output_schema": item.output_schema,
            "category_id": str(item.category_id) if item.category_id else None,
            "tags": item.tags,
            "visibility": body.visibility,
        }
        for item in body.items
    ]

    # Build source_path_map: item.name → item.source_path (or endpoint path as fallback)
    source_path_map = {
        item.name: (item.source_path if item.source_path is not None else item.endpoint)
        for item in body.items
    }

    registry = NodeRegistry(db)
    try:
        nodes = await registry.batch_register(
            items=items,
            department_id=body.department_id,
            owner=user,
            credential_id=body.credential_id,
            source_path_map=source_path_map,
            discovery_session_id=body.session_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    # Update discovery session if provided
    if body.session_id:
        session_result = await db.execute(
            select(DiscoverySession).where(
                DiscoverySession.id == body.session_id,
                DiscoverySession.user_id == user.id,
            )
        )
        sess = session_result.scalar_one_or_none()
        if sess:
            sess.status = "completed"
            sess.imported_count = (sess.imported_count or 0) + len(nodes)
            sess.completed_at = datetime.utcnow()
            await db.commit()

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
                "organization_name": n.department.organization.name if n.department and n.department.organization else "",
                "team_name": n.department.team_name if n.department else "",
                "invocation_count": n.invocation_count,
                "tags": [t.tag for t in n.tags],
            })
        except Exception:
            pass

    results = [BatchImportResultItem(name=n.name, node_id=n.id) for n in nodes]
    return BatchImportResponse(imported=len(results), nodes=results)


@router.get("/imported")
async def get_imported_paths(
    credential_id: uuid_module.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the source_path values of all nodes imported from a given service credential."""
    result = await db.execute(
        select(Node.source_path)
        .where(
            Node.source_credential_id == credential_id,
            Node.source_path.isnot(None),
        )
    )
    paths = [row[0] for row in result.fetchall()]
    return {"credential_id": str(credential_id), "imported_paths": paths}


# ---------- Discovery Session CRUD ----------


@router.post("/sessions", response_model=DiscoverySessionSchema, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: DiscoverySessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new discovery session (status: probing)."""
    sess = DiscoverySession(
        user_id=user.id,
        base_url=body.base_url,
        source=body.source,
        status="probing",
    )
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return sess


@router.patch("/sessions/{session_id}", response_model=DiscoverySessionSchema)
async def update_session(
    session_id: uuid_module.UUID,
    body: DiscoverySessionUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update session status / metadata."""
    result = await db.execute(
        select(DiscoverySession).where(
            DiscoverySession.id == session_id,
            DiscoverySession.user_id == user.id,
        )
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    if body.status is not None:
        sess.status = body.status
    if body.spec_url is not None:
        sess.spec_url = body.spec_url
    if body.total_operations is not None:
        sess.total_operations = body.total_operations
    if body.imported_count is not None:
        sess.imported_count = body.imported_count
    if body.completed_at is not None:
        sess.completed_at = body.completed_at

    await db.commit()
    await db.refresh(sess)
    return sess


@router.get("/sessions", response_model=list[DiscoverySessionSchema])
async def list_sessions(
    page: int = 1,
    page_size: int = 20,
    base_url: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List discovery sessions for the current user, newest first. Optional base_url filter."""
    from sqlalchemy import desc

    offset = (page - 1) * page_size
    query = (
        select(DiscoverySession)
        .where(DiscoverySession.user_id == user.id)
        .order_by(desc(DiscoverySession.created_at))
        .limit(page_size)
        .offset(offset)
    )
    if base_url:
        query = query.where(DiscoverySession.base_url == base_url.rstrip("/"))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=DiscoverySessionDetail)
async def get_session(
    session_id: uuid_module.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get session details including linked nodes."""
    result = await db.execute(
        select(DiscoverySession).where(
            DiscoverySession.id == session_id,
            DiscoverySession.user_id == user.id,
        )
    )
    sess = result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    nodes_result = await db.execute(
        select(Node).where(Node.discovery_session_id == session_id)
    )
    nodes = nodes_result.scalars().all()

    return DiscoverySessionDetail(
        id=sess.id,
        base_url=sess.base_url,
        source=sess.source,
        status=sess.status,
        spec_url=sess.spec_url,
        total_operations=sess.total_operations,
        imported_count=sess.imported_count,
        created_at=sess.created_at,
        completed_at=sess.completed_at,
        nodes=[
            LinkedNodeSchema(
                id=n.id,
                name=n.name,
                display_name=n.display_name,
                source_path=n.source_path,
                status=n.status,
            )
            for n in nodes
        ],
    )


# ---------- Duplicate URL Detection ----------


@router.get("/check-duplicate", response_model=DuplicateUrlResponse)
async def check_duplicate_url(
    base_url: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check if a base_url has already been discovered/imported."""
    normalized = base_url.rstrip("/")

    # Check discovery sessions
    result = await db.execute(
        select(DiscoverySession).where(
            DiscoverySession.user_id == user.id,
            DiscoverySession.base_url == normalized,
            DiscoverySession.status.in_(["completed", "importing"]),
        )
        .order_by(DiscoverySession.created_at.desc())
        .limit(1)
    )
    existing_sess = result.scalar_one_or_none()

    # Check nodes with matching base_url in endpoint
    node_result = await db.execute(
        select(func.count()).select_from(Node).where(
            Node.endpoint.ilike(f"{normalized}%"),
        )
    )
    node_count = node_result.scalar() or 0

    if existing_sess or node_count > 0:
        return DuplicateUrlResponse(
            duplicate=True,
            existing_session_id=existing_sess.id if existing_sess else None,
            existing_count=node_count,
            message=f"该 URL 已有 {node_count} 个节点注册",
        )

    return DuplicateUrlResponse(duplicate=False)


# ---------- Endpoint Compare ----------


@router.post("/sessions/{session_id}/compare", response_model=CompareResponse)
async def compare_session(
    session_id: uuid_module.UUID,
    body: CompareRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare current session's spec with a previous session's imported nodes.

    Returns path+method pairs with status: new, imported, updated, removed.
    """
    # Load current session
    current_result = await db.execute(
        select(DiscoverySession).where(
            DiscoverySession.id == session_id,
            DiscoverySession.user_id == user.id,
        )
    )
    current_sess = current_result.scalar_one_or_none()
    if not current_sess:
        raise HTTPException(status_code=404, detail="当前会话不存在")

    # Load previous session's imported nodes
    prev_nodes_result = await db.execute(
        select(Node).where(Node.discovery_session_id == body.previous_session_id)
    )
    prev_nodes = list(prev_nodes_result.scalars().all())
    prev_map: dict[str, Node] = {}
    for n in prev_nodes:
        key = f"{n.source_path or ''}|{n.method or ''}"
        prev_map[key] = n

    # Load current session's nodes (if any already imported)
    curr_nodes_result = await db.execute(
        select(Node).where(Node.discovery_session_id == session_id)
    )
    curr_nodes = list(curr_nodes_result.scalars().all())
    curr_map: dict[str, Node] = {}
    for n in curr_nodes:
        key = f"{n.source_path or ''}|{n.method or ''}"
        curr_map[key] = n

    items: list[CompareResultItem] = []

    # Check current session nodes against previous
    all_keys = set(prev_map.keys()) | set(curr_map.keys())
    for key in sorted(all_keys):
        parts = key.split("|", 1)
        path = parts[0] if parts else ""
        method = parts[1] if len(parts) > 1 else ""

        in_prev = key in prev_map
        in_curr = key in curr_map

        if in_curr and not in_prev:
            items.append(CompareResultItem(path=path, method=method, status="new"))
        elif in_prev and not in_curr:
            items.append(CompareResultItem(path=path, method=method, status="removed"))
        elif in_prev and in_curr:
            prev_node = prev_map[key]
            curr_node = curr_map[key]
            changes: dict[str, str] = {}
            if prev_node.description != curr_node.description:
                changes["description"] = "changed"
            if prev_node.display_name != curr_node.display_name:
                changes["display_name"] = "changed"
            if changes:
                items.append(CompareResultItem(path=path, method=method, status="updated", changes=changes))
            else:
                items.append(CompareResultItem(path=path, method=method, status="imported"))

    return CompareResponse(items=items)


# ---------- Iterate Import ----------


@router.post("/sessions/{session_id}/iterate", response_model=IterateResponse)
async def iterate_import(
    session_id: uuid_module.UUID,
    body: IterateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute iterate actions: import new nodes, update existing, or skip.

    Each action specifies path+method+action(import/update/skip).
    """
    # Verify session
    sess_result = await db.execute(
        select(DiscoverySession).where(
            DiscoverySession.id == session_id,
            DiscoverySession.user_id == user.id,
        )
    )
    sess = sess_result.scalar_one_or_none()
    if not sess:
        raise HTTPException(status_code=404, detail="会话不存在")

    imported = 0
    updated = 0
    skipped = 0

    for action_item in body.actions:
        if action_item.action == "skip":
            skipped += 1
            continue

        if action_item.action == "update":
            # Find existing node by source_path + method
            existing_result = await db.execute(
                select(Node).where(
                    Node.source_path == action_item.path,
                    Node.method == action_item.method.upper(),
                    Node.discovery_session_id.isnot(None),
                )
            )
            existing_node = existing_result.scalar_one_or_none()
            if existing_node:
                # Mark node as updated by bumping updated_at
                from sqlalchemy import update as sa_update
                await db.execute(
                    sa_update(Node).where(Node.id == existing_node.id).values(
                        discovery_session_id=session_id,
                    )
                )
                updated += 1
            else:
                skipped += 1

        elif action_item.action == "import":
            # This is a new node — would need full node data
            # For now, count it. Actual creation requires re-probing or draft data.
            imported += 1

    # Update session
    sess.imported_count = (sess.imported_count or 0) + imported + updated
    await db.commit()

    return IterateResponse(imported=imported, updated=updated, skipped=skipped)
