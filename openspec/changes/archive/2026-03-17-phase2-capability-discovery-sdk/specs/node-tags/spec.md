## ADDED Requirements

### Requirement: 热门标签查询
系统 SHALL 提供 `GET /api/v1/tags` 端点（需认证），统计当前命名空间内各标签关联的 active Node 数量，返回按关联数量降序的标签列表。参数：`domain`（可选，按 domain: 前缀过滤）、`limit`（默认 20，最大 100）。

#### Scenario: 获取热门标签
- **WHEN** 已认证用户调用 GET /api/v1/tags
- **THEN** 系统 SHALL 返回 200，包含标签名和对应的 Node 数量，按关联数量降序排列

#### Scenario: 按 domain 过滤标签
- **WHEN** 携带 `?domain=finance` 参数
- **THEN** 系统 SHALL 只返回以 `finance:` 开头或 domain 分类为 finance 的标签

#### Scenario: 无 Node 时返回空列表
- **WHEN** 当前命名空间无任何 active Node
- **THEN** 系统 SHALL 返回 200 和空数组 `[]`

---

### Requirement: 按标签浏览 Node
系统 SHALL 提供 `GET /api/v1/tags/{tag}/nodes` 端点（需认证），返回带有指定标签的所有 active Node 列表，支持 `page` / `page_size` 分页。

#### Scenario: 按标签获取 Node 列表
- **WHEN** 已认证用户调用 GET /api/v1/tags/finance/nodes
- **THEN** 系统 SHALL 返回 200，包含所有带有 finance 标签的 active Node 列表

#### Scenario: 标签不存在或无关联 Node
- **WHEN** 请求的标签无任何关联 Node
- **THEN** 系统 SHALL 返回 200 和空列表 `[]`，NOT 返回 404

#### Scenario: 分页查询
- **WHEN** 携带 `?page=2&page_size=10` 参数
- **THEN** 系统 SHALL 返回对应分页的 Node 列表及总数
