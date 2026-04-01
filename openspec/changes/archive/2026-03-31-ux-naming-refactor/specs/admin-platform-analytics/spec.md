## MODIFIED Requirements

### Requirement: Top nodes ranking
系统 SHALL 提供 `GET /api/v1/admin/analytics/top-nodes` 端点，返回按调用次数排序的前 N 个节点。响应 SHALL 包含 organization_name 和 team_name 字段，替代原 namespace/slug 字段。

#### Scenario: Get top 10 nodes
- **WHEN** 超管请求 `GET /admin/analytics/top-nodes`
- **THEN** 系统返回调用次数最多的 10 个节点，含节点名、organization_name、team_name、owner、调用次数
