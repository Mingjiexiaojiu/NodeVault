## MODIFIED Requirements

### Requirement: 注册 Node
系统 SHALL 提供 `POST /api/v1/nodes` 端点（需认证），接受 `NodeCreate` 请求体，在调用者指定的 `department_id` 所对应的 Department 下创建 Node 记录及 v1.0.0 NodeVersion 记录。Node `name` 在同一 Department 下 SHALL 唯一。请求体 SHALL 包含必填字段 `category_id`（UUID，关联 categories 表）和 `department_id`（UUID，关联 departments 表）。

#### Scenario: 注册 Node 成功
- **WHEN** 已认证用户提供合法的 NodeCreate 请求体（含 name/category_id/department_id/input_schema/output_schema/runtime 等）
- **THEN** 系统 SHALL 创建 Node 和 NodeVersion 记录，返回 201 和 NodeResponse（含 id/name/category_id/category_name/department_id/status/版本号）

#### Scenario: 同部门内 name 重复
- **WHEN** 同一用户尝试注册与已有 Node 同名的新 Node（同 department_id）
- **THEN** 系统 SHALL 返回 409，提示名称在该部门已存在

#### Scenario: 字段校验复用 NodeSchemaBase 规则
- **WHEN** 提供不符合 snake_case 的 name 或不符合 SemVer 的 version
- **THEN** 系统 SHALL 返回 422 并说明具体字段的校验错误

#### Scenario: category_id 不存在时注册失败
- **WHEN** 提供的 category_id 在 categories 表中不存在
- **THEN** 系统 SHALL 返回 422，提示"指定的分类不存在"

---

### Requirement: 查询 Node 列表
系统 SHALL 提供 `GET /api/v1/nodes` 端点（需认证），返回当前用户有权访问的 Node 列表，支持 `department_id`（替代 `namespace_id`）、`category_id`、`status`、`tag`、`source_credential_id` 过滤，支持 `page` / `page_size` 分页（默认 page=1，page_size=20，最大 100）。

#### Scenario: 无过滤条件查询
- **WHEN** 不携带任何查询参数调用 GET /api/v1/nodes
- **THEN** 系统 SHALL 返回 200 和当前用户当前部门内的 Node 列表（已归档节点默认不返回）

#### Scenario: 按 department_id 过滤
- **WHEN** 携带 `?department_id=<uuid>` 查询参数
- **THEN** 系统 SHALL 只返回属于该 department 的 Node

#### Scenario: 按 tag 过滤
- **WHEN** 携带 `?tag=data` 查询参数
- **THEN** 系统 SHALL 只返回关联该 tag 的 Node
