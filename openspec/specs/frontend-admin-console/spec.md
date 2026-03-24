## ADDED Requirements

### Requirement: Admin layout and route guard
前端 SHALL 提供独立的 `AdminLayout.vue` 布局组件，所有 `/admin/*` 路由使用此布局。路由守卫 SHALL 在 `beforeEach` 中验证当前用户 role === 0，否则重定向至 `/`。

#### Scenario: Superadmin navigates to admin area
- **WHEN** role=0 的已登录用户导航到 `/admin`
- **THEN** 系统显示 AdminLayout 及默认子页面（概览/用户管理）

#### Scenario: Regular user attempts to access admin route
- **WHEN** role=2 的用户直接在地址栏输入 `/admin/users`
- **THEN** 路由守卫将其重定向到 `/`，不加载管理页面

#### Scenario: Admin navigation sidebar
- **WHEN** 超管在管理区域内
- **THEN** 布局左侧显示包含「用户管理、全局节点、分类管理、平台统计、系统设置」的导航侧栏

---

### Requirement: User management page
前端 SHALL 提供 `/admin/users` 页面，展示所有用户列表，支持关键词搜索，支持封禁/解封/角色变更操作。

#### Scenario: View user list
- **WHEN** 超管访问 `/admin/users`
- **THEN** 页面展示用户表格，列包含：头像/用户名/邮箱/角色标签/状态/注册时间/操作

#### Scenario: Ban user from list
- **WHEN** 超管点击某用户行的「封禁」按钮并确认
- **THEN** 前端调用 PATCH status 接口，成功后该行状态标签更新为「已封禁」

#### Scenario: Change user role
- **WHEN** 超管点击角色标签并选择新角色
- **THEN** 前端调用 PATCH role 接口，成功后标签即时更新

---

### Requirement: Global nodes view page
前端 SHALL 提供 `/admin/nodes` 页面，展示全平台节点列表，支持按 namespace/status/category 过滤。

#### Scenario: View all nodes
- **WHEN** 超管访问 `/admin/nodes`
- **THEN** 页面展示节点表格，列包含：节点名/所属Namespace/所有者/分类/状态/调用次数/操作

#### Scenario: Force disable node
- **WHEN** 超管点击某节点行的「下线」按钮并确认
- **THEN** 前端调用 PATCH status 接口，成功后节点状态显示为「已禁用」

---

### Requirement: Platform analytics page
前端 SHALL 提供 `/admin/analytics` 页面，展示平台统计大盘，含概览卡片和调用趋势折线图。

#### Scenario: View platform overview
- **WHEN** 超管访问 `/admin/analytics`
- **THEN** 页面顶部展示 4 个数据卡（总用户/总节点/总技能/总调用），下方展示 30 天调用趋势折线图

#### Scenario: Switch time range
- **WHEN** 超管点击时间范围选择器（7d/30d/90d）
- **THEN** 折线图数据重新加载并刷新显示

---

### Requirement: System settings page
前端 SHALL 提供 `/admin/settings` 页面，展示系统配置项列表，支持内联编辑。

#### Scenario: Toggle open registration
- **WHEN** 超管在设置页面切换「开放注册」开关
- **THEN** 前端调用 PUT settings 接口，成功后给出 toast 提示「设置已保存」

#### Scenario: Edit platform announcement
- **WHEN** 超管在公告输入框输入内容并点击保存
- **THEN** 前端调用 PUT settings/platform_announcement 接口，成功后显示更新成功提示
