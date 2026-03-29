## MODIFIED Requirements

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
