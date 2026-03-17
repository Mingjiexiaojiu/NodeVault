## ADDED Requirements

### Requirement: 调用完成后更新统计计数
系统 SHALL 在每次 Node 调用完成（无论成功或失败）后，递增 `nodes.invocation_count` 字段，以支持搜索热度排序和统计查询。更新操作 SHALL 以异步/非阻塞方式执行，不影响调用响应时间。

#### Scenario: 成功调用后计数递增
- **WHEN** Node 调用成功返回
- **THEN** 该 Node 的 `invocation_count` SHALL 在后台递增 1

#### Scenario: 失败调用后计数递增
- **WHEN** Node 调用失败（超时或目标服务错误）
- **THEN** 该 Node 的 `invocation_count` SHALL 同样递增 1（不区分成功失败）

#### Scenario: 计数更新失败不影响调用结果
- **WHEN** 统计计数写入数据库失败
- **THEN** 系统 SHALL 记录告警日志，但调用响应 SHALL 已正常返回，不因计数失败而改变
