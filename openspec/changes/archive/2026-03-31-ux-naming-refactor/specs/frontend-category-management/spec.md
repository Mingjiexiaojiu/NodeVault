## MODIFIED Requirements

### Requirement: 创建分类表单
系统 SHALL 在分类管理页提供"新建分类"按钮，点击后展示创建表单。表单 SHALL 只包含"名称"（display_name）、"图标"（icon）字段，不再包含"标识"（name）字段。

#### Scenario: 创建自定义分类成功
- **WHEN** 用户填写合法 display_name 并提交
- **THEN** 系统 SHALL 调用 POST /api/v1/categories（只传 display_name 和可选 icon），成功后刷新列表

#### Scenario: display_name 重复提示
- **WHEN** 提交的 display_name 与已有分类重复
- **THEN** 系统 SHALL 显示错误提示"该分类名称已存在"

### Requirement: 分类列表展示
分类管理页列表 SHALL 不再展示"标识"列，直接以 display_name 作为主名称列展示。

#### Scenario: 分类列表只显示名称
- **WHEN** 用户访问分类管理页
- **THEN** 列表 SHALL 显示列：名称（display_name）、图标、节点数量、类型（系统/自定义）
