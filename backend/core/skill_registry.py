"""Skill 管理核心逻辑。

包含 Skill CRUD 操作和版本发布。
"""
import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.node import Node, NodeVersion
from backend.models.skill import Skill, SkillVersion
from backend.models.skill_node import SkillNode
from backend.models.user import User
from backend.schemas.skill import SkillCreate, SkillUpdate, SkillVersionCreate


class SkillRegistry:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _check_owner(self, skill: Skill, user: User) -> None:
        """检查用户是否为技能创建者或超管。"""
        if user.role == 0:
            return  # 超管可操作所有技能
        if skill.owner_id != user.id:
            raise PermissionError("仅技能创建者或超管可操作此技能")

    async def _get_skill(self, skill_id: uuid.UUID) -> Skill | None:
        result = await self.db.execute(
            select(Skill)
            .options(
                selectinload(Skill.skill_nodes).selectinload(SkillNode.node).selectinload(Node.category_rel),
                selectinload(Skill.versions),
            )
            .where(Skill.id == skill_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Skill CRUD
    # ------------------------------------------------------------------

    async def create_skill(self, payload: SkillCreate, owner: User) -> Skill:
        """创建技能集。name 可选，未提供时基于 display_name 自动生成。"""
        from backend.core.naming import to_kebab_case

        if payload.name:
            # User-provided name: check uniqueness
            existing = await self.db.execute(
                select(Skill).where(Skill.name == payload.name)
            )
            if existing.scalar_one_or_none() is not None:
                raise ValueError(f"已存在名为 '{payload.name}' 的技能集")
            name = payload.name
        else:
            # Auto-generate from display_name
            base = to_kebab_case(payload.display_name)
            name = base
            suffix = 2
            while True:
                existing = await self.db.execute(
                    select(Skill).where(Skill.name == name)
                )
                if existing.scalar_one_or_none() is None:
                    break
                name = f"{base}-{suffix}"
                suffix += 1

        skill = Skill(
            name=name,
            display_name=payload.display_name,
            description=payload.description,
            owner_id=owner.id,
        )
        self.db.add(skill)
        await self.db.commit()
        await self.db.refresh(skill)
        return await self._get_skill(skill.id)

    async def list_skills(
        self,
        user: User,
        skip: int = 0,
        limit: int = 50,
    ) -> list[tuple[Skill, int, str | None]]:
        """列出技能，返回 (skill, node_count, latest_version) 元组列表。"""
        result = await self.db.execute(
            select(Skill)
            .options(
                selectinload(Skill.skill_nodes).selectinload(SkillNode.node).selectinload(Node.category_rel),
                selectinload(Skill.versions),
            )
            .where(Skill.status != "archived")
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
                len(skill.skill_nodes),
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
        await self._check_owner(skill, owner)

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
        await self._check_owner(skill, owner)

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
        await self._check_owner(skill, owner)

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
        """构建节点快照：从 skill_nodes M2M 关联查询节点及默认版本，含 usage_hint。"""
        result = await self.db.execute(
            select(SkillNode)
            .options(selectinload(SkillNode.node))
            .where(SkillNode.skill_id == skill_id)
            .order_by(SkillNode.sort_order)
        )
        skill_nodes = list(result.scalars().all())
        snapshot = []
        for sn in skill_nodes:
            node = sn.node
            if node is None:
                continue
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
                "usage_hint": sn.usage_hint,
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
