## ADDED Requirements

### Requirement: Probe spec paths for a given URL
The system SHALL accept a base URL and attempt to discover an OpenAPI Spec by sending GET requests to a configurable ordered list of common spec paths.

#### Scenario: Spec found at standard path
- **WHEN** user provides `https://api.example.com` and the service exposes `/openapi.json`
- **THEN** system SHALL return the parsed OpenAPI document and the discovered spec path

#### Scenario: Spec found at non-standard path
- **WHEN** user provides `https://api.example.com` and the first 3 paths return 404 but `/v3/api-docs` returns 200 with valid OpenAPI JSON
- **THEN** system SHALL return the parsed document from `/v3/api-docs`

#### Scenario: No spec found at any path
- **WHEN** all probe paths return 404 or non-OpenAPI content
- **THEN** system SHALL return a response indicating no spec was discovered, with available fallback options (manual path, upload file)

### Requirement: Support authenticated spec probing
The system SHALL support probing services that require authentication to access their spec endpoint.

#### Scenario: Spec endpoint returns 401 without credentials
- **WHEN** a probe path returns HTTP 401 or 403
- **THEN** system SHALL report that authentication is needed and await user-provided credentials

#### Scenario: Login with username and password to obtain token
- **WHEN** user provides a login endpoint, username, and password
- **THEN** system SHALL POST to the login endpoint, extract a token from the response, and retry the spec probe with `Authorization: Bearer <token>`

#### Scenario: Smart token extraction from login response
- **WHEN** the login response JSON contains multiple string fields
- **THEN** system SHALL identify candidate token fields by checking for JWT prefix `eyJ` or key names containing `token`/`jwt`/`access`, and use the best match

### Requirement: Default probe paths list
The system SHALL maintain a built-in ordered list of probe paths including at minimum: `/openapi.json`, `/swagger.json`, `/openapi.yaml`, `/v3/api-docs`, `/v2/api-docs`, `/api/schema/`, `/swagger/v1/swagger.json`, `/swagger/doc.json`.

#### Scenario: Default paths are tried in order
- **WHEN** probing begins with no custom paths
- **THEN** system SHALL try each default path in priority order, stopping at the first successful match

### Requirement: Extensible probe paths
The system SHALL allow adding custom probe paths to the global list when a user manually specifies a non-standard path that succeeds.

#### Scenario: User-specified path succeeds
- **WHEN** auto-probe fails and user manually enters `/custom/api-docs` which returns a valid spec
- **THEN** system SHALL offer to add `/custom/api-docs` to the global probe path list for future probes

### Requirement: Parse OpenAPI 2.x and 3.x
The system SHALL parse both Swagger 2.x and OpenAPI 3.x format documents (JSON and YAML).

#### Scenario: Swagger 2.x document
- **WHEN** the discovered spec has `"swagger": "2.0"`
- **THEN** system SHALL parse it and extract paths/operations correctly

#### Scenario: OpenAPI 3.x document
- **WHEN** the discovered spec has `"openapi": "3.x.x"`
- **THEN** system SHALL parse it and extract paths/operations correctly

### Requirement: SSRF protection
The system SHALL validate probe target URLs and reject requests to private/internal IP ranges to prevent Server-Side Request Forgery.

#### Scenario: Private IP rejected
- **WHEN** user submits `http://169.254.169.254/latest/meta-data` or `http://10.0.0.1/openapi.json`
- **THEN** system SHALL reject the request with an error indicating the target address is not allowed

#### Scenario: Admin whitelist allows private range
- **WHEN** environment variable `ALLOWED_PRIVATE_CIDRS` includes `10.0.0.0/8` and user submits `http://10.0.0.5/openapi.json`
- **THEN** system SHALL allow the probe to proceed

### Requirement: Probe timeout
The system SHALL enforce a per-path timeout of 5 seconds and a total probe timeout of 30 seconds.

#### Scenario: Single path times out
- **WHEN** a probe path does not respond within 5 seconds
- **THEN** system SHALL skip that path and continue to the next

#### Scenario: Total probe timeout
- **WHEN** the cumulative probe time exceeds 30 seconds
- **THEN** system SHALL stop probing and return results for paths already tried

### Requirement: Identify User-Agent
The system SHALL set the HTTP User-Agent header to `NodeVault/1.0 ServiceProbe` for all outgoing probe requests.

#### Scenario: Probe request headers
- **WHEN** system sends a GET request to a probe path
- **THEN** the request SHALL include `User-Agent: NodeVault/1.0 ServiceProbe`

### Requirement: 探测失败返回结构化错误类型
当服务探测失败时，系统 SHALL 在 ProbeResult 中包含 `error_type` 字段，值为以下枚举之一：connection_refused | timeout | dns_error | ssl_error | spec_not_found | parse_error。

#### Scenario: 连接被拒绝
- **WHEN** TCP 连接被目标拒绝
- **THEN** ProbeResult.error_type SHALL 为 "connection_refused"，message 为 "无法连接到目标服务，请确认地址和端口是否正确"

#### Scenario: 连接超时
- **WHEN** TCP 连接或 HTTP 请求超过 10 秒无响应
- **THEN** ProbeResult.error_type SHALL 为 "timeout"，message 为 "连接超时，请确认服务是否可达"

#### Scenario: DNS 解析失败
- **WHEN** 无法解析目标主机名
- **THEN** ProbeResult.error_type SHALL 为 "dns_error"，message 为 "域名无法解析，请检查 URL 是否正确"

#### Scenario: SSL 证书错误
- **WHEN** SSL 握手失败
- **THEN** ProbeResult.error_type SHALL 为 "ssl_error"，message 为 "SSL 证书验证失败"

#### Scenario: 无法找到 API 规范
- **WHEN** HTTP 连接成功但在标准路径均未找到有效规范
- **THEN** ProbeResult.error_type SHALL 为 "spec_not_found"，message 为 "服务可达但未找到 OpenAPI 规范文件"

#### Scenario: 规范解析失败
- **WHEN** 获取到文件但 JSON/YAML 解析或 OpenAPI schema 校验失败
- **THEN** ProbeResult.error_type SHALL 为 "parse_error"，message 为 "规范文件格式错误，解析失败"

### Requirement: 探测目标 URL
系统 SHALL 接受用户输入的 base_url，依次尝试标准路径获取 OpenAPI/Swagger 规范，解析成功后返回包含 spec_url / openapi_version / title / endpoints 的 ProbeResult。探测失败时 SHALL 返回包含 error_type 的结构化错误信息。

#### Scenario: 探测失败时返回结构化信息
- **WHEN** 探测过程中任何阶段出错
- **THEN** 系统 SHALL 返回 ProbeResult，其中 success=false，error_type 为上述枚举值之一，message 为对应中文提示信息
