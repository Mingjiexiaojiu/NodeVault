## ADDED Requirements

### Requirement: 全文搜索 Node
系统 SHALL 提供 `GET /api/v1/search/nodes` 端点（需认证），基于 MeiliSearch 对 Node 进行全文搜索。请求参数包括 `q`（关键词，支持中英文，可为空）、`type`、`tags`（多值）、`namespace`、`status`（默认 active）、`sort`（relevance/latest/popular，默认 relevance）、`page`（默认 1）、`page_size`（默认 20，最大 100）。

#### Scenario: 关键词全文搜索
- **WHEN** 已认证用户携带 `?q=资金池检测` 调用 GET /api/v1/search/nodes
- **THEN** 系统 SHALL 返回 200，results 包含 name/description/tags 中匹配该关键词的 Node 列表，估算总数在 total 字段返回

#### Scenario: 按类型过滤
- **WHEN** 携带 `?type=analysis` 参数
- **THEN** 系统 SHALL 只返回 type=analysis 的 Node

#### Scenario: 按标签过滤（多标签）
- **WHEN** 携带 `?tags=finance&tags=risk` 参数
- **THEN** 系统 SHALL 只返回同时包含 finance 和 risk 标签的 Node

#### Scenario: 按热度排序
- **WHEN** 携带 `?sort=popular` 参数
- **THEN** 系统 SHALL 按 invocation_count 降序排列结果

#### Scenario: 空关键词返回所有活跃 Node
- **WHEN** 不携带 `q` 参数（或 q 为空字符串）
- **THEN** 系统 SHALL 返回当前命名空间内所有 active 状态的 Node（按热度排序）

#### Scenario: MeiliSearch 服务不可用
- **WHEN** MeiliSearch 连接失败
- **THEN** 系统 SHALL 返回 503，提示搜索服务暂不可用，不影响其他接口

---

### Requirement: 搜索自动补全
系统 SHALL 提供 `GET /api/v1/search/suggest` 端点（需认证），基于输入前缀返回 Node 名称建议，用于搜索框实时提示。参数：`q`（必填，最短 1 字符）、`limit`（默认 5，最大 10）。

#### Scenario: 输入前缀返回建议
- **WHEN** 已认证用户携带 `?q=detect` 调用 GET /api/v1/search/suggest
- **THEN** 系统 SHALL 返回不超过 limit 条的建议列表，每条含 name 和 display_name 字段

#### Scenario: 无匹配时返回空列表
- **WHEN** 输入前缀无任何匹配 Node
- **THEN** 系统 SHALL 返回 200 和空数组 `[]`

---

### Requirement: MeiliSearch 索引初始化
系统 SHALL 在应用启动时调用 `NodeSearchIndex.setup_index()` 完成索引配置，包括：可搜索字段（name/display_name/description/tags/keywords/category/team）、可过滤字段（type/status/visibility/namespace/tags/team）、可排序字段（created_at/updated_at/invocation_count）。初始化失败 SHALL 记录告警日志，但不阻止应用启动。

#### Scenario: 应用启动时索引初始化成功
- **WHEN** 应用启动且 MeiliSearch 可用
- **THEN** 系统 SHALL 完成索引配置，日志中无 MeiliSearch 错误

#### Scenario: 应用启动时 MeiliSearch 不可用
- **WHEN** 应用启动时 MeiliSearch 连接超时
- **THEN** 系统 SHALL 记录告警日志后继续启动，不抛出未捕获异常

---

### Requirement: 全量重建索引管理接口
系统 SHALL 提供 `POST /api/v1/search/reindex` 端点（需管理员权限），将数据库中所有 active 状态的 Node 批量同步到 MeiliSearch 索引。

#### Scenario: 重建索引成功
- **WHEN** 管理员调用 POST /api/v1/search/reindex
- **THEN** 系统 SHALL 返回 200，包含同步的 Node 数量

#### Scenario: 非管理员调用
- **WHEN** 普通用户调用 POST /api/v1/search/reindex
- **THEN** 系统 SHALL 返回 403


---

## Changes from ux-naming-refactor

## MODIFIED Requirements

### Requirement: MeiliSearch 索引初始化（更新）
系统 SHALL 在应用启动时调用 `NodeSearchIndex.setup_index()` 完成索引配置。可搜索字段 SHALL 更新为：name/display_name/description/tags/keywords/category/organization_name/team_name（替代原 `team` 字段）。可过滤字段 SHALL 更新为：type/status/visibility/tags/organization_name/team_name（替代原 `namespace`/`team` 字段）。可排序字段不变。

#### Scenario: 应用启动时索引初始化成功
- **WHEN** 应用启动且 MeiliSearch 可用
- **THEN** 系统 SHALL 完成索引配置，搜索字段包含 organization_name 和 team_name，不含原 team/namespace 字段

### Requirement: 搜索结果包含组织和团队信息
搜索返回的节点结果 SHALL 包含 organization_name 和 team_name 字段，替代原 department_slug。

#### Scenario: 搜索结果展示组织和团队
- **WHEN** 用户搜索节点
- **THEN** 搜索结果中每条记录 SHALL 包含 organization_name 和 team_name 字段
