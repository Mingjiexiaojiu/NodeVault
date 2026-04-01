## ADDED Requirements

### Requirement: 分类管理页面
系统 SHALL 在 `/categories` 路由提供分类管理页面，展示所有分类的列表，含 display_name、图标、节点数量和是否为系统默认标识。仅 role ≤ 1 的用户可见此路由。

#### Scenario: 主管访问分类管理页
- **WHEN** role=1 的用户访问 /categories
- **THEN** 页面 SHALL 显示所有分类列表，系统默认分类带"系统"徽标，每项显示节点数量

#### Scenario: 普通用户无法访问
- **WHEN** role=2 的普通用户尝试访问 /categories
- **THEN** 系统 SHALL 重定向到首页或显示"无权限访问"提示

### Requirement: 创建分类表单
系统 SHALL 在分类管理页提供"新建分类"按钮，点击后展示创建表单（name/display_name/icon）。

#### Scenario: 创建自定义分类成功
- **WHEN** 用户填写合法 name 和 display_name 并提交
- **THEN** 系统 SHALL 调用 POST /api/v1/categories，成功后刷新列表

#### Scenario: name 格式校验
- **WHEN** 用户输入含大写字母的 name
- **THEN** 表单 SHALL 内联提示"名称须为小写字母、数字、下划线"

### Requirement: 删除分类确认
系统 SHALL 在删除分类时显示确认对话框，提示该分类下的节点数量。

#### Scenario: 删除有节点的分类提示
- **WHEN** 用户点击删除某个分类，该分类下有节点
- **THEN** 系统 SHALL 显示"该分类下有 N 个节点，无法删除"的错误提示

#### Scenario: 系统默认分类不显示删除按钮
- **WHEN** 分类列表中 is_default=true 的分类
- **THEN** 该行 SHALL NOT 显示删除按钮

### Requirement: 顶部导航分类入口
系统 SHALL 在 AppLayout 顶部导航栏中添加"分类"链接（位于"技能"之后），仅在当前用户 role ≤ 1 时渲染。

#### Scenario: 主管用户看到分类链接
- **WHEN** role=1 的用户登录后查看导航栏
- **THEN** 导航栏 SHALL 显示"分类"链接，点击跳转到 /categories

#### Scenario: 普通用户不显示分类链接
- **WHEN** role=2 的普通用户登录后查看导航栏
- **THEN** 导航栏 SHALL NOT 显示"分类"链接


---

## Changes from ux-naming-refactor

## MODIFIED Requirements

### Requirement: 创建分类表单（更新）
系统 SHALL 在分类管理页提供"新建分类"按钮，点击后展示创建表单。表单 SHALL 只包含"名称"（display_name）、"图标"（icon）字段，不再包含"标识"（name）字段。

#### Scenario: 创建自定义分类成功
- **WHEN** 用户填写合法 display_name 并提交
- **THEN** 系统 SHALL 调用 POST /api/v1/categories（只传 display_name 和可选 icon），成功后刷新列表

#### Scenario: display_name 重复提示
- **WHEN** 提交的 display_name 与已有分类重复
- **THEN** 系统 SHALL 显示错误提示"该分类名称已存在"

### Requirement: 分类列表展示（更新）
分类管理页列表 SHALL 不再展示"标识"列，直接以 display_name 作为主名称列展示。

#### Scenario: 分类列表只显示名称
- **WHEN** 用户访问分类管理页
- **THEN** 列表 SHALL 显示列：名称（display_name）、图标、节点数量、类型（系统/自定义）
