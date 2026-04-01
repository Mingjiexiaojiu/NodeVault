## MODIFIED Requirements

### Requirement: Global namespaces list
系统 SHALL 提供 `GET /api/v1/admin/namespaces` 端点，返回所有团队及其成员数量、节点数量。响应 SHALL 包含 organization_name 和 team_name 字段，替代原 slug 字段。

#### Scenario: List all namespaces
- **WHEN** 超管请求 `GET /admin/namespaces`
- **THEN** 系统返回所有团队，含 organization_name/team_name/owner/member_count/node_count 字段

### Requirement: Global nodes list
系统 SHALL 提供 `GET /api/v1/admin/nodes` 端点，返回所有节点。节点响应 SHALL 包含 organization_name 和 team_name 字段，替代原 department_slug。

#### Scenario: List all nodes across namespaces
- **WHEN** 超管请求 `GET /admin/nodes`
- **THEN** 系统返回所有节点，含 organization_name/team_name/owner_id/visibility/status 字段

### Requirement: 管理后台创建团队
`POST /api/v1/admin/departments` 端点 SHALL 接受 org_name 和 team_name 字段，替代原 slug 和 display_name。

#### Scenario: 管理后台创建团队
- **WHEN** 超管通过管理后台创建团队，提交 org_name 和 team_name
- **THEN** 系统 SHALL 按创建团队流程处理（组织不存在则自动创建）
