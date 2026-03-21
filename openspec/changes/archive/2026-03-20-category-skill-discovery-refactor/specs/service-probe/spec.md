## ADDED Requirements

### Requirement: 探测失败返回结构化错误类型
当服务探测失败时，系统 SHALL 在 ProbeResult 中包含 `error_type` 字段，值为以下枚举之一：connection_refused | timeout | dns_error | ssl_error | spec_not_found | parse_error，以便前端可以渲染可读的提示信息。

#### Scenario: 连接被拒绝
- **WHEN** TCP 连接被目标拒绝（ConnectionRefusedError）
- **THEN** ProbeResult.error_type SHALL 为 "connection_refused"，message 为 "无法连接到目标服务，请确认地址和端口是否正确"

#### Scenario: 连接超时
- **WHEN** TCP 连接或 HTTP 请求超过 10 秒无响应
- **THEN** ProbeResult.error_type SHALL 为 "timeout"，message 为 "连接超时，请确认服务是否可达"

#### Scenario: DNS 解析失败
- **WHEN** 无法解析目标主机名
- **THEN** ProbeResult.error_type SHALL 为 "dns_error"，message 为 "域名无法解析，请检查 URL 是否正确"

#### Scenario: SSL 证书错误
- **WHEN** SSL 握手失败（证书过期、自签名等）
- **THEN** ProbeResult.error_type SHALL 为 "ssl_error"，message 为 "SSL 证书验证失败"

#### Scenario: 无法找到 API 规范
- **WHEN** HTTP 连接成功但在标准路径（/openapi.json, /swagger.json, /api-docs 等）均未找到有效规范
- **THEN** ProbeResult.error_type SHALL 为 "spec_not_found"，message 为 "服务可达但未找到 OpenAPI 规范文件"

#### Scenario: 规范解析失败
- **WHEN** 获取到文件但 JSON/YAML 解析或 OpenAPI schema 校验失败
- **THEN** ProbeResult.error_type SHALL 为 "parse_error"，message 为 "规范文件格式错误，解析失败"

## ADDED Requirements

### Requirement: 探测目标 URL
系统 SHALL 接受用户输入的 base_url，依次尝试标准路径获取 OpenAPI/Swagger 规范，解析成功后返回包含 spec_url / openapi_version / title / endpoints 的 ProbeResult。

#### Scenario: 探测成功（无变化）
（保持原有行为不变）

#### Scenario: 探测失败时返回结构化信息
- **WHEN** 探测过程中任何阶段出错
- **THEN** 系统 SHALL 返回 ProbeResult，其中 success=false，error_type 为上述枚举值之一，message 为对应中文提示信息；不再返回通用的错误字符串
