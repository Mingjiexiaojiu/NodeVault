## ADDED Requirements

### Requirement: Node Schema v1.0 YAML 结构定义
系统 SHALL 定义标准化的 Node Schema v1.0 格式（YAML），包含以下顶级字段：`name`、`version`、`display_name`、`description`、`type`、`tags`、`category`、`keywords`、`author`、`team`、`email`、`namespace`、`input_schema`、`output_schema`、`runtime`、`timeout`、`retry`、`rate_limit`、`dependencies`、`status`、`visibility`、`license`、`created_at`、`updated_at`。

#### Scenario: 完整 Node Schema 示例可通过验证
- **WHEN** 提供一个包含所有必填字段（name、version、type、input_schema、output_schema、runtime）的 YAML Node 定义
- **THEN** 系统 SHALL 验证通过，返回解析后的 Node 对象

#### Scenario: 缺少必填字段时拒绝
- **WHEN** 提供一个缺少 `name` 或 `version` 或 `type` 或 `runtime` 字段的 YAML Node 定义
- **THEN** 系统 SHALL 返回验证错误，明确指出缺失的字段名

### Requirement: Node name 唯一标识符规范
`name` 字段 SHALL 使用 snake_case 格式，全局唯一，仅允许小写字母、数字和下划线，长度 3-64 字符。

#### Scenario: 合法的 Node name
- **WHEN** Node name 为 `detect_fund_pool`
- **THEN** 验证通过

#### Scenario: 非法的 Node name
- **WHEN** Node name 为 `Detect-Fund-Pool` 或 `a` 或包含空格的字符串
- **THEN** 验证失败，提示 name 必须是 snake_case 格式

### Requirement: 语义化版本号
`version` 字段 SHALL 遵循 SemVer 规范（MAJOR.MINOR.PATCH），例如 `"1.0.0"`、`"2.1.3"`。

#### Scenario: 有效版本号
- **WHEN** version 为 `"1.0.0"` 或 `"0.1.0"` 或 `"10.20.30"`
- **THEN** 验证通过

#### Scenario: 无效版本号
- **WHEN** version 为 `"1.0"` 或 `"v1.0.0"` 或 `"abc"`
- **THEN** 验证失败

### Requirement: Node 类型枚举
`type` 字段 SHALL 限定为以下枚举值之一：`data_cleaning`、`analysis`、`risk`、`nlp`、`vision`、`ml`、`tool`、`utility`。

#### Scenario: 使用有效类型
- **WHEN** type 为 `analysis`
- **THEN** 验证通过

#### Scenario: 使用无效类型
- **WHEN** type 为 `unknown_type`
- **THEN** 验证失败，返回允许的类型列表

### Requirement: Runtime 类型枚举与配置
`runtime.type` 字段 SHALL 限定为以下枚举值之一：`http`、`grpc`、`docker`、`python`、`mcp`。当 `runtime.type` 为 `http` 时，SHALL 要求 `endpoint` 和 `method` 字段存在。

#### Scenario: HTTP Runtime 配置
- **WHEN** runtime.type 为 `http` 且提供了 endpoint 和 method
- **THEN** 验证通过

#### Scenario: HTTP Runtime 缺少 endpoint
- **WHEN** runtime.type 为 `http` 但未提供 endpoint
- **THEN** 验证失败

### Requirement: 输入输出 Schema 使用 JSON Schema
`input_schema` 和 `output_schema` SHALL 使用 JSON Schema（draft-07 兼容）格式定义，`type` 字段固定为 `object`。

#### Scenario: 合法的 input_schema
- **WHEN** input_schema 包含 `type: object` 和 `properties` 定义
- **THEN** 验证通过

#### Scenario: input_schema type 非 object
- **WHEN** input_schema 的 type 为 `array` 或 `string`
- **THEN** 验证失败，提示 input_schema.type 必须为 object

### Requirement: Node 状态枚举
`status` 字段 SHALL 限定为：`draft`、`active`、`deprecated`、`archived`，默认值为 `draft`。

#### Scenario: 未提供 status 字段
- **WHEN** 注册 Node 时未指定 status
- **THEN** 系统自动设置 status 为 `draft`

### Requirement: Node 可见性枚举
`visibility` 字段 SHALL 限定为：`public`、`internal`、`private`，默认值为 `internal`。

#### Scenario: 未提供 visibility 字段
- **WHEN** 注册 Node 时未指定 visibility
- **THEN** 系统自动设置 visibility 为 `internal`
