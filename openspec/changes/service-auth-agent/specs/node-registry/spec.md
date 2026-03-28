## ADDED Requirements

### Requirement: 创建 Node 时绑定凭据
`POST /api/v1/nodes` 的 `NodeCreate` 请求体 SHALL 支持可选的 `credential_id`（UUID）字段。当提供该字段时，系统 SHALL 将其写入所创建 NodeVersion 的 `runtime_config.credential_id`，以便调用时使用该凭据进行服务鉴权。

#### Scenario: 创建 Node 时指定 credential_id
- **WHEN** 用户提交包含 `credential_id` 的 NodeCreate 请求
- **THEN** 系统 SHALL 将 credential_id 写入 NodeVersion.runtime_config，NodeResponse 中 SHALL 包含 `credential_id` 字段

#### Scenario: 创建 Node 时不指定 credential_id
- **WHEN** 用户提交不含 `credential_id` 的 NodeCreate 请求
- **THEN** 系统 SHALL 按原有逻辑创建 Node，runtime_config 中不含 credential_id

---

### Requirement: 编辑 Node 时绑定或解绑凭据
`PATCH /api/v1/nodes/{node_id}` 的 `NodeUpdate` 请求体 SHALL 支持可选的 `credential_id`（UUID 或 null）字段。当提供 UUID 时，系统 SHALL 更新默认版本的 `runtime_config.credential_id`；当提供 null 时，系统 SHALL 清除该字段（解绑凭据）。

#### Scenario: 编辑 Node 绑定凭据
- **WHEN** 用户发送包含 `credential_id: "<uuid>"` 的 PATCH 请求
- **THEN** 系统 SHALL 更新 Node 默认版本的 runtime_config.credential_id，返回更新后的 NodeResponse

#### Scenario: 编辑 Node 解绑凭据
- **WHEN** 用户发送包含 `credential_id: null` 的 PATCH 请求
- **THEN** 系统 SHALL 将 Node 默认版本的 runtime_config 中的 credential_id 字段删除（或置为 null）

---

### Requirement: Node 响应携带凭据绑定信息
`NodeResponse` 和 `NodeDetailResponse` SHALL 包含可选的 `credential_id`（UUID | null）字段，从 Node 默认版本的 runtime_config 中读取，方便前端展示当前绑定状态。

#### Scenario: 查看已绑定凭据的 Node
- **WHEN** 获取一个已绑定 credential_id 的 Node 详情
- **THEN** 响应 SHALL 包含 `credential_id` 字段（UUID 字符串）

#### Scenario: 查看未绑定凭据的 Node
- **WHEN** 获取一个未绑定 credential_id 的 Node 详情
- **THEN** 响应中 `credential_id` SHALL 为 null
