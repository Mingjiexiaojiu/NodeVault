"""Skill 管理核心逻辑。

包含 Skill CRUD 操作和版本发布。
"""
import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.namespace import Namespace, NamespaceMember
from backend.models.node import Node, NodeVersion
from backend.models.skill import Skill, SkillVersion
from backend.models.user import User
from backend.schemas.skill import SkillCreate, SkillUpdate, SkillVersionCreate


class SkillRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_namespace(self, namespace_id: uuid.UUID) -> Namespace:
        result = await self.db.execute(
            select(Namespace).where(Namespace.id == namespace_id)
        )
        ns = result.scalar_one_or_none()
        if ns is None:
            raise ValueError("指定的部门不存在")
        return ns

    async def _check_member(self, namespace_id: uuid.UUID, user: User) -> None:
        result = await self.db.execute(
            select(NamespaceMember).where(
                NamespaceMember.namespace_id == namespace_id,
                NamespaceMember.user_id == user.id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise PermissionError("您不是该部门的成员")

    async def _get_skill(self, skill_id: uuid.UUID) -> Skill | None:
        result = await self.db.execute(
            select(Skill)
            .options(selectinload(Skill.nodes), selectinload(Skill.versions))
            .where(Skill.id == skill_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Skill CRUD
    # ------------------------------------------------------------------

    async def create_skill(self, payload: SkillCreate, owner: User) -> Skill:
        """创建技能集，校验 namespace 成员资格和 name 唯一性。"""
        await self._get_namespace(payload.namespace_id)
        await self._check_member(payload.namespace_id, owner)

        # Uniqueness check
        existing = await self.db.execute(
            select(Skill).where(
                Skill.name == payload.name,
                Skill.namespace_id == payload.namespace_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"该部门下已存在名为 '{payload.name}' 的技能集")

        skill = Skill(
            name=payload.name,
            display_name=payload.display_name,
            description=payload.description,
            namespace_id=payload.namespace_id,
            owner_id=owner.id,
        )
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return await self._get_skill(skill.id)

    async def list_skills(
        self,
        namespace_id: uuid.UUID | None,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[tuple[Skill, int, str | None]]:
        """列出技能，返回 (skill, node_count, latest_version) 元组列表。"""
        # Determine accessible namespace IDs
        if namespace_id:
            ns_ids = [namespace_id]
        else:
            membership_result = await self.db.execute(
                select(NamespaceMember.namespace_id).where(NamespaceMember.user_id == user.id)
            )
            ns_ids = list(membership_result.scalars().all())
            if not ns_ids:
                return []

        result = await self.db.execute(
            select(Skill)
            .options(selectinload(Skill.nodes), selectinload(Skill.versions))
            .where(Skill.namespace_id.in_(ns_ids), Skill.status != "archived")
            .offset(skip)
            .limit(limit)
        )
        skills = list(result.scalars().all())
        out = []
        for skill in skills:
            default_ver = next(
                (v for v in skill.versions if v.is_default),
                skill.versions[0] if skill.versions else None,
            )
            out.append((
                skill,
                len(skill.nodes),
                default_ver.version if default_ver else None,
            ))
        return out

    async def get_skill(self, skill_id: uuid.UUID) -> Skill | None:
        return await self._get_skill(skill_id)

    async def update_skill(
        self, skill_id: uuid.UUID, payload: SkillUpdate, owner: User
    ) -> Skill:
        skill = await self._get_skill(skill_id)
        if skill is None:
            raise ValueError("技能集不存在")
        await self._check_member(skill.namespace_id, owner)

        if payload.display_name is not None:
            skill.display_name = payload.display_name
        if payload.description is not None:
            skill.description = payload.description
        if payload.status is not None:
            skill.status = payload.status

        await self.db.commit()
        await self.db.refresh(skill)
        return await self._get_skill(skill.id)

    async def archive_skill(self, skill_id: uuid.UUID, owner: User) -> None:
        skill = await self._get_skill(skill_id)
        if skill is None:
            raise ValueError("技能集不存在")
        await self._check_member(skill.namespace_id, owner)

        await self.db.execute(
            update(Skill).where(Skill.id == skill_id).values(status="archived")
        )
        await self.db.commit()

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------

    async def create_version(
        self, skill_id: uuid.UUID, payload: SkillVersionCreate, owner: User
    ) -> SkillVersion:
        """发布技能版本：锁定节点快照，可选设为默认版本，重置 is_stale。"""
        skill = await self._get_skill(skill_id)
        if skill is None:
            raise ValueError("技能集不存在")
        await self._check_member(skill.namespace_id, owner)

        # Check version uniqueness within skill
        existing = await self.db.execute(
            select(SkillVersion).where(
                SkillVersion.skill_id == skill_id,
                SkillVersion.version == payload.version,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(f"版本号 '{payload.version}' 已存在")

        # Build node snapshot: collect current default NodeVersion for each node
        node_snapshot = await self._build_node_snapshot(skill_id)

        # If this version becomes default, unset previous defaults
        if payload.is_default:
            await self.db.execute(
                update(SkillVersion)
                .where(SkillVersion.skill_id == skill_id, SkillVersion.is_default.is_(True))
                .values(is_default=False)
            )

        version = SkillVersion(
            skill_id=skill_id,
            version=payload.version,
            skill_md=payload.skill_md,
            node_snapshot=node_snapshot,
            release_notes=payload.release_notes,
            is_default=payload.is_default,
        )
        self.db.add(version)

        # Reset is_stale flag on the skill
        await self.db.execute(
            update(Skill).where(Skill.id == skill_id).values(is_stale=False)
        )

        await self.db.commit()
        await self.db.refresh(version)
        return version

    async def _build_node_snapshot(self, skill_id: uuid.UUID) -> list[dict[str, Any]]:
        """构建节点快照：查询当前技能集所有节点及其默认版本。"""
        result = await self.db.execute(
            select(Node).where(Node.skill_id == skill_id)
        )
        nodes = list(result.scalars().all())
        snapshot = []
        for node in nodes:
            # Get default version
            ver_result = await self.db.execute(
                select(NodeVersion).where(
                    NodeVersion.node_id == node.id,
                    NodeVersion.is_default.is_(True),
                )
            )
            default_ver = ver_result.scalar_one_or_none()
            snapshot.append({
                "node_id": str(node.id),
                "node_name": node.name,
                "node_display_name": node.display_name,
                "node_version_id": str(default_ver.id) if default_ver else None,
                "node_version": default_ver.version if default_ver else None,
            })
        return snapshot

    async def list_versions(self, skill_id: uuid.UUID) -> list[SkillVersion]:
        result = await self.db.execute(
            select(SkillVersion)
            .where(SkillVersion.skill_id == skill_id)
            .order_by(SkillVersion.created_at.desc())
        )
        return list(result.scalars().all())
