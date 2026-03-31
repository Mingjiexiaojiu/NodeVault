import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.department import Department, DepartmentMember
from backend.models.node import Node, NodeInvocationLog, NodeTag, NodeVersion
from backend.models.skill import Skill
from backend.models.skill_node import SkillNode
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.node import NodeCreate, NodeVersionCreate, NodeVersionUpdate


class NodeRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_department(self, owner: User, department_id: uuid.UUID) -> Department:
        """获取部门并验证成员身份。"""
        result = await self.db.execute(
            select(Department).where(Department.id == department_id)
        )
        dept = result.scalar_one_or_none()
        if dept is None:
            raise ValueError("指定的部门不存在")
        membership = await self.db.execute(
            select(DepartmentMember).where(
                DepartmentMember.department_id == department_id,
                DepartmentMember.user_id == owner.id,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise PermissionError("您不是该部门成员，无法在此部门下操作")
        return dept

    async def _get_user_department_ids(self, user: User) -> list[uuid.UUID]:
        """获取用户所属的所有部门 ID（通过成员关系）"""
        result = await self.db.execute(
            select(DepartmentMember.department_id).where(DepartmentMember.user_id == user.id)
        )
        return list(result.scalars().all())

    async def _check_department_permission(self, node: Node, user: User) -> None:
        """检查用户是否是节点所属部门的成员（同部门成员才可写）"""
        membership = await self.db.execute(
            select(DepartmentMember).where(
                DepartmentMember.department_id == node.department_id,
                DepartmentMember.user_id == user.id,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise PermissionError("无权操作此节点：仅本部门成员可修改、删除和管理版本")

    async def create_node(self, payload: NodeCreate, owner: User) -> Node:
        await self._get_department(owner, payload.department_id)

        node = Node(
            name=payload.name,
            department_id=payload.department_id,
            owner_id=owner.id,
            display_name=payload.display_name,
            description=payload.description,
            category_id=payload.category_id,
            status=payload.status.value,
            visibility=payload.visibility.value,
        )
        self.db.add(node)
        await self.db.flush()

        # Build runtime_config dict; include credential_id if provided
        runtime_config = payload.runtime.model_dump(exclude_none=True)
        if payload.runtime.credential_id is not None:
            runtime_config["credential_id"] = str(payload.runtime.credential_id)

        # Create first version
        version = NodeVersion(
            node_id=node.id,
            version=payload.version,
            input_schema=payload.input_schema,
            output_schema=payload.output_schema,
            runtime_config=runtime_config,
            is_default=True,
            created_by=owner.id,
        )
        self.db.add(version)

        # Create tags
        for tag_name in payload.tags:
            self.db.add(NodeTag(node_id=node.id, tag=tag_name))

        await self.db.commit()
        await self.db.refresh(node)
        return await self.get_node(node.id)

    async def batch_register(
        self,
        items: list[dict[str, Any]],
        department_id: uuid.UUID,
        owner: User,
        credential_id: uuid.UUID | None = None,
        source_path_map: dict[str, str] | None = None,
        discovery_session_id: uuid.UUID | None = None,
    ) -> list[Node]:
        """Batch-create Nodes within a single transaction.

        Each item dict: name, endpoint, method, base_url, display_name,
        description, category, tags, input_schema, output_schema, visibility.
        """
        # Verify department membership
        membership = await self.db.execute(
            select(DepartmentMember).where(
                DepartmentMember.department_id == department_id,
                DepartmentMember.user_id == owner.id,
            )
        )
        if membership.scalar_one_or_none() is None:
            raise PermissionError("Not a member of this department")

        # Check name conflicts
        names = [it["name"] for it in items]
        existing = await self.db.execute(
            select(Node.name).where(
                Node.department_id == department_id, Node.name.in_(names)
            )
        )
        conflicts = set(existing.scalars().all())
        if conflicts:
            raise ValueError(
                f"Node names already exist: {', '.join(sorted(conflicts))}"
            )

        created_nodes: list[Node] = []
        for it in items:
            base_url = it.get("base_url", "").rstrip("/")
            endpoint_path = it.get("endpoint", "")
            full_endpoint = f"{base_url}{endpoint_path}" if base_url else endpoint_path

            rc: dict[str, Any] = {
                "endpoint": full_endpoint,
                "method": it.get("method", "POST"),
            }
            if credential_id:
                rc["credential_id"] = str(credential_id)

            node = Node(
                name=it["name"],
                department_id=department_id,
                owner_id=owner.id,
                display_name=it.get("display_name"),
                description=it.get("description"),
                category_id=it.get("category_id"),
                status="active",
                visibility=it.get("visibility", "internal"),
                source_credential_id=credential_id,
                source_path=source_path_map.get(it["name"]) if source_path_map else None,
                discovery_session_id=discovery_session_id,
            )
            self.db.add(node)
            await self.db.flush()

            version = NodeVersion(
                node_id=node.id,
                version="1.0.0",
                input_schema=it.get("input_schema", {}),
                output_schema=it.get("output_schema", {}),
                runtime_config=rc,
                is_default=True,
                created_by=owner.id,
            )
            self.db.add(version)

            for tag_name in it.get("tags", []):
                self.db.add(NodeTag(node_id=node.id, tag=tag_name))

            created_nodes.append(node)

        await self.db.commit()
        return created_nodes

    async def list_nodes(
        self,
        owner: User,
        category_id: uuid.UUID | None = None,
        status: str | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 20,
        mine_only: bool = False,
        source_credential_id: uuid.UUID | None = None,
    ) -> list[Node]:
        from sqlalchemy import or_
        dept_ids = await self._get_user_department_ids(owner)
        if mine_only:
            # 返回用户所属所有部门的节点
            stmt = (
                select(Node)
                .where(Node.department_id.in_(dept_ids))
                .where(Node.status != NodeStatus.ARCHIVED.value)
                .options(
                    selectinload(Node.tags),
                    selectinload(Node.department).selectinload(Department.organization),
                    selectinload(Node.category_rel),
                    selectinload(Node.versions),
                )
            )
        else:
            # public/internal nodes are visible to all authenticated users; private nodes only to members
            stmt = (
                select(Node)
                .where(
                    or_(
                        Node.visibility == "public",
                        Node.visibility == "internal",
                        Node.department_id.in_(dept_ids),
                    )
                )
                .where(Node.status != NodeStatus.ARCHIVED.value)
                .options(
                    selectinload(Node.tags),
                    selectinload(Node.department).selectinload(Department.organization),
                    selectinload(Node.category_rel),
                    selectinload(Node.versions),
                )
            )
        if category_id:
            stmt = stmt.where(Node.category_id == category_id)
        if status:
            stmt = stmt.where(Node.status == status)
        if tag:
            stmt = stmt.join(NodeTag).where(NodeTag.tag == tag)
        if source_credential_id:
            stmt = stmt.where(Node.source_credential_id == source_credential_id)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_node(self, node_id: uuid.UUID) -> Node | None:
        result = await self.db.execute(
            select(Node)
            .where(Node.id == node_id)
            .options(
                selectinload(Node.tags),
                selectinload(Node.versions),
                selectinload(Node.department).selectinload(Department.organization),
                selectinload(Node.category_rel),
            )
        )
        return result.scalar_one_or_none()

    async def update_node(self, node_id: uuid.UUID, payload: dict[str, Any], owner: User) -> Node:
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("Node not found")
        await self._check_department_permission(node, owner)

        allowed = {"display_name", "description", "category_id", "visibility", "status"}
        stale_triggers = {"description"}
        changed_stale = False
        for field, value in payload.items():
            if field in allowed and value is not None:
                # Convert enum values to strings for storage
                setattr(node, field, value.value if hasattr(value, "value") else value)
                if field in stale_triggers:
                    changed_stale = True

        # Handle credential_id: update the default NodeVersion's runtime_config
        if "credential_id" in payload:
            default_version = next(
                (v for v in (node.versions or []) if v.is_default), None
            )
            if default_version is not None:
                rc = dict(default_version.runtime_config or {})
                if payload["credential_id"] is None:
                    rc.pop("credential_id", None)
                else:
                    rc["credential_id"] = str(payload["credential_id"])
                default_version.runtime_config = rc

        await self.db.commit()
        await self.db.refresh(node)

        # Trigger is_stale on affected Skill(s) via skill_nodes
        if changed_stale:
            from sqlalchemy import select as sa_select
            result = await self.db.execute(
                sa_select(SkillNode.skill_id).where(SkillNode.node_id == node_id)
            )
            skill_ids_to_mark = set(result.scalars().all())
            for sid in skill_ids_to_mark:
                await self.db.execute(
                    update(Skill).where(Skill.id == sid).values(is_stale=True)
                )
            if skill_ids_to_mark:
                await self.db.commit()

        return await self.get_node(node_id)

    async def archive_node(self, node_id: uuid.UUID, owner: User) -> None:
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("节点不存在")
        await self._check_department_permission(node, owner)

        await self.db.execute(
            update(Node)
            .where(Node.id == node_id)
            .values(status=NodeStatus.ARCHIVED.value)
        )
        await self.db.commit()

    async def list_versions(self, node_id: uuid.UUID) -> list[NodeVersion]:
        result = await self.db.execute(
            select(NodeVersion)
            .where(NodeVersion.node_id == node_id)
            .order_by(NodeVersion.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_version(
        self, node_id: uuid.UUID, payload: NodeVersionCreate, owner: User
    ) -> NodeVersion:
        # Check node exists and caller belongs to the same namespace
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("节点不存在")
        await self._check_department_permission(node, owner)

        # Check version uniqueness
        existing = await self.db.execute(
            select(NodeVersion).where(
                NodeVersion.node_id == node_id,
                NodeVersion.version == payload.version,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Version {payload.version} already exists for this node")

        if payload.is_default:
            # Unset previous default
            await self.db.execute(
                update(NodeVersion)
                .where(NodeVersion.node_id == node_id)
                .values(is_default=False)
            )

        version = NodeVersion(
            node_id=node_id,
            version=payload.version,
            input_schema=payload.input_schema,
            output_schema=payload.output_schema,
            runtime_config=payload.runtime_config,
            changelog=payload.changelog,
            is_default=payload.is_default,
            created_by=owner.id,
        )
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def update_version(
        self, node_id: uuid.UUID, version: str, payload: NodeVersionUpdate, owner: User
    ) -> NodeVersion:
        """修改已有版本的 schema / runtime_config / changelog。"""
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("节点不存在")
        await self._check_department_permission(node, owner)

        result = await self.db.execute(
            select(NodeVersion).where(
                NodeVersion.node_id == node_id,
                NodeVersion.version == version,
            )
        )
        ver = result.scalar_one_or_none()
        if ver is None:
            raise ValueError(f"版本 {version} 不存在")

        for field in ("input_schema", "output_schema", "runtime_config", "changelog"):
            value = getattr(payload, field)
            if value is not None:
                setattr(ver, field, value)

        await self.db.commit()
        await self.db.refresh(ver)
        return ver

    async def delete_version(self, node_id: uuid.UUID, version: str, owner: User) -> None:
        """永久删除指定版本，不允许删除当前默认版本。"""
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("节点不存在")
        await self._check_department_permission(node, owner)

        result = await self.db.execute(
            select(NodeVersion).where(
                NodeVersion.node_id == node_id,
                NodeVersion.version == version,
            )
        )
        ver = result.scalar_one_or_none()
        if ver is None:
            raise ValueError(f"版本 {version} 不存在")
        if ver.is_default:
            raise ValueError("不能删除当前默认版本，请先将其他版本设为默认版本后再操作")

        await self.db.delete(ver)
        await self.db.commit()

    async def get_version(
        self, node_id: uuid.UUID, version: str | None = None
    ) -> NodeVersion | None:
        if version:
            result = await self.db.execute(
                select(NodeVersion).where(
                    NodeVersion.node_id == node_id,
                    NodeVersion.version == version,
                )
            )
        else:
            result = await self.db.execute(
                select(NodeVersion).where(
                    NodeVersion.node_id == node_id,
                    NodeVersion.is_default.is_(True),
                )
            )
        return result.scalar_one_or_none()

    async def log_invocation(
        self,
        node_id: uuid.UUID,
        version: str,
        invoked_by: uuid.UUID,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
        status: str,
        latency_ms: int,
        error_message: str | None = None,
    ) -> uuid.UUID:
        log = NodeInvocationLog(
            node_id=node_id,
            version=version,
            invoked_by=invoked_by,
            input_data=input_data,
            output_data=output_data,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        self.db.add(log)
        await self.db.commit()
        return log.id

    async def list_logs(self, node_id: uuid.UUID, limit: int = 50) -> list[NodeInvocationLog]:
        result = await self.db.execute(
            select(NodeInvocationLog)
            .where(NodeInvocationLog.node_id == node_id)
            .order_by(NodeInvocationLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
