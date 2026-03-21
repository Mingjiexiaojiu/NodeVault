## ADDED Requirements

### Requirement: NodeCreate Pydantic Schema 复用 NodeSchemaBase 校验规则
Phase 1 的 `NodeCreate` 请求体 Schema SHALL 沿用 Phase 0 `NodeSchemaBase` 已定义的所有字段校验规则（name snake_case 正则、version SemVer 正则、input/output_schema type=object 约束、http runtime 需要 endpoint+method）。`NodeCreate` SHALL 包含必填字段 `category_id`（UUID，引用 categories 表），不再包含 `type`（NodeType 枚举）字段。`skill_id` 和 `usage_hint` 字段从 NodeCreate 中移除。

#### Scenario: NodeCreate 校验 name 格式
- **WHEN** 通过 `POST /api/v1/nodes` 提交 name 为 `MyNode`（含大写）
- **THEN** 系统 SHALL 返回 422，校验错误信息与直接使用 NodeSchemaBase 时一致

#### Scenario: NodeCreate 校验 http runtime 完整性
- **WHEN** 通过 `POST /api/v1/nodes` 提交 runtime.type=http 但缺少 endpoint
- **THEN** 系统 SHALL 返回 422，提示 http runtime 需要 endpoint 字段

#### Scenario: NodeCreate 要求 category_id
- **WHEN** 通过 `POST /api/v1/nodes` 未提供 category_id
- **THEN** 系统 SHALL 返回 422，提示 category_id 为必填字段
