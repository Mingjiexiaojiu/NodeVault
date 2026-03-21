## MODIFIED Requirements

### Requirement: 注册 Node
系统 SHALL 提供 `POST /api/v1/nodes` 端点（需认证），接受 `NodeCreate` 请求体，在调用者的默认 Namespace 下创建 Node 记录和 v1.0.0 NodeVersion 记录。Node `name` 在同一 Namespace 内 SHALL 唯一。请求体 SHALL 包含必填字段 `category_id`（UUID，指向 categories 表）。

#### Scenario: 注册 Node 成功
- **WHEN** 已认证用户提供合法的 NodeCreate 请求体（name/category_id/input_schema/output_schema/runtime 均有效）
- **THEN** 系统 SHALL 创建 Node 和 NodeVersion 记录，返回 201 和 NodeResponse（含 id/name/category_id/category_name/status/版本号）

#### Scenario: 同命名空间内 name 重复
- **WHEN** 同一用户尝试注册与已有 Node 同名的新 Node
- **THEN** 系统 SHALL 返回 409，提示名称在该命名空间已存在

#### Scenario: 字段校验复用 NodeSchemaBase 规则
- **WHEN** 提供不符合 snake_case 的 name 或不符合 SemVer 的 version
- **THEN** 系统 SHALL 返回 422 并说明具体字段的校验错误

#### Scenario: category_id 不存在时注册失败
- **WHEN** 提供的 category_id 在 categories 表中不存在
- **THEN** 系统 SHALL 返回 422，提示"指定的分类不存在"

### Requirement: 查询 Node 列表
系统 SHALL 提供 `GET /api/v1/nodes` 端点（需认证），返回当前用户有权访问的 Node 列表，支持按 `category_id`、`status`、`tag`、`source_credential_id` 过滤，支持 `page` / `page_size` 分页（默认 page=1，page_size=20，最大 100）。

#### Scenario: 无过滤条件查询
- **WHEN** 不携带任何查询参数调用 GET /api/v1/nodes
- **THEN** 系统 SHALL 返回 200 和当前用户命名空间内的 Node 列表（已归档节点默认不返回）

#### Scenario: 按 category_id 过滤
- **WHEN** 携带 `?category_id=<uuid>` 查询参数
- **THEN** 系统 SHALL 只返回 category_id 匹配的 Node

#### Scenario: 按 tag 过滤
- **WHEN** 携带 `?tag=data` 查询参数
- **THEN** 系统 SHALL 只返回关联该 tag 的 Node

#### Scenario: 按 source_credential_id 过滤
- **WHEN** 携带 `?source_credential_id=<uuid>` 查询参数
- **THEN** 系统 SHALL 只返回来自该凭证的 Node

#### Scenario: 分页
- **WHEN** 携带 `?page=2&page_size=5`
- **THEN** 系统 SHALL 返回第 6-10 条记录

### Requirement: 更新 Node 元信息
系统 SHALL 提供 `PATCH /api/v1/nodes/{node_id}` 端点（需认证），允许更新 `display_name`、`description`、`category_id`、`visibility`、`status` 字段。`name` 创建后 SHALL NOT 被修改。更新成功后，系统 SHALL 同步更新 MeiliSearch 中对应 Node 的索引文档。

#### Scenario: 更新 category_id 成功
- **WHEN** Node 所有者 PATCH 更新 category_id 指向另一个有效分类
- **THEN** 系统 SHALL 返回 200 和更新后的 NodeResponse，含新 category_name

#### Scenario: 非所有者无法更新
- **WHEN** 非 Node 所有者尝试 PATCH 更新
- **THEN** 系统 SHALL 返回 403

#### Scenario: 更新后索引同步
- **WHEN** Node 元信息更新成功
- **THEN** 系统 SHALL 更新 MeiliSearch 中该 Node 的文档（category_name 字段替代旧 type 字段）

### Requirement: Node 注册时同步搜索索引
系统 SHALL 在 `POST /api/v1/nodes` 成功创建 Node 后，自动将该 Node 的可搜索字段（id/name/display_name/description/tags/category_name/status/namespace/invocation_count）同步到 MeiliSearch 索引。同步失败 SHALL 记录告警日志，但 NOT 影响 Node 注册的成功响应。

#### Scenario: 注册 Node 后索引同步
- **WHEN** 成功注册一个新 Node
- **THEN** 系统 SHALL 向 MeiliSearch 写入该 Node 的文档（含 category_name），使其可被搜索接口发现

#### Scenario: 索引同步失败不影响注册
- **WHEN** MeiliSearch 服务不可用，但 Node 注册数据库写入成功
- **THEN** 系统 SHALL 返回 201（注册成功），并记录索引同步失败的告警日志
