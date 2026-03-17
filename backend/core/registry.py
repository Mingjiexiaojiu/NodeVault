import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.namespace import Namespace
from backend.models.node import Node, NodeInvocationLog, NodeTag, NodeVersion
from backend.models.user import User
from backend.schemas.enums import NodeStatus
from backend.schemas.node import NodeCreate, NodeVersionCreate


class NodeRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_namespace(self, owner: User) -> Namespace:
        result = await self.db.execute(
            select(Namespace).where(Namespace.owner_id == owner.id)
        )
        ns = result.scalar_one_or_none()
        if ns is None:
            raise ValueError(f"No namespace found for user {owner.id}")
        return ns

    async def create_node(self, payload: NodeCreate, owner: User) -> Node:
        ns = await self._get_namespace(owner)

        node = Node(
            name=payload.name,
            namespace_id=ns.id,
            owner_id=owner.id,
            display_name=payload.display_name,
            description=payload.description,
            type=payload.type.value,
            category=payload.category,
            status=payload.status.value,
            visibility=payload.visibility.value,
        )
        self.db.add(node)
        await self.db.flush()

        # Create first version
        version = NodeVersion(
            node_id=node.id,
            version=payload.version,
            input_schema=payload.input_schema,
            output_schema=payload.output_schema,
            runtime_config=payload.runtime.model_dump(),
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

    async def list_nodes(
        self,
        owner: User,
        type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[Node]:
        ns = await self._get_namespace(owner)
        stmt = (
            select(Node)
            .where(Node.namespace_id == ns.id)
            .where(Node.status != NodeStatus.ARCHIVED.value)
            .options(selectinload(Node.tags))
        )
        if type:
            stmt = stmt.where(Node.type == type)
        if status:
            stmt = stmt.where(Node.status == status)
        if tag:
            stmt = stmt.join(NodeTag).where(NodeTag.tag == tag)

        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_node(self, node_id: uuid.UUID) -> Node | None:
        result = await self.db.execute(
            select(Node)
            .where(Node.id == node_id)
            .options(selectinload(Node.tags), selectinload(Node.versions))
        )
        return result.scalar_one_or_none()

    async def update_node(self, node_id: uuid.UUID, payload: dict[str, Any], owner: User) -> Node:
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("Node not found")
        if node.owner_id != owner.id:
            raise PermissionError("Not allowed to update this node")

        allowed = {"display_name", "description", "category", "visibility", "status"}
        for field, value in payload.items():
            if field in allowed and value is not None:
                # Convert enum values to strings for storage
                setattr(node, field, value.value if hasattr(value, "value") else value)

        await self.db.commit()
        await self.db.refresh(node)
        return await self.get_node(node_id)

    async def archive_node(self, node_id: uuid.UUID, owner: User) -> None:
        node = await self.get_node(node_id)
        if node is None:
            raise ValueError("Node not found")
        if node.owner_id != owner.id:
            raise PermissionError("Not allowed to delete this node")

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
