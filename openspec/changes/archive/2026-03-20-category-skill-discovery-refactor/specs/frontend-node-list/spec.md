## ADDED Requirements

### Requirement: 节点列表展示与筛选
前端 SHALL 在 /nodes 页面展示节点列表，支持按分类、状态、可见性等条件筛选，以及按名称搜索。

#### Scenario: 分类筛选替代类型筛选
- **WHEN** 用户打开节点列表页面
- **THEN** 筛选区域 SHALL 展示「分类」下拉，选项从 `GET /api/v1/categories` 动态加载，选择后传 category_id 参数到后端查询接口
- **AND** 不再显示旧的「类型」筛选下拉（NodeType 枚举）

#### Scenario: 节点卡片展示分类标签
- **WHEN** 节点列表渲染节点卡片 / 表格行
- **THEN** 每个节点 SHALL 展示其所属分类的 display_name 作为标签（badge），替代原有的 type 标签

#### Scenario: 分类数据加载失败时的降级
- **WHEN** `GET /api/v1/categories` 请求失败
- **THEN** 前端 SHALL 在分类筛选区显示"加载失败，点击重试"，节点列表正常展示但不显示分类标签（或显示"未分类"）
