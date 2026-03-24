## ADDED Requirements

### Requirement: Platform overview stats
系统 SHALL 提供 `GET /api/v1/admin/analytics/overview` 端点，返回平台级数据总览：总用户数、总节点数、总技能数、总调用次数、过去 24 小时新增用户数、过去 24 小时调用次数。

#### Scenario: Get platform overview
- **WHEN** 超管请求 `GET /admin/analytics/overview`
- **THEN** 系统返回 total_users/total_nodes/total_skills/total_invocations/new_users_24h/invocations_24h 字段

---

### Requirement: Invocation trend
系统 SHALL 提供 `GET /api/v1/admin/analytics/invocations` 端点，返回指定时间范围（7d/30d/90d）内每日调用量趋势数组。

#### Scenario: Get 30-day invocation trend
- **WHEN** 超管请求 `GET /admin/analytics/invocations?range=30d`
- **THEN** 系统返回最近 30 天每天的调用成功数和失败数数组

---

### Requirement: Top nodes ranking
系统 SHALL 提供 `GET /api/v1/admin/analytics/top-nodes` 端点，返回按调用次数排序的前 N 个节点（默认 10）。

#### Scenario: Get top 10 nodes
- **WHEN** 超管请求 `GET /admin/analytics/top-nodes`
- **THEN** 系统返回调用次数最多的 10 个节点，含节点名、namespace、owner、调用次数

---

### Requirement: Active users ranking
系统 SHALL 提供 `GET /api/v1/admin/analytics/top-users` 端点，返回按拥有节点数排序的前 N 个用户（默认 10）。

#### Scenario: Get top 10 active users
- **WHEN** 超管请求 `GET /admin/analytics/top-users`
- **THEN** 系统返回拥有节点数最多的 10 个用户，含用户名、节点数、技能数
