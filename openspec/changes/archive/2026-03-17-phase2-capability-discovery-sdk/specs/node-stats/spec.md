## ADDED Requirements

### Requirement: Node 调用统计查询
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}/stats` 端点（需认证），聚合该 Node 在指定时间段内的调用日志，返回：总调用量、成功率、平均延迟、P95/P99 延迟、每日调用趋势、Top 调用者列表。时间范围通过 `days` 参数控制（默认 30，最大 365）。

#### Scenario: 正常获取统计数据
- **WHEN** 已认证用户调用 GET /api/v1/nodes/{node_id}/stats
- **THEN** 系统 SHALL 返回 200，包含 total_invocations/success_rate/avg_latency_ms/p95_latency_ms/p99_latency_ms/daily_trend/top_callers 字段

#### Scenario: 指定时间范围
- **WHEN** 携带 `?days=7` 参数
- **THEN** 系统 SHALL 只统计最近 7 天内的调用日志

#### Scenario: 无调用记录时返回零值
- **WHEN** 该 Node 在指定时间段内无任何调用记录
- **THEN** 系统 SHALL 返回 200，total_invocations=0，success_rate=null，avg_latency_ms=null，daily_trend 为空数组

#### Scenario: Node 不存在或无权限
- **WHEN** 请求不存在的 node_id 或当前用户无访问权限
- **THEN** 系统 SHALL 返回 404

---

### Requirement: 调用统计数据来源
系统 SHALL 聚合 `invocation_logs` 表中对应 `node_id` 的记录计算统计值。P95/P99 延迟 SHALL 使用应用层排序计算（从最近 days 天的 latency_ms 值中取百分位数）。统计查询 SHALL 限定 `created_at >= now() - days` 范围以控制性能。

#### Scenario: invocation_logs 索引加速查询
- **WHEN** 执行统计查询时
- **THEN** 数据库 SHALL 能利用 `(node_id, created_at)` 复合索引避免全表扫描

#### Scenario: days 参数边界校验
- **WHEN** 请求携带 `?days=500`（超过最大值 365）
- **THEN** 系统 SHALL 返回 422，提示 days 超出允许范围
