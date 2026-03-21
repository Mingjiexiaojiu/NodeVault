## ADDED Requirements

### Requirement: Node ↔ Skill 多对多关联
系统 SHALL 使用 `skill_nodes` 关联表（id, skill_id FK, node_id FK, usage_hint VARCHAR(500), sort_order INT, created_at）管理 Node 与 Skill 的多对多关系。UNIQUE(skill_id, node_id)。

#### Scenario: 同一节点属于多个 Skill
- **WHEN** 节点 A 被添加到 Skill X 和 Skill Y
- **THEN** skill_nodes 表 SHALL 有两条记录，分别关联 (X, A) 和 (Y, A)

#### Scenario: 同一 Skill 中同一节点不可重复
- **WHEN** 尝试将已在 Skill X 中的节点 A 再次添加到 Skill X
- **THEN** 系统 SHALL 返回 409，提示"该节点已在此技能集中"

### Requirement: 添加节点到 Skill
系统 SHALL 提供 `POST /api/v1/skills/{skill_id}/nodes` 端点（需认证），接受 node_id 和可选 usage_hint，将节点添加到技能集中。添加后 SHALL 触发 Skill 的 is_stale=true。

#### Scenario: 添加节点成功
- **WHEN** Skill 所有者提交合法的 node_id 和 usage_hint
- **THEN** 系统 SHALL 创建 skill_nodes 记录，返回 201，并将 Skill is_stale 置为 true

#### Scenario: 添加不存在的节点
- **WHEN** 提交的 node_id 不存在
- **THEN** 系统 SHALL 返回 404

### Requirement: 从 Skill 移除节点
系统 SHALL 提供 `DELETE /api/v1/skills/{skill_id}/nodes/{node_id}` 端点（需认证），将节点从技能集中移除。移除后 SHALL 触发 Skill 的 is_stale=true。

#### Scenario: 移除节点成功
- **WHEN** Skill 所有者请求移除某节点
- **THEN** 系统 SHALL 删除对应 skill_nodes 记录，返回 204，并将 Skill is_stale 置为 true

### Requirement: 更新关联的 usage_hint
系统 SHALL 提供 `PATCH /api/v1/skills/{skill_id}/nodes/{node_id}` 端点（需认证），更新该节点在此技能集中的 usage_hint。

#### Scenario: 更新 usage_hint 成功
- **WHEN** Skill 所有者更新某节点的 usage_hint
- **THEN** 系统 SHALL 返回 200，并将 Skill is_stale 置为 true

### Requirement: Skill 支持 is_system 标记
Skill 表 SHALL 包含 `is_system` 布尔字段（默认 false）。is_system=true 的 Skill 由系统自动创建，普通用户和主管 SHALL NOT 删除系统 Skill。

#### Scenario: 尝试删除系统 Skill 被拒绝
- **WHEN** 用户尝试 DELETE is_system=true 的 Skill
- **THEN** 系统 SHALL 返回 422，提示"系统预设技能集不可删除"

#### Scenario: 超管删除系统 Skill
- **WHEN** role=0 的超管尝试 DELETE is_system=true 的 Skill
- **THEN** 系统 SHALL 允许删除，返回 204

### Requirement: 自定义 Skill 可删除
非系统 Skill（is_system=false）的所有者 SHALL 可以删除该 Skill。删除时 SHALL 同时清除 skill_nodes 中的关联记录。

#### Scenario: 删除自定义 Skill 成功
- **WHEN** Skill 所有者删除 is_system=false 的 Skill
- **THEN** 系统 SHALL 删除 Skill、关联的 skill_nodes 记录和所有 SkillVersion，返回 204

## MODIFIED Requirements

### Requirement: 获取 Skill 详情
系统 SHALL 提供 `GET /api/v1/skills/{skill_id}` 端点（需认证），返回 Skill 详情，含所属节点列表（从 skill_nodes 关联表查询，含每个节点的 usage_hint）和版本历史，以及 is_system 标记。

#### Scenario: 获取存在的 Skill
- **WHEN** 使用有效的 skill_id
- **THEN** 系统 SHALL 返回 SkillDetailResponse，含 is_system 标记、nodes 数组（每项含 node_id/name/display_name/usage_hint/status，usage_hint 来自 skill_nodes 关联表）和 versions 数组

#### Scenario: Skill 不存在
- **WHEN** skill_id 不存在
- **THEN** 系统 SHALL 返回 404

### Requirement: 查询 Skill 列表
系统 SHALL 提供 `GET /api/v1/skills` 端点（需认证），返回当前用户命名空间内的 Skill 列表，包含每个 Skill 的节点数量、最新版本号和 is_system 标记。

#### Scenario: 列出所有 Skill
- **WHEN** 调用 GET /api/v1/skills
- **THEN** 系统 SHALL 返回 SkillResponse 列表，每项含 node_count、latest_version、is_system 字段

#### Scenario: 已归档 Skill 不在默认列表中
- **WHEN** 不带 status 参数调用 GET /api/v1/skills
- **THEN** 系统 SHALL 不返回 status=archived 的 Skill

### Requirement: is_stale 自动检测
系统 SHALL 在以下事件发生时自动将对应 Skill 的 `is_stale` 置为 `true`：skill_nodes 关联变更（节点加入/移除）、关联节点的 `description` 更新、节点发布新的默认版本、skill_nodes 中 usage_hint 变更。

#### Scenario: 节点从 Skill 添加/移除触发 is_stale
- **WHEN** 节点被添加到或从某 Skill 中移除
- **THEN** 该 Skill 的 is_stale 字段 SHALL 被置为 true

#### Scenario: 生成新版本后 is_stale 重置
- **WHEN** 成功发布一个新的 SkillVersion
- **THEN** 该 Skill 的 is_stale 字段 SHALL 被重置为 false

### Requirement: SkillVersion 快照管理
系统 SHALL 提供 `GET /api/v1/skills/{skill_id}/versions` 列出版本历史，`POST /api/v1/skills/{skill_id}/versions` 保存并发布一个新版本。快照 SHALL 包含 skill_nodes 中的 usage_hint。

#### Scenario: 发布新版本
- **WHEN** 用户提交 version（SemVer）、skill_md（SKILL.md 文本）和可选 release_notes
- **THEN** 系统 SHALL 创建 SkillVersion 记录，node_snapshot 包含每个关联节点的完整信息及其 usage_hint（来自 skill_nodes），重置 is_stale=false，返回 201

#### Scenario: 版本号重复
- **WHEN** 提交与已有版本号相同的版本
- **THEN** 系统 SHALL 返回 409

#### Scenario: 查看版本列表
- **WHEN** 调用 GET /api/v1/skills/{skill_id}/versions
- **THEN** 系统 SHALL 按创建时间倒序返回所有版本，含 version/created_at/release_notes/is_default

### Requirement: 软删除 Skill
系统 SHALL 提供 `DELETE /api/v1/skills/{skill_id}` 端点（需认证）。对于 is_system=false 的 Skill，执行物理删除并级联清除 skill_nodes 和 SkillVersion。对于 is_system=true 的 Skill，仅 role=0 超管可执行删除。

#### Scenario: 删除自定义 Skill 成功
- **WHEN** Skill 所有者调用 DELETE is_system=false 的 Skill
- **THEN** 系统 SHALL 物理删除 Skill 及关联的 skill_nodes、SkillVersion，返回 204

#### Scenario: 非超管删除系统 Skill 被拒绝
- **WHEN** role ≥ 1 的用户调用 DELETE is_system=true 的 Skill
- **THEN** 系统 SHALL 返回 422，提示"系统预设技能集不可删除"
