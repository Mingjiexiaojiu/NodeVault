## MODIFIED Requirements

### Requirement: Get user detail
系统 SHALL 提供 `GET /api/v1/admin/users/{user_id}` 端点，返回指定用户详情及其拥有的 **department** 数量（`department_count`）、node 数量、skill 数量。响应中 SHALL NOT 包含 `namespace_count` 字段。

#### Scenario: Get existing user detail
- **WHEN** 超管请求 `GET /admin/users/{valid_id}`
- **THEN** 系统返回用户完整信息及资源摘要统计，统计字段包含 `department_count`/`node_count`/`skill_count`

#### Scenario: Get non-existent user
- **WHEN** 超管请求一个不存在的 user_id
- **THEN** 系统返回 HTTP 404

## ADDED Requirements

### Requirement: 节点和技能管理后台列表字段
系统 SHALL 在 `GET /api/v1/admin/nodes` 和 `GET /api/v1/admin/skills` 响应的每条记录中使用 `department_id` 和 `department_slug` 字段（替代 `namespace_id` 和 `namespace_slug`）标识所属部门。

#### Scenario: 管理后台列出节点
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 每条节点记录 SHALL 包含 `department_id`（UUID）和 `department_slug`（string）字段，SHALL NOT 包含 `namespace_id` 或 `namespace_slug` 字段

#### Scenario: 管理后台列出技能
- **WHEN** 超管请求 `GET /api/v1/admin/skills`
- **THEN** 每条技能记录 SHALL 包含 `department_id` 和 `department_slug` 字段，SHALL NOT 包含 `namespace_id` 或 `namespace_slug` 字段
