## ADDED Requirements

### Requirement: 创建 Skill
系统 SHALL 提供 `POST /api/v1/skills` 端点（需认证），创建一个新的 Skill 实体。Skill `name` 在同一 Namespace 内 SHALL 唯一，`name` 须为 kebab-case。

#### Scenario: 创建 Skill 成功
- **WHEN** 已认证用户提供合法的 name、display_name、description
- **THEN** 系统 SHALL 创建 Skill 记录，返回 201 和 SkillResponse（含 id/name/display_name/status/is_stale）

#### Scenario: name 重复
- **WHEN** 同一 Namespace 下已存在同名 Skill
- **THEN** 系统 SHALL 返回 409

#### Scenario: name 格式非法
- **WHEN** name 包含大写字母或下划线（非 kebab-case）
- **THEN** 系统 SHALL 返回 422

### Requirement: 查询 Skill 列表
系统 SHALL 提供 `GET /api/v1/skills` 端点（需认证），返回当前用户命名空间内的 Skill 列表，包含每个 Skill 的节点数量和最新版本号。

#### Scenario: 列出所有 Skill
- **WHEN** 调用 GET /api/v1/skills
- **THEN** 系统 SHALL 返回 SkillResponse 列表，每项含 node_count 和 latest_version 字段

#### Scenario: 已归档 Skill 不在默认列表中
- **WHEN** 不带 status 参数调用 GET /api/v1/skills
- **THEN** 系统 SHALL 不返回 status=archived 的 Skill

### Requirement: 获取 Skill 详情
系统 SHALL 提供 `GET /api/v1/skills/{skill_id}` 端点（需认证），返回 Skill 详情，含所属节点列表和版本历史。

#### Scenario: 获取存在的 Skill
- **WHEN** 使用有效的 skill_id
- **THEN** 系统 SHALL 返回 SkillDetailResponse，含 nodes 数组（每项含 node_id/name/usage_hint/status）和 versions 数组

#### Scenario: Skill 不存在
- **WHEN** skill_id 不存在
- **THEN** 系统 SHALL 返回 404

### Requirement: 更新 Skill 元信息
系统 SHALL 提供 `PATCH /api/v1/skills/{skill_id}` 端点（需认证），允许更新 display_name、description、status。

#### Scenario: 更新 description 成功
- **WHEN** Skill 所有者 PATCH 更新 description
- **THEN** 系统 SHALL 返回 200 和更新后的 SkillResponse

#### Scenario: 非所有者无法更新
- **WHEN** 非 Skill 所有者尝试 PATCH 更新
- **THEN** 系统 SHALL 返回 403

### Requirement: 软删除 Skill
系统 SHALL 提供 `DELETE /api/v1/skills/{skill_id}` 端点（需认证），将 Skill status 改为 `archived`，不物理删除。软删除后所属节点的 `skill_id` 保持不变，不自动解绑。

#### Scenario: 软删除成功
- **WHEN** Skill 所有者调用 DELETE
- **THEN** 系统 SHALL 返回 204，Skill status 变为 archived

### Requirement: is_stale 自动检测
系统 SHALL 在以下事件发生时自动将对应 Skill 的 `is_stale` 置为 `true`：节点的 `skill_id` 变更（加入/离开）、节点的 `usage_hint` 或 `description` 更新、节点发布新的默认版本。

#### Scenario: 节点 usage_hint 变更触发 is_stale
- **WHEN** 属于某 Skill 的节点更新了 usage_hint
- **THEN** 该 Skill 的 is_stale 字段 SHALL 被置为 true

#### Scenario: 生成新版本后 is_stale 重置
- **WHEN** 成功发布一个新的 SkillVersion
- **THEN** 该 Skill 的 is_stale 字段 SHALL 被重置为 false

### Requirement: SkillVersion 快照管理
系统 SHALL 提供 `GET /api/v1/skills/{skill_id}/versions` 列出版本历史，`POST /api/v1/skills/{skill_id}/versions` 保存并发布一个新版本。

#### Scenario: 发布新版本
- **WHEN** 用户提交 version（SemVer）、skill_md（SKILL.md 文本）和可选 release_notes
- **THEN** 系统 SHALL 创建 SkillVersion 记录，锁定当前所有节点的 node_version_id 快照，重置 is_stale=false，返回 201

#### Scenario: 版本号重复
- **WHEN** 提交与已有版本号相同的版本
- **THEN** 系统 SHALL 返回 409

#### Scenario: 查看版本列表
- **WHEN** 调用 GET /api/v1/skills/{skill_id}/versions
- **THEN** 系统 SHALL 按创建时间倒序返回所有版本，含 version/created_at/release_notes/is_default
