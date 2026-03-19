## MODIFIED Requirements

### Requirement: 查询 Node 列表
系统 SHALL 提供 `GET /api/v1/nodes` 端点（需认证），返回当前用户有权访问的 Node 列表，支持按 `type`、`status`、`tag`、`source_credential_id` 过滤，支持 `page` / `page_size` 分页（默认 page=1，page_size=20，最大 100）。

#### Scenario: 无过滤条件查询
- **WHEN** 不携带任何查询参数调用 GET /api/v1/nodes
- **THEN** 系统 SHALL 返回 200 和当前用户命名空间内的 Node 列表（已归档节点默认不返回）

#### Scenario: 按 type 过滤
- **WHEN** 携带 `?type=nlp` 查询参数
- **THEN** 系统 SHALL 只返回 type 为 nlp 的 Node

#### Scenario: 按 tag 过滤
- **WHEN** 携带 `?tag=data` 查询参数
- **THEN** 系统 SHALL 只返回关联该 tag 的 Node

#### Scenario: 按 source_credential_id 过滤
- **WHEN** 携带 `?source_credential_id=<uuid>` 查询参数
- **THEN** 系统 SHALL 只返回来自该凭证的 Node

#### Scenario: 分页
- **WHEN** 携带 `?page=2&page_size=5`
- **THEN** 系统 SHALL 返回第 6-10 条记录
