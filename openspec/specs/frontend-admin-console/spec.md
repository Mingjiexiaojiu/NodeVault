## Purpose
提供 NodeVault 管理员后台的前端页面结构、路由守卫及各管理模块 UI。
## Requirements
### Requirement: Admin layout and route guard
管理员导航栏 SHALL 包含 7 个 Tab 项，顺序为：`用户管理 | 全局节点 | 分类管理 | 平台统计 | 部门管理 | 申请管理 | 系统设置`。"平台统计"SHALL 位于第 4 个位置（正中间），"申请管理"SHALL 替换原"授权管理"。

#### Scenario: 导航顺序正确
- **WHEN** 管理员访问任意管理页面
- **THEN** 顶部导航 SHALL 显示上述 7 项，平台统计位于中间，申请管理位于倒数第二位

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

### Requirement: 申请管理页面
管理员后台 SHALL 提供"申请管理"页面（路由 `/admin/applications`），展示主管角色申请列表。页面 SHALL 包含：
- 顶部统计卡片：待审批数、已批准数、已拒绝数
- 申请列表表格：申请人用户名、邮箱、申请角色、申请理由（可为空显示"—"）、申请时间、状态徽章
- 每条 pending 申请 SHALL 有"通过"和"拒绝"操作按钮
- 点击"通过"时，SHALL 弹出"审批 + 分配部门"弹窗（而非直接调用接口），弹窗包含：
  - 申请人信息展示（只读）
  - 部门选择下拉框：从 `GET /admin/departments` 获取列表，前端过滤仅展示 `supervisor_username == null`（即无主管）的部门；若无可选部门则提示"当前无可分配的空余部门"
  - 审批备注输入框（可选）
  - 确认按钮调用 `POST /admin/role-applications/{id}/approve` 携带 `department_id`
- 点击"拒绝"时弹出备注输入框（现有行为保持不变）
- 支持按 status 筛选（全部/待审批/已批准/已拒绝）

#### Scenario: 查看待审批申请
- **WHEN** 管理员进入申请管理页
- **THEN** 页面 SHALL 默认展示所有 pending 状态的申请

#### Scenario: 点击通过按钮弹出分配弹窗
- **WHEN** 管理员点击某条 pending 申请的"通过"按钮
- **THEN** 页面 SHALL 弹出"审批 + 分配部门"弹窗，部门下拉框只展示当前无主管的部门

#### Scenario: 部门下拉无可用选项时的提示
- **WHEN** 管理员打开审批弹窗，但所有部门均已有主管
- **THEN** 部门下拉框 SHALL 显示禁用的提示项"当前无可分配的空余部门"，确认按钮 SHALL 为禁用状态

#### Scenario: 审批操作即时反馈
- **WHEN** 管理员在审批弹窗中选择部门并点击确认
- **THEN** 该行申请状态 SHALL 立即更新为"已批准"，操作按钮 SHALL 消失，弹窗 SHALL 关闭

### Requirement: API Key 管理迁移至系统设置
原"授权管理"页中的 API Key 审计列表 SHALL 迁移至"系统设置"页（`/admin/settings`），作为独立的区块展示，标题为"API 密钥管理"。

#### Scenario: 系统设置页展示 API Key
- **WHEN** 管理员访问系统设置页
- **THEN** 页面 SHALL 包含 API 密钥管理区块，功能与原授权管理页一致

