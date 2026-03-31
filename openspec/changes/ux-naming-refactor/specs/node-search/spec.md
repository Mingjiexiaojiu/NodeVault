## MODIFIED Requirements

### Requirement: MeiliSearch 索引初始化
系统 SHALL 在应用启动时调用 `NodeSearchIndex.setup_index()` 完成索引配置。可搜索字段 SHALL 包含 name/display_name/description/tags/keywords/category/organization_name/team_name（替代原 team 字段）。可过滤字段 SHALL 包含 type/status/visibility/namespace/tags/organization_name/team_name。可排序字段不变。

#### Scenario: 应用启动时索引初始化成功
- **WHEN** 应用启动且 MeiliSearch 可用
- **THEN** 系统 SHALL 完成索引配置，搜索字段包含 organization_name 和 team_name

### Requirement: 搜索结果包含组织和团队信息
搜索返回的节点结果 SHALL 包含 organization_name 和 team_name 字段，替代原 department_slug。

#### Scenario: 搜索结果展示组织和团队
- **WHEN** 用户搜索节点
- **THEN** 搜索结果中每条记录 SHALL 包含 organization_name 和 team_name 字段
