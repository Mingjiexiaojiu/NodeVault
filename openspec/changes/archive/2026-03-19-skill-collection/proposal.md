## Why

当前 NodeVault 的 Skill 导出是单节点粒度的，而 AI Agent 框架（如 OpenClaw、Claude Code、Cursor）期望的是**技能集**——一组同方向节点打包成一个 SKILL.md，让 Agent 按场景按需加载并直接调用 REST API。现有的 `skill.py` ZIP 格式面向 Python 开发者，不是 AI 可读的调用文档，无法被 Agent 框架原生消费。

## What Changes

- **新增** `Skill` 实体：将现有节点的 `category` 字符串字段升级为 `Skill` 外键，一个 Skill 就是一个方向的节点集合（如 NLP、Finance），节点只能属于一个 Skill
- **新增** `SkillVersion` 实体：Skill 的可版本化快照，锁定发布时各节点的具体版本号，并存储 AI 生成的 `SKILL.md` 文本
- **新增** Node 模型字段 `usage_hint`：用户填写的使用场景描述，用于指导 LLM 生成准确的触发关键词和调用说明
- **新增** SKILL.md 生成接口：收集 Skill 下所有节点的 metadata + usage_hint + I/O schema，调用 LLM 生成标准 Agent Skills 格式的 SKILL.md
- **新增** Skill 导出接口：下载包含 `SKILL.md` + `references/setup.md` 的 ZIP，供 Agent 框架直接安装使用
- **新增** 前端技能集管理页：创建/编辑 Skill、查看节点列表、生成预览与发布版本、下载 ZIP
- **修改** 节点创建/编辑页：`category` 字段改为 Skill 选择器，新增 `usage_hint` 输入框

## Capabilities

### New Capabilities

- `skill-collection`: Skill 实体 CRUD、SkillVersion 快照管理、is_stale 变更检测
- `skill-md-generator`: 基于节点 metadata + usage_hint + schema，调用 LLM 生成符合 Agent Skills 标准的 SKILL.md
- `skill-set-export`: 将 SkillVersion 打包为 ZIP（SKILL.md + references/setup.md），供 OpenClaw / Claude Code 等 Agent 框架安装
- `frontend-skill-collection`: 技能集列表页、详情页（节点列表、版本历史）、生成预览、发布与下载流程

### Modified Capabilities

- `node-registry`: Node 新增 `usage_hint` 字段和 `skill_id` 外键（替代字符串 category），注册和更新接口随之调整
- `frontend-node-create`: 节点创建/编辑页新增 `usage_hint` 输入框，`category` 改为 Skill 选择器

## Impact

- **数据库**：新增 `skills` 表、`skill_versions` 表；`nodes` 表新增 `usage_hint` 列、`skill_id` 外键，保留 `category` 字段作为冗余展示（从 Skill.display_name 同步）
- **API**：新增 `/api/v1/skills` CRUD、`/api/v1/skills/{id}/versions` 版本管理、`/api/v1/skills/{id}/generate`（LLM 生成 SKILL.md 预览）、`/api/v1/skills/{id}/export`（下载 ZIP）
- **LLM 依赖**：SKILL.md 生成需要调用外部 LLM API（Claude / OpenAI），需要配置 API Key 环境变量
- **现有导出不受影响**：单节点 `skill.py` ZIP（`GET /api/v1/nodes/{id}/export/skill`）保留，路径不变
- **前端**：新增技能集路由和页面；节点表单改动影响创建和编辑流程
