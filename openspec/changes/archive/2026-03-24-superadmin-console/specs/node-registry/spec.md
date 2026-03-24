## MODIFIED Requirements

### Requirement: Node visibility bypass for superadmin
全局节点查询（`GET /api/v1/admin/nodes`）SHALL 忽略节点的 visibility 设置，返回所有节点，包括 private 节点。现有的 `GET /api/v1/nodes` 端点行为不变（仍受 namespace 与 visibility 隔离）。

#### Scenario: Superadmin sees private nodes in admin view
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 系统返回包含 visibility=private 的节点

#### Scenario: Regular user still cannot see others' private nodes
- **WHEN** role=2 的用户请求 `GET /api/v1/nodes`
- **THEN** 系统仅返回该用户 namespace 内的节点或公开节点（行为不变）
