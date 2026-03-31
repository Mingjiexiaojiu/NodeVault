"""SKILL.md AI 生成器。

从技能集节点元数据构建 Prompt 并调用 LLM（claude 或 openai）生成 SKILL.md 内容。
通过 DB 行级锁防止同一 Skill 同时触发多次生成。
支持使用用户自定义 AI 配置（UserAIConfig）覆盖全局环境变量配置。
"""
import asyncio
import os
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.node import Node, NodeVersion
from backend.models.skill import Skill
from backend.models.skill_node import SkillNode


_LLM_TIMEOUT = 120  # seconds


@dataclass
class LLMConfig:
    """LLM 调用配置，可来自用户自定义 AI 配置或全局环境变量回退。"""
    provider: str      # "openai" | "claude" | "custom"
    model: str
    api_key: str
    base_url: str | None = None


def _build_prompt(skill: Skill, nodes_meta: list[dict[str, Any]], base_url: str) -> str:
    node_sections = []
    for nm in nodes_meta:
        node_sections.append(
            f"### {nm['display_name'] or nm['name']}\n"
            f"- 用途：{nm['usage_hint'] or nm['description'] or '（无描述）'}\n"
            f"- 输入 Schema：\n```json\n{nm['input_schema']}\n```\n"
            f"- 输出 Schema：\n```json\n{nm['output_schema']}\n```\n"
            f"- 调用端点：POST {base_url}/api/v1/invoke/{nm['name']}\n"
        )
    nodes_block = "\n".join(node_sections) if node_sections else "（暂无节点）"

    return f"""你是一名专业的 AI 工具技能文档作者。请根据以下 NodeVault 技能集信息，生成一份符合 Agent Skills 规范的 SKILL.md 文件。

技能集名称：{skill.name}
展示名称：{skill.display_name}
描述：{skill.description or '（无描述）'}
节点数量：{len(nodes_meta)}

节点详情：
{nodes_block}

要求：
1. 文件以 YAML frontmatter 开头，包含 name、description、trigger_keywords（列表）、metadata（含 version、author）
2. Markdown 正文包含 ## Overview、## Nodes（每个节点独立小节）、## Authentication、## Setup
3. 每个节点小节包含：功能说明、调用示例（curl 格式，使用 $NODEVAULT_URL 和 $NODEVAULT_API_KEY 环境变量）
4. Authentication 章节说明如何设置 API Key（Bearer Token）
5. Setup 章节说明所需环境变量：NODEVAULT_URL、NODEVAULT_API_KEY
6. 全程使用简体中文，代码块保持英文

请直接返回 SKILL.md 文件内容，不要附加任何解释。"""


async def _call_claude(prompt: str, cfg: LLMConfig) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(
        api_key=cfg.api_key,
        base_url=cfg.base_url or None,
        timeout=_LLM_TIMEOUT,
    )
    message = await client.messages.create(
        model=cfg.model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


async def _call_openai(prompt: str, cfg: LLMConfig) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=cfg.api_key,
        base_url=cfg.base_url or None,
        timeout=_LLM_TIMEOUT,
    )
    response = await client.chat.completions.create(
        model=cfg.model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return response.choices[0].message.content


async def generate_skill_md(
    db: AsyncSession,
    skill_id: uuid.UUID,
    llm_config: LLMConfig | None = None,
) -> dict[str, str]:
    """生成 SKILL.md 草稿，返回 {skill_md, suggested_version}。

    llm_config: 用户选定的 AI 配置；为 None 时回落到环境变量（LLM_PROVIDER）。
    """
    result = await db.execute(
        select(Skill).where(Skill.id == skill_id)
    )

    skill = result.scalar_one_or_none()
    if skill is None:
        raise ValueError("技能集不存在")

    # Collect node metadata via skill_nodes M2M
    sn_result = await db.execute(
        select(SkillNode)
        .where(SkillNode.skill_id == skill_id)
        .order_by(SkillNode.sort_order)
    )
    skill_nodes = list(sn_result.scalars().all())
    if not skill_nodes:
        raise ValueError("技能集下没有节点，无法生成 SKILL.md")

    nodes_meta = []
    for sn in skill_nodes:
        # Load the node
        node_result = await db.execute(
            select(Node).where(Node.id == sn.node_id)
        )
        node = node_result.scalar_one_or_none()
        if node is None:
            continue
        # Get default version for schema
        ver_result = await db.execute(
            select(NodeVersion).where(
                NodeVersion.node_id == node.id,
                NodeVersion.is_default.is_(True),
            )
        )
        default_ver = ver_result.scalar_one_or_none()
        # usage_hint from SkillNode; fallback to node.description
        usage_hint = sn.usage_hint or node.description
        nodes_meta.append({
            "name": node.name,
            "display_name": node.display_name,
            "description": node.description,
            "usage_hint": usage_hint,
            "input_schema": str(default_ver.input_schema) if default_ver else "{}",
            "output_schema": str(default_ver.output_schema) if default_ver else "{}",
        })

    base_url = os.environ.get("NODEVAULT_BASE_URL", "https://your-nodevault-host")
    prompt = _build_prompt(skill, nodes_meta, base_url)

    # 优先使用传入的用户配置；否则回落到全局环境变量
    if llm_config is None:
        provider = os.environ.get("LLM_PROVIDER", "claude").lower()
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("未配置 AI 提供商，请先在「个人设置 → AI 配置」中添加 API Key")
            llm_config = LLMConfig(
                provider="openai",
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                api_key=api_key,
            )
        else:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("未配置 AI 提供商，请先在「个人设置 → AI 配置」中添加 API Key")
            llm_config = LLMConfig(
                provider="claude",
                model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-5"),
                api_key=api_key,
            )

    if llm_config.provider == "claude":
        skill_md = await _call_claude(prompt, llm_config)
    else:
        # openai / custom（openai-compatible）均走 openai 客户端
        skill_md = await _call_openai(prompt, llm_config)

    # Suggest next patch version
    from sqlalchemy import func as sqlfunc
    from backend.models.skill import SkillVersion

    latest_ver_result = await db.execute(
        select(SkillVersion.version)
        .where(SkillVersion.skill_id == skill_id)
        .order_by(SkillVersion.created_at.desc())
        .limit(1)
    )
    latest_ver = latest_ver_result.scalar_one_or_none()
    if latest_ver:
        parts = latest_ver.split(".")
        try:
            suggested = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"
        except (IndexError, ValueError):
            suggested = "1.0.0"
    else:
        suggested = "1.0.0"

    return {"skill_md": skill_md, "suggested_version": suggested}
