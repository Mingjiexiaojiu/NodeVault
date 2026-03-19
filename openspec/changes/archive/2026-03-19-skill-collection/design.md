## Context

NodeVault 目前的 Skill 导出是单节点粒度（`GET /api/v1/nodes/{id}/export/skill`），生成包含 `skill.py`（Python SDK 调用代码）的 ZIP，面向 Python 开发者使用。

Agent 框架（OpenClaw / Claude Code / Cursor）期望的是 **Agent Skills 标准格式**：一个包含 `SKILL.md` 的目录，AI 读取其中的 Markdown 文档后，直接按文档描述构造 HTTP 请求调用 NodeVault REST API，所有认证信息从 `.env` 读取。

节点当前的 `category` 是裸字符串，没有持久化实体，无法关联版本、描述、导出历史等元数据。

---

## Goals / Non-Goals

**Goals:**
- 将 `category` 升级为 `Skill` 实体，支持 CRUD 和版本化快照
- Node 新增 `usage_hint` 字段，供 LLM 生成准确的 SKILL.md
- 实现 SKILL.md 生成接口（调用外部 LLM）和导出接口（ZIP 下载）
- 前端提供技能集管理页面，支持生成预览、编辑、发布、下载
- 保持现有单节点 `skill.py` ZIP 导出路径不变

**Non-Goals:**
- 不实现 MCP 协议层（已有独立实现，Skill 导出走 REST HTTP 直调）
- 不修改 OpenAI / LangChain / MCP 导出格式
- 不实现 Skill 的跨用户分享或公开市场

---

## Decisions

### D1：Skill 实体替代 category 字符串

**决策**：`nodes.category` 字段保留（从 Skill.display_name 冗余写入），同时新增 `skill_id` UUID 外键（nullable，已有节点平滑迁移，`SET NULL` on delete）。

**原因**：category 字符串已在前端多处使用，保留字段避免大规模前端改动；`skill_id` 外键提供精确关联，两者并存直到彻底切换。

**备选方案**：直接废弃 category 字段 → 改动面太大，阻断进行中的前端工作。

---

### D2：SkillVersion 存储完整 SKILL.md 文本

**决策**：`skill_versions.skill_md` 列（TEXT）存储 AI 生成并经用户确认的完整 SKILL.md 原文；`node_snapshot` 列（JSONB）存储快照时各节点的 `{node_id, node_version_id, node_name}` 列表。

**原因**：运行时导出只需读库，无需重新调用 LLM；历史版本可精确复现；用户微调内容可直接保存。

---

### D3：LLM 生成 SKILL.md 的提示策略

**决策**：将 Skill 下所有节点的 `name / display_name / description / usage_hint / input_schema / output_schema` 序列化为结构化 Prompt，调用外部 LLM（优先 Claude，通过 `LLM_PROVIDER` 环境变量切换）。生成结果为草稿，用户可在前端预览编辑后再确认发布。

生成内容包括：
1. YAML frontmatter（`name / description / trigger_keywords / metadata`）
2. 环境配置说明（`.env` 变量）
3. 每个节点：场景描述 + REST 调用格式 + 入参/出参表 + 请求/响应示例
4. 工具组合使用示例

**原因**：`usage_hint`（用户填写）+ schema（系统字段）双重信息来源保证生成质量；草稿预览避免用户对 AI 生成结果无感知地发布。

---

### D4：is_stale 检测机制

**决策**：`skills.is_stale` 布尔字段，以下事件触发置 `true`：节点加入/离开该 Skill、节点的 `usage_hint / description` 更新、节点发布新默认版本。由前端在技能集详情页展示"节点已变更，建议重新生成"的提示 banner，不强制阻断下载。

---

### D5：ZIP 导出结构

```
{skill_name}-{version}.zip/
├── SKILL.md              ← SkillVersion.skill_md 原文
└── references/
    └── setup.md          ← 静态模板：如何配置 .env（NODEVAULT_URL / NODEVAULT_API_KEY）
```

**原因**：结构与 Claude Code / OpenClaw 的标准 Skills 目录一致；`setup.md` 为人类可读的安装指引，静态模板生成即可。

---

### D6：LLM API 调用的错误处理

**决策**：LLM 调用超时（30s）或失败时返回 `503`，不降级到模板生成。前端展示明确错误提示，引导用户重试或手动编写。

**原因**：降级模板生成质量差且可能产生误导性内容；用户重试成本低。

---

## Risks / Trade-offs

- **[LLM 成本]** 每次生成调用外部 LLM，有 API 费用 → 限制为按需触发（用户主动点击"生成"），不自动触发
- **[生成质量]** `usage_hint` 为空时 LLM 可能生成模糊的触发描述 → 前端在 usage_hint 为空的节点上显示警告
- **[迁移]** 已有节点的 `category` 字符串无法自动匹配到 Skill 实体 → 迁移脚本将相同 category 值分组，自动创建对应 Skill 实体并回填 `skill_id`；无法匹配的保持 null
- **[并发]** 同一 Skill 同时触发多次 LLM 生成 → 接口加幂等锁（数据库行锁），重复请求返回 `409`

## Migration Plan

1. Alembic migration：`skills` 表 + `skill_versions` 表 + `nodes.skill_id` + `nodes.usage_hint`
2. 数据迁移脚本：读取现有 `nodes.category` 分组 → 创建 Skill 记录 → 回填 `nodes.skill_id`
3. 部署：后端先上（字段 nullable，无破坏性），前端后上
4. 回滚：`skill_id` 为 nullable，回滚只需重新部署旧版前端，数据库保持兼容

## Open Questions

- LLM Provider 配置：优先 Claude API 还是允许用户在 admin 设置里切换？
- `setup.md` 中 NodeVault URL 是否硬编码为 `${NODEVAULT_URL}` 占位符，还是根据系统配置填入实际地址？
