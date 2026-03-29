## ADDED Requirements

### Requirement: Create encrypted credential
The system SHALL allow users to create a credential record for a target service, encrypting sensitive fields (password, static token, API key) with AES-256-GCM before storage.

#### Scenario: Create bearer_login credential
- **WHEN** user provides base_url, login_endpoint, username, password, and token_json_path
- **THEN** system SHALL encrypt the username and password, store them in `service_credentials`, and return the credential ID and metadata (without plaintext secrets)

#### Scenario: Create bearer_static credential
- **WHEN** user provides base_url and a static bearer token
- **THEN** system SHALL encrypt the token and store it in `service_credentials`

#### Scenario: Create api_key credential
- **WHEN** user provides base_url, API key header name, and API key value
- **THEN** system SHALL encrypt the API key value and store it

#### Scenario: Create basic auth credential
- **WHEN** user provides base_url, username, and password for HTTP Basic auth
- **THEN** system SHALL encrypt the credentials and store them

### Requirement: List credentials
The system SHALL allow users to list their own credential records, showing metadata without revealing plaintext secrets.

#### Scenario: List user credentials
- **WHEN** user requests their credential list
- **THEN** system SHALL return each credential's id, name, base_url, auth_type, created_at, and last_used_at, with sensitive fields masked (e.g., username shown, password hidden)

### Requirement: Delete credential
The system SHALL allow users to delete their own credential records.

#### Scenario: Delete credential clears Node references
- **WHEN** user deletes a credential that is referenced by Nodes via credential_id
- **THEN** system SHALL set those Nodes' credential_id to null (not delete the Nodes) and delete the credential record

#### Scenario: Delete credential also removes token cache
- **WHEN** user deletes a credential
- **THEN** system SHALL delete all associated `credential_token_cache` rows before deleting the credential record, ensuring no orphaned cache entries remain

### Requirement: Token caching
The system SHALL cache access tokens obtained from target services in `credential_token_cache` with an expiration timestamp.

#### Scenario: Token cached after login
- **WHEN** system obtains a token by logging into a target service
- **THEN** system SHALL store the token and its expiration time in the cache, associated with the credential ID

#### Scenario: Cached token returned when valid
- **WHEN** a cached token exists and has not expired (with 60-second safety margin)
- **THEN** system SHALL return the cached token without re-authenticating

### Requirement: Automatic token refresh
The system SHALL automatically refresh expired tokens during invoke by re-authenticating with stored credentials.

#### Scenario: Token expired, auto-refresh succeeds
- **WHEN** an invoke operation needs a token but the cached token is expired
- **THEN** system SHALL decrypt the credential, authenticate against the target service, cache the new token, and proceed with the invoke

#### Scenario: Auto-refresh fails
- **WHEN** the target service rejects the stored credentials during auto-refresh
- **THEN** system SHALL return an error indicating authentication failure and suggest the user update their credentials

#### Scenario: Token rejected mid-request, retry once
- **WHEN** the target service returns 401 during an invoke even though the token was not expired
- **THEN** system SHALL force-refresh the token once and retry the request; if still 401, return an authentication error

### Requirement: Encryption key management
The system SHALL read the AES-256 encryption key from environment variable `CREDENTIAL_ENCRYPT_KEY`. The key MUST be exactly 32 bytes (provided as 64-char hex or 44-char base64).

#### Scenario: Missing encryption key
- **WHEN** `CREDENTIAL_ENCRYPT_KEY` is not set and a credential operation is attempted
- **THEN** system SHALL return an error indicating the encryption key is not configured

#### Scenario: Invalid encryption key format
- **WHEN** `CREDENTIAL_ENCRYPT_KEY` is set but is not a valid 32-byte key
- **THEN** system SHALL fail fast at startup with a clear error message

### Requirement: Credential secrets never returned in API responses
The system SHALL never include plaintext passwords, tokens, or API keys in any API response.

#### Scenario: Create credential response
- **WHEN** a credential is successfully created
- **THEN** the response SHALL include the credential ID, name, base_url, auth_type, and created_at, but SHALL NOT include password, token, or API key values

#### Scenario: Get credential detail
- **WHEN** user requests a specific credential's details
- **THEN** the response SHALL show the username (if applicable) but SHALL mask or omit all secret fields

---

## Changes from service-auth-agent

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
