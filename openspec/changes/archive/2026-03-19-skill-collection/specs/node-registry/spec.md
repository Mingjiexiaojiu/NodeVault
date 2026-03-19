## MODIFIED Requirements

### Requirement: 注册 Node
系统 SHALL 提供 `POST /api/v1/nodes` 端点（需认证），接受 `NodeCreate` 请求体，在调用者的默认 Namespace 下创建 Node 记录和 v1.0.0 NodeVersion 记录。Node `name` 在同一 Namespace 内 SHALL 唯一。请求体 SHALL 支持可选字段 `skill_id`（UUID）和 `usage_hint`（字符串，最长 500 字符）。

#### Scenario: 注册 Node 成功
- **WHEN** 已认证用户提供合法的 NodeCreate 请求体（name/type/input_schema/output_schema/runtime 均有效）
- **THEN** 系统 SHALL 创建 Node 和 NodeVersion 记录，返回 201 和 NodeResponse（含 id/name/type/status/版本号/skill_id/usage_hint）

#### Scenario: 同命名空间内 name 重复
- **WHEN** 同一用户尝试注册与已有 Node 同名的新 Node
- **THEN** 系统 SHALL 返回 409，提示名称在该命名空间已存在

#### Scenario: 字段校验复用 NodeSchemaBase 规则
- **WHEN** 提供不符合 snake_case 的 name 或不符合 SemVer 的 version
- **THEN** 系统 SHALL 返回 422 并说明具体字段的校验错误

#### Scenario: skill_id 不存在时注册失败
- **WHEN** 提供的 skill_id 在数据库中不存在
- **THEN** 系统 SHALL 返回 422，提示"指定的技能集不存在"

## ADDED Requirements

### Requirement: Node 支持 usage_hint 字段
Node 记录 SHALL 包含可选字段 `usage_hint`（字符串，最长 500 字符），描述该节点的适用场景，供 LLM 生成 SKILL.md 时使用。`PATCH /api/v1/nodes/{node_id}` SHALL 支持更新 usage_hint，更新后 SHALL 触发所属 Skill 的 is_stale 置 true。

#### Scenario: 更新 usage_hint 成功
- **WHEN** Node 所有者 PATCH 更新 usage_hint
- **THEN** 系统 SHALL 返回 200，NodeResponse 含更新后的 usage_hint，且所属 Skill 的 is_stale 被置为 true

#### Scenario: usage_hint 超长被拒绝
- **WHEN** 提供的 usage_hint 超过 500 字符
- **THEN** 系统 SHALL 返回 422

### Requirement: Node 支持 skill_id 字段
Node 记录 SHALL 包含可选字段 `skill_id`（UUID 外键，指向 skills 表），`PATCH /api/v1/nodes/{node_id}` SHALL 支持更新 skill_id（含置 null），变更 skill_id SHALL 触发新旧两个 Skill 的 is_stale 置 true。

#### Scenario: 变更 skill_id 触发双端 is_stale
- **WHEN** 节点从 Skill A 移动到 Skill B（更新 skill_id）
- **THEN** 系统 SHALL 将 Skill A 和 Skill B 的 is_stale 均置为 true
