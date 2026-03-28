## ADDED Requirements

### Requirement: 更新凭据
系统 SHALL 提供 `PATCH /api/v1/credentials/{id}` 端点（需认证），允许用户更新自己凭据的 `name`、`token_ttl`，以及重新设置密码/token/api_key（覆盖加密字段）。`auth_type` 和 `base_url` 不可修改。若更新了加密字段，系统 SHALL 同时清空该凭据的 token_cache（强制下次重新鉴权）。

#### Scenario: 更新凭据名称和 TTL
- **WHEN** 用户发送 PATCH 请求，body 包含 `{"name": "new-name", "token_ttl": 3600}`
- **THEN** 系统 SHALL 更新对应字段，返回更新后的凭据元数据

#### Scenario: 更新密码（bearer_login）
- **WHEN** 用户发送 PATCH 请求，body 包含 `{"password": "new-password"}`
- **THEN** 系统 SHALL 重新加密新密码，清空 token_cache，返回成功

#### Scenario: 不修改加密字段时保持原值
- **WHEN** PATCH body 中未包含 password/static_token/api_key_value 字段
- **THEN** 系统 SHALL 不覆盖现有加密数据

#### Scenario: 尝试修改 auth_type 或 base_url
- **WHEN** PATCH body 中包含 auth_type 或 base_url
- **THEN** 系统 SHALL 忽略这些字段（或返回 422 提示不可修改）

---

### Requirement: 测试凭据连接
系统 SHALL 提供 `POST /api/v1/credentials/{id}/test` 端点（需认证），验证该凭据是否能成功鉴权目标服务，返回 `{success: bool, message: str, latency_ms: int | null}`。测试不应写入或更新 token_cache。

#### Scenario: bearer_login 测试成功
- **WHEN** 以有效 bearer_login 凭据调用 test 端点
- **THEN** 系统 SHALL 用存储的账号密码请求 login_endpoint，返回 `{success: true, message: "连接成功", latency_ms: <数值>}`

#### Scenario: 鉴权失败（密码错误）
- **WHEN** 存储的凭据已过期或密码错误
- **THEN** 系统 SHALL 返回 `{success: false, message: "鉴权失败：服务返回 401"}` (HTTP 200)

#### Scenario: 服务不可达
- **WHEN** 目标服务 URL 无法连接（超时或 DNS 失败）
- **THEN** 系统 SHALL 返回 `{success: false, message: "连接超时：<url>"}` (HTTP 200)

#### Scenario: 非本人凭据
- **WHEN** 用户尝试测试不属于自己的凭据
- **THEN** 系统 SHALL 返回 404

---

## MODIFIED Requirements

### Requirement: Delete credential
The system SHALL allow users to delete their own credential records.

#### Scenario: Delete credential clears Node references
- **WHEN** user deletes a credential that is referenced by Nodes via credential_id
- **THEN** system SHALL set those Nodes' credential_id to null (not delete the Nodes) and delete the credential record

#### Scenario: Delete credential also removes token cache
- **WHEN** user deletes a credential
- **THEN** system SHALL delete all associated `credential_token_cache` rows before deleting the credential record, ensuring no orphaned cache entries remain
