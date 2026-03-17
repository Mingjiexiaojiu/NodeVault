## ADDED Requirements

### Requirement: 注册 Node
系统 SHALL 提供 `POST /api/v1/nodes` 端点（需认证），接受 `NodeCreate` 请求体，在调用者的默认 Namespace 下创建 Node 记录和 v1.0.0 NodeVersion 记录。Node `name` 在同一 Namespace 内 SHALL 唯一。

#### Scenario: 注册 Node 成功
- **WHEN** 已认证用户提供合法的 NodeCreate 请求体（name/type/input_schema/output_schema/runtime 均有效）
- **THEN** 系统 SHALL 创建 Node 和 NodeVersion 记录，返回 201 和 NodeResponse（含 id/name/type/status/版本号）

#### Scenario: 同命名空间内 name 重复
- **WHEN** 同一用户尝试注册与已有 Node 同名的新 Node
- **THEN** 系统 SHALL 返回 409，提示名称在该命名空间已存在

#### Scenario: 字段校验复用 NodeSchemaBase 规则
- **WHEN** 提供不符合 snake_case 的 name 或不符合 SemVer 的 version
- **THEN** 系统 SHALL 返回 422 并说明具体字段的校验错误

---

### Requirement: 查询 Node 列表
系统 SHALL 提供 `GET /api/v1/nodes` 端点（需认证），返回当前用户有权访问的 Node 列表，支持按 `type`、`status`、`tag` 过滤，支持 `page` / `page_size` 分页（默认 page=1，page_size=20，最大 100）。

#### Scenario: 无过滤条件查询
- **WHEN** 不携带任何查询参数调用 GET /api/v1/nodes
- **THEN** 系统 SHALL 返回 200 和当前用户命名空间内的 Node 列表（已归档节点默认不返回）

#### Scenario: 按 type 过滤
- **WHEN** 携带 `?type=nlp` 查询参数
- **THEN** 系统 SHALL 只返回 type 为 nlp 的 Node

#### Scenario: 按 tag 过滤
- **WHEN** 携带 `?tag=data` 查询参数
- **THEN** 系统 SHALL 只返回关联该 tag 的 Node

#### Scenario: 分页
- **WHEN** 携带 `?page=2&page_size=5`
- **THEN** 系统 SHALL 返回第 6-10 条记录

---

### Requirement: 获取 Node 详情
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}` 端点（需认证），返回指定 Node 的完整信息，包含当前默认版本的 input_schema/output_schema/runtime_config。

#### Scenario: 获取存在的 Node
- **WHEN** 使用有效的 node_id 调用 GET /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 200 和包含该 Node 完整信息与默认版本详情的 NodeDetailResponse

#### Scenario: Node 不存在
- **WHEN** 使用不存在的 node_id
- **THEN** 系统 SHALL 返回 404

---

### Requirement: 更新 Node 元信息
系统 SHALL 提供 `PATCH /api/v1/nodes/{node_id}` 端点（需认证），允许更新 `display_name`、`description`、`category`、`visibility`、`status` 字段。`name` 和 `type` 创建后 SHALL NOT 被修改。

#### Scenario: 更新 display_name 成功
- **WHEN** Node 所有者 PATCH 更新 display_name 为新值
- **THEN** 系统 SHALL 返回 200 和更新后的 NodeResponse

#### Scenario: 非所有者无法更新
- **WHEN** 非 Node 所有者尝试 PATCH 更新
- **THEN** 系统 SHALL 返回 403

---

### Requirement: 软删除 Node
系统 SHALL 提供 `DELETE /api/v1/nodes/{node_id}` 端点（需认证），将 Node status 改为 `archived`，不物理删除记录。已归档的 Node SHALL NOT 出现在默认列表查询结果中。

#### Scenario: 软删除成功
- **WHEN** Node 所有者调用 DELETE /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 204，Node status 变为 archived

#### Scenario: 归档后不出现在列表
- **WHEN** 调用 GET /api/v1/nodes（不带 status 过滤）
- **THEN** 系统 SHALL NOT 返回 status 为 archived 的 Node

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
