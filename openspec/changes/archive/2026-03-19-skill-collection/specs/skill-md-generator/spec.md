## ADDED Requirements

### Requirement: 生成 SKILL.md 草稿
系统 SHALL 提供 `POST /api/v1/skills/{skill_id}/generate` 端点（需认证），收集 Skill 下所有 active 节点的 metadata 后调用外部 LLM，生成标准 Agent Skills 格式的 SKILL.md 草稿文本，不自动发布版本。

#### Scenario: 生成成功
- **WHEN** 已认证用户调用 POST /api/v1/skills/{skill_id}/generate
- **THEN** 系统 SHALL 收集节点的 name/display_name/description/usage_hint/input_schema/output_schema，调用 LLM，返回 200 和 `{"skill_md": "<生成的 SKILL.md 完整文本>", "suggested_version": "x.y.z"}`

#### Scenario: Skill 下没有 active 节点
- **WHEN** Skill 下没有 status=active 的节点
- **THEN** 系统 SHALL 返回 422，提示"技能集中没有可用节点"

#### Scenario: LLM 调用失败
- **WHEN** 外部 LLM API 返回错误或超时（30秒）
- **THEN** 系统 SHALL 返回 503，提示"AI 生成服务暂时不可用，请稍后重试"

#### Scenario: 并发生成请求被拒绝
- **WHEN** 同一 Skill 正在生成中，又收到新的生成请求
- **THEN** 系统 SHALL 返回 409，提示"该技能集正在生成中"

### Requirement: SKILL.md 内容标准
生成的 SKILL.md SHALL 包含：YAML frontmatter（name/description/trigger_keywords/metadata）、环境配置说明（.env 变量）、每个节点的 REST 调用文档（场景描述 + POST 接口路径 + 入参表 + 出参表 + 请求/响应示例）、工具组合使用示例。

#### Scenario: frontmatter 字段完整
- **WHEN** 生成成功
- **THEN** 输出的 YAML frontmatter SHALL 含 name（来自 Skill.name）、description（LLM 生成，100字内）、trigger_keywords（LLM 生成，5-10 个中英文关键词）、metadata.version 和 metadata.author

#### Scenario: 节点调用文档包含入参表
- **WHEN** 节点有 input_schema.properties
- **THEN** 对应章节 SHALL 包含 Markdown 表格，列为：字段名、类型、是否必填、说明

#### Scenario: usage_hint 为空时仍能生成
- **WHEN** 部分节点的 usage_hint 为空
- **THEN** 系统 SHALL 仅基于 description 和 schema 推断场景描述，不报错
