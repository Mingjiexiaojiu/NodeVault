## Requirements

### Requirement: base_url 前缀自动匹配凭据
当调用 Node 时，如果 NodeVersion.runtime_config 中未显式设置 `credential_id`，系统 SHALL 自动在调用者所属凭据（owner_id）中查找 base_url 与 Node endpoint 匹配的凭据，并将其用于本次请求鉴权。匹配规则为最长前缀匹配（base_url 越长优先级越高）。

#### Scenario: 无显式绑定时自动匹配
- **WHEN** 调用一个 runtime_config 中无 credential_id 的 Node，且调用者拥有一个 base_url 是该 Node endpoint 前缀的凭据
- **THEN** 系统 SHALL 自动使用该凭据进行鉴权，请求正常转发

#### Scenario: 多个凭据匹配时取最长前缀
- **WHEN** 调用者有 base_url = "http://svc.company.com" 和 "http://svc.company.com/api" 两个凭据，Node endpoint 为 "http://svc.company.com/api/v1/score"
- **THEN** 系统 SHALL 使用 base_url 较长的凭据（"http://svc.company.com/api"）

#### Scenario: 无匹配凭据时不报错
- **WHEN** Node 无显式 credential_id，且调用者无任何 base_url 匹配的凭据
- **THEN** 系统 SHALL 不附加任何鉴权头，按无鉴权模式发送请求（与原有行为一致）

#### Scenario: 显式绑定优先于自动匹配
- **WHEN** Node 的 runtime_config 中已设置 credential_id
- **THEN** 系统 SHALL 使用显式绑定的凭据，不触发自动匹配逻辑

---

### Requirement: 自动匹配不影响调用日志
自动匹配使用的凭据信息 SHALL 不暴露在 NodeInvocationLog 中，以避免敏感信息泄露。日志中不记录鉴权使用的 credential_id。

#### Scenario: 调用日志不含 credential 信息
- **WHEN** 通过自动匹配凭据成功调用 Node
- **THEN** `node_invocation_logs` 表中 SHALL 不记录 credential_id 或 token 信息
