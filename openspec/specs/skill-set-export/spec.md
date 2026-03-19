## Requirements

### Requirement: 下载 Skill 技能集 ZIP
系统 SHALL 提供 `GET /api/v1/skills/{skill_id}/export` 端点（需认证），返回 ZIP 文件，默认使用最新 SkillVersion，可通过 `?version=x.y.z` 指定历史版本。

#### Scenario: 下载最新版本 ZIP
- **WHEN** 调用 GET /api/v1/skills/{skill_id}/export
- **THEN** 响应 Content-Type 为 application/zip，Content-Disposition 为 `attachment; filename="{skill_name}-{version}.zip"`，ZIP 含 SKILL.md 和 references/setup.md

#### Scenario: 下载指定历史版本
- **WHEN** 调用 GET /api/v1/skills/{skill_id}/export?version=1.0.0
- **THEN** 系统 SHALL 使用该版本的 SkillVersion.skill_md 生成 ZIP

#### Scenario: Skill 尚无任何版本
- **WHEN** Skill 从未发布过版本
- **THEN** 系统 SHALL 返回 422，提示"请先生成并发布一个版本"

#### Scenario: 指定版本不存在
- **WHEN** 请求的 version 号不存在
- **THEN** 系统 SHALL 返回 404

### Requirement: ZIP 内容结构
导出的 ZIP SHALL 包含且仅包含以下文件：`SKILL.md`（SkillVersion.skill_md 原文）和 `references/setup.md`（静态模板，说明如何配置 .env）。

#### Scenario: SKILL.md 内容完整
- **WHEN** 解压 ZIP 读取 SKILL.md
- **THEN** 文件内容 SHALL 与对应 SkillVersion.skill_md 字段完全一致

#### Scenario: setup.md 包含环境变量说明
- **WHEN** 解压 ZIP 读取 references/setup.md
- **THEN** 文件 SHALL 包含 NODEVAULT_URL 和 NODEVAULT_API_KEY 的配置说明
