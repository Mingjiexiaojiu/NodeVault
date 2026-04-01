## ADDED Requirements

### Requirement: Global nodes list
系统 SHALL 提供 `GET /api/v1/admin/nodes` 端点，返回所有 namespace 下的所有节点（忽略 visibility 限制），支持分页、按 namespace/status/category 过滤。

#### Scenario: List all nodes across namespaces
- **WHEN** 超管请求 `GET /admin/nodes`
- **THEN** 系统返回所有用户、所有 namespace 下的节点，含 namespace_id/owner_id/visibility/status 字段

#### Scenario: Filter by namespace
- **WHEN** 超管请求 `GET /admin/nodes?namespace_id=<id>`
- **THEN** 系统只返回该 namespace 下的节点

---

### Requirement: Force disable node
系统 SHALL 提供 `PATCH /api/v1/admin/nodes/{node_id}/status` 端点，允许超管将任意节点设为 `disabled` 或恢复 `active`。

#### Scenario: Force disable a node
- **WHEN** 超管 PATCH `{"status": "disabled"}` 到任意节点
- **THEN** 系统将该节点 status 更新为 disabled，后续调用返回 403

#### Scenario: Re-enable a node
- **WHEN** 超管 PATCH `{"status": "active"}` 到已禁用节点
- **THEN** 系统将该节点 status 恢复为 active

---

### Requirement: Global namespaces list
系统 SHALL 提供 `GET /api/v1/admin/namespaces` 端点，返回所有 namespace 及其成员数量、节点数量。

#### Scenario: List all namespaces
- **WHEN** 超管请求 `GET /admin/namespaces`
- **THEN** 系统返回所有 namespace，含 slug/owner/member_count/node_count 字段

---

### Requirement: Global skills list
系统 SHALL 提供 `GET /api/v1/admin/skills` 端点，返回所有 namespace 下的所有技能，支持分页。

#### Scenario: List all skills
- **WHEN** 超管请求 `GET /admin/skills`
- **THEN** 系统返回所有用户的所有技能，含 namespace_id/owner_id/status 字段


---

## Changes from ux-naming-refactor

## MODIFIED Requirements

### Requirement: Global namespaces list（更新）
系统 SHALL 提供 `GET /api/v1/admin/namespaces` 端点，返回所有团队及其成员数量、节点数量。响应 SHALL 包含 organization_name 和 team_name 字段，替代原 slug 字段。

#### Scenario: List all namespaces
- **WHEN** 超管请求 `GET /admin/namespaces`
- **THEN** 系统返回所有团队，含 organization_name/team_name/owner/member_count/node_count 字段

### Requirement: Global nodes list（更新）
系统 SHALL 提供 `GET /api/v1/admin/nodes` 端点，返回所有节点。节点响应 SHALL 包含 organization_name 和 team_name 字段，替代原 department_slug。

#### Scenario: List all nodes across namespaces
- **WHEN** 超管请求 `GET /admin/nodes`
- **THEN** 系统返回所有节点，含 organization_name/team_name/owner_id/visibility/status 字段

### Requirement: 管理后台创建团队（更新）
`POST /api/v1/admin/departments` 端点 SHALL 接受 org_name 和 team_name 字段，替代原 slug 和 display_name。

#### Scenario: 管理后台创建团队
- **WHEN** 超管通过管理后台创建团队，提交 org_name 和 team_name
- **THEN** 系统 SHALL 按创建团队流程处理（组织不存在则自动创建）
