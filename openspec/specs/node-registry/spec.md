## Requirements
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

### Requirement: 获取 Node 详情
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}` 端点（需认证），返回指定 Node 的完整信息，包含当前默认版本的 input_schema/output_schema/runtime_config。

#### Scenario: 获取存在的 Node
- **WHEN** 使用有效的 node_id 调用 GET /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 200 和包含该 Node 完整信息与默认版本详情的 NodeDetailResponse

#### Scenario: Node 不存在
- **WHEN** 使用不存在的 node_id
- **THEN** 系统 SHALL 返回 404

---

### Requirement: Node 注册时同步搜索索引
系统 SHALL 在 `POST /api/v1/nodes` 成功创建 Node 后，自动将该 Node 的可搜索字段（id/name/display_name/description/tags/type/status/namespace/invocation_count）同步到 MeiliSearch 索引。同步失败 SHALL 记录告警日志，但 NOT 影响 Node 注册的成功响应。

#### Scenario: 注册 Node 后索引同步
- **WHEN** 成功注册一个新 Node
- **THEN** 系统 SHALL 向 MeiliSearch 写入该 Node 的文档，使其可被搜索接口发现

#### Scenario: 索引同步失败不影响注册
- **WHEN** MeiliSearch 服务不可用，但 Node 注册数据库写入成功
- **THEN** 系统 SHALL 返回 201（注册成功），并记录索引同步失败的告警日志

---

### Requirement: 更新 Node 元信息
系统 SHALL 提供 `PATCH /api/v1/nodes/{node_id}` 端点（需认证），允许更新 `display_name`、`description`、`category`、`visibility`、`status` 字段。`name` 和 `type` 创建后 SHALL NOT 被修改。更新成功后，系统 SHALL 同步更新 MeiliSearch 中对应 Node 的索引文档。

#### Scenario: 更新 display_name 成功
- **WHEN** Node 所有者 PATCH 更新 display_name 为新值
- **THEN** 系统 SHALL 返回 200 和更新后的 NodeResponse

#### Scenario: 非所有者无法更新
- **WHEN** 非 Node 所有者尝试 PATCH 更新
- **THEN** 系统 SHALL 返回 403

#### Scenario: 更新后索引同步
- **WHEN** Node 元信息更新成功
- **THEN** 系统 SHALL 更新 MeiliSearch 中该 Node 的文档，使搜索结果反映最新数据

---

### Requirement: 软删除 Node
系统 SHALL 提供 `DELETE /api/v1/nodes/{node_id}` 端点（需认证），将 Node status 改为 `archived`，不物理删除记录。已归档的 Node SHALL NOT 出现在默认列表查询结果中。软删除成功后，系统 SHALL 从 MeiliSearch 索引中删除该 Node 文档。

#### Scenario: 软删除成功
- **WHEN** Node 所有者调用 DELETE /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 204，Node status 变为 archived

#### Scenario: 归档后不出现在列表
- **WHEN** 调用 GET /api/v1/nodes（不带 status 过滤）
- **THEN** 系统 SHALL NOT 返回 status 为 archived 的 Node

#### Scenario: 归档后从搜索索引移除
- **WHEN** Node 被软删除后
- **THEN** 系统 SHALL 从 MeiliSearch 索引中删除该 Node 文档，使其不再出现在搜索结果中

---

### Requirement: Node 版本管理
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}/versions` 和 `POST /api/v1/nodes/{node_id}/versions` 端点（需认证），用于查看版本列表和发布新版本。同一 Node 下版本号 SHALL 唯一，新发布的版本如标记 `is_default=true` SHALL 替换旧的默认版本。

#### Scenario: 查看版本列表
- **WHEN** 调用 GET /api/v1/nodes/{node_id}/versions
- **THEN** 系统 SHALL 返回该 Node 所有版本，按创建时间倒序排列

#### Scenario: 发布新版本
- **WHEN** Node 所有者 POST 提交合法的 NodeVersionCreate（含新版本号、schemas、runtime）
- **THEN** 系统 SHALL 创建 NodeVersion 记录，返回 201

#### Scenario: 版本号重复拒绝
- **WHEN** 提交与已有版本号相同的新版本
- **THEN** 系统 SHALL 返回 409

---

### Requirement: Node runtime_config supports credential_id
The system SHALL support an optional `credential_id` field in Node's runtime_config. When present, the system SHALL use the referenced credential for authentication and combine the credential's `base_url` with the Node's relative `endpoint` to form the full request URL.

#### Scenario: Node created with credential_id
- **WHEN** a Node is created via batch import with `credential_id` referencing a valid credential
- **THEN** the Node's runtime_config SHALL contain `credential_id` and a relative `endpoint` (e.g., `/translate` instead of `https://api.xxx.com/translate`)

#### Scenario: Node without credential_id (backward compatible)
- **WHEN** an existing Node has no `credential_id` in its runtime_config
- **THEN** the system SHALL continue using the full `endpoint` URL and the existing `auth` config from runtime_config (no behavior change)

### Requirement: Batch create Nodes endpoint
The system SHALL provide `POST /api/v1/nodes/batch` endpoint that accepts an array of Node definitions and creates them all in a single transaction.

#### Scenario: Batch create succeeds
- **WHEN** authenticated user submits an array of 4 valid Node definitions with a shared credential_id
- **THEN** the system SHALL create all 4 Nodes and their initial versions in one transaction, returning 201 with an array of NodeResponse objects

#### Scenario: Batch create with name conflict
- **WHEN** one of the batch items has a name that conflicts with an existing Node in the namespace
- **THEN** the system SHALL reject the entire batch with 409, indicating which name(s) conflict

#### Scenario: Batch create atomic rollback
- **WHEN** any Node in the batch fails validation
- **THEN** the system SHALL rollback the entire transaction (no partial creates)

---

## Changes from superadmin-console

## MODIFIED Requirements

### Requirement: Node visibility bypass for superadmin
全局节点查询（`GET /api/v1/admin/nodes`）SHALL 忽略节点�?visibility 设置，返回所有节点，包括 private 节点。现有的 `GET /api/v1/nodes` 端点行为不变（仍�?namespace �?visibility 隔离）�?

#### Scenario: Superadmin sees private nodes in admin view
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 系统返回包含 visibility=private 的节�?

#### Scenario: Regular user still cannot see others' private nodes
- **WHEN** role=2 的用户请�?`GET /api/v1/nodes`
- **THEN** 系统仅返回该用户 namespace 内的节点或公开节点（行为不变）

---

## Changes from superadmin-console

## MODIFIED Requirements

### Requirement: Node visibility bypass for superadmin
全局节点查询（`GET /api/v1/admin/nodes`）SHALL 忽略节点�?visibility 设置，返回所有节点，包括 private 节点。现有的 `GET /api/v1/nodes` 端点行为不变（仍�?namespace �?visibility 隔离）�?

#### Scenario: Superadmin sees private nodes in admin view
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 系统返回包含 visibility=private 的节�?

#### Scenario: Regular user still cannot see others' private nodes
- **WHEN** role=2 的用户请�?`GET /api/v1/nodes`
- **THEN** 系统仅返回该用户 namespace 内的节点或公开节点（行为不变）

---

## Changes from superadmin-console

## MODIFIED Requirements

### Requirement: Node visibility bypass for superadmin
全局节点查询（`GET /api/v1/admin/nodes`）SHALL 忽略节点�?visibility 设置，返回所有节点，包括 private 节点。现有的 `GET /api/v1/nodes` 端点行为不变（仍�?namespace �?visibility 隔离）�?

#### Scenario: Superadmin sees private nodes in admin view
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 系统返回包含 visibility=private 的节�?

#### Scenario: Regular user still cannot see others' private nodes
- **WHEN** role=2 的用户请�?`GET /api/v1/nodes`
- **THEN** 系统仅返回该用户 namespace 内的节点或公开节点（行为不变）


---

## Changes from service-auth-agent

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
