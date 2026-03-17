## ADDED Requirements

### Requirement: HTTP 类型 Node 调用执行
系统 SHALL 提供 `POST /api/v1/nodes/{node_id}/invoke` 端点（需认证），对 `runtime.type=http` 的 Node 发起实际 HTTP 调用。调用者 SHALL 传入 `input` 字段（JSON 对象），系统 SHALL 将其转发到 Node 的 `runtime.endpoint`，返回目标服务的响应内容。

#### Scenario: 成功调用 HTTP Node
- **WHEN** 已认证用户调用 active 状态的 HTTP Node，input 合法，目标服务正常响应
- **THEN** 系统 SHALL 返回 200，包含 `output`（目标服务 JSON 响应）、`latency_ms`、`version`、`invocation_id`

#### Scenario: 调用非 active 状态的 Node
- **WHEN** 目标 Node 状态为 draft 或 archived
- **THEN** 系统 SHALL 返回 404，提示 Node 不存在或未激活

#### Scenario: 指定版本调用
- **WHEN** 请求体包含 `version: "1.1.0"`
- **THEN** 系统 SHALL 使用该指定版本的 runtime_config 执行调用，而非默认版本

#### Scenario: 默认版本调用
- **WHEN** 请求体不包含 `version` 字段
- **THEN** 系统 SHALL 使用 `is_default=true` 的版本执行调用

---

### Requirement: 调用超时处理
系统 SHALL 对 HTTP 调用设置超时时间（默认 30 秒，可在 runtime_config 中通过 `timeout` 字段以秒为单位覆盖）。超时后 SHALL 返回错误响应而非无限等待。

#### Scenario: 目标服务超时
- **WHEN** 目标服务在超时时间内未响应
- **THEN** 系统 SHALL 返回 502，提示调用超时，并在调用日志中记录 status=timeout

#### Scenario: 目标服务返回 HTTP 错误
- **WHEN** 目标服务返回 4xx/5xx 状态码
- **THEN** 系统 SHALL 返回 502，提示目标服务异常，并在日志中记录具体错误

---

### Requirement: 调用日志持久化
系统 SHALL 为每次 Node 调用（无论成功或失败）写入一条 `NodeInvocationLog` 记录，包含：`node_id`、`version`、`invoked_by`、`input_data`、`output_data`、`status`（success/failure/timeout）、`latency_ms`、`error_message`（失败时）、`created_at`。日志 SHALL 使用 `try/finally` 模式确保失败时也被记录。

#### Scenario: 成功调用后记录日志
- **WHEN** Node 调用成功
- **THEN** 系统 SHALL 写入 status=success 的调用日志，包含完整的 input_data 和 output_data

#### Scenario: 失败调用后记录日志
- **WHEN** Node 调用因超时或目标服务错误失败
- **THEN** 系统 SHALL 写入 status=failure 或 status=timeout 的日志，包含 error_message

---

### Requirement: 调用日志查询
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}/logs` 端点（需认证），返回该 Node 最近的调用日志，默认返回最新 50 条，按 `created_at` 倒序排列。

#### Scenario: 查询调用日志
- **WHEN** 调用 GET /api/v1/nodes/{node_id}/logs
- **THEN** 系统 SHALL 返回包含调用记录列表的 200 响应，每条记录包含 id/version/status/latency_ms/created_at

#### Scenario: 无调用记录时
- **WHEN** 该 Node 从未被调用过
- **THEN** 系统 SHALL 返回 200 和空列表 `[]`

---

### Requirement: HTTP 执行器认证支持
`HTTPExecutor` SHALL 支持从 `runtime_config.auth` 读取认证配置，支持两种认证方式：
- `bearer`：从环境变量读取 token，添加 `Authorization: Bearer <token>` 请求头
- `api_key`：从环境变量读取 key，添加自定义请求头（默认 `X-API-Key`）

#### Scenario: Bearer Token 认证
- **WHEN** runtime_config.auth.type 为 bearer，且 token_env 指定的环境变量存在
- **THEN** HTTPExecutor SHALL 在转发请求时携带正确的 Authorization 请求头

#### Scenario: 无认证配置
- **WHEN** runtime_config 不包含 auth 字段
- **THEN** HTTPExecutor SHALL 不添加任何认证请求头，直接转发

---

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
