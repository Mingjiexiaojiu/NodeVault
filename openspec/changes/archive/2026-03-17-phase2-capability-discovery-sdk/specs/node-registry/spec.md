## ADDED Requirements

### Requirement: Node 注册时同步搜索索引
系统 SHALL 在 `POST /api/v1/nodes` 成功创建 Node 后，自动将该 Node 的可搜索字段（id/name/display_name/description/tags/type/status/namespace/invocation_count）同步到 MeiliSearch 索引。同步失败 SHALL 记录告警日志，但 NOT 影响 Node 注册的成功响应。

#### Scenario: 注册 Node 后索引同步
- **WHEN** 成功注册一个新 Node
- **THEN** 系统 SHALL 向 MeiliSearch 写入该 Node 的文档，使其可被搜索接口发现

#### Scenario: 索引同步失败不影响注册
- **WHEN** MeiliSearch 服务不可用，但 Node 注册数据库写入成功
- **THEN** 系统 SHALL 返回 201（注册成功），并记录索引同步失败的告警日志

---

## MODIFIED Requirements

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
