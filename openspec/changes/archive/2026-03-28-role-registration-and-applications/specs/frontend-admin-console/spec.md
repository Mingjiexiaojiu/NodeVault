## MODIFIED Requirements

### Requirement: Admin layout and route guard
管理员导航栏 SHALL 包含 7 个 Tab 项，顺序为：`用户管理 | 全局节点 | 分类管理 | 平台统计 | 部门管理 | 申请管理 | 系统设置`。"平台统计"SHALL 位于第 4 个位置（正中间），"申请管理"SHALL 替换原"授权管理"。

#### Scenario: 导航顺序正确
- **WHEN** 管理员访问任意管理页面
- **THEN** 顶部导航 SHALL 显示上述 7 项，平台统计位于中间，申请管理位于倒数第二位

## ADDED Requirements

### Requirement: 申请管理页面
管理员后台 SHALL 提供"申请管理"页面（路由 `/admin/applications`），展示主管角色申请列表。页面 SHALL 包含：
- 顶部统计卡片：待审批数、已批准数、已拒绝数
- 申请列表表格：申请人用户名、邮箱、申请角色、申请理由（可为空显示"—"）、申请时间、状态徽章
- 每条 pending 申请 SHALL 有"通过"和"拒绝"操作按钮，点击拒绝时弹出备注输入框
- 支持按 status 筛选（全部/待审批/已批准/已拒绝）

#### Scenario: 查看待审批申请
- **WHEN** 管理员进入申请管理页
- **THEN** 页面 SHALL 默认展示所有 pending 状态的申请

#### Scenario: 审批操作即时反馈
- **WHEN** 管理员点击"通过"按钮
- **THEN** 该行申请状态 SHALL 立即更新为"已批准"，操作按钮 SHALL 消失

### Requirement: API Key 管理迁移至系统设置
原"授权管理"页中的 API Key 审计列表 SHALL 迁移至"系统设置"页（`/admin/settings`），作为独立的区块展示，标题为"API 密钥管理"。

#### Scenario: 系统设置页展示 API Key
- **WHEN** 管理员访问系统设置页
- **THEN** 页面 SHALL 包含 API 密钥管理区块，功能与原授权管理页一致
