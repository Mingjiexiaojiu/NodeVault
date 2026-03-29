## MODIFIED Requirements

### Requirement: 申请管理 API
系统 SHALL 提供以下端点（需要 role=0 超级管理员权限）：
- `GET /api/v1/admin/role-applications`：分页列表，支持按 status 过滤，返回申请人用户名/邮箱等信息
- `POST /api/v1/admin/role-applications/{id}/approve`：审批通过，必须携带 `department_id`（目标部门 UUID），可选 `review_note`。审批操作 SHALL 在同一数据库事务中原子完成以下步骤：① 将 `role_applications.status` 更新为 `approved`；② 将 `users.role` 更新为 `app.requested_role`；③ 创建 `DepartmentMember(department_id, user_id, role="admin")`
- `POST /api/v1/admin/role-applications/{id}/reject`：拒绝申请，可选 `review_note`

#### Scenario: 列表查询
- **WHEN** 管理员调用 `GET /api/v1/admin/role-applications?status=pending`
- **THEN** 系统 SHALL 返回所有 pending 状态的申请，包含申请人 username、email、created_at

#### Scenario: 审批通过并分配部门
- **WHEN** 管理员调用 `POST /admin/role-applications/{id}/approve`，携带有效的 `department_id`
- **THEN** 系统 SHALL 在同一事务中：将申请状态置为 approved、将用户角色升级为 1、将用户以 `role="admin"` 加入指定部门

#### Scenario: 审批通过但目标部门已有主管
- **WHEN** 管理员调用 approve 接口，指定的 `department_id` 对应的部门已存在主管
- **THEN** 系统 SHALL 返回 `409 Conflict`，`detail="该部门已有主管，请选择其他部门"`，不执行任何状态变更

#### Scenario: 审批通过但未提供 department_id
- **WHEN** 管理员调用 approve 接口但未携带 `department_id`
- **THEN** 系统 SHALL 返回 `422 Unprocessable Entity`

#### Scenario: 审批拒绝
- **WHEN** 管理员对某条 pending 申请执行拒绝操作，可填写拒绝备注
- **THEN** 系统 SHALL 将 `role_applications.status` 更新为 `rejected`，`users.role` 保持不变，记录 `review_note`

#### Scenario: 重复申请检查
- **WHEN** 已有 pending 申请的用户再次调用注册接口
- **THEN** 此场景不适用（注册只触发一次）；若后续支持在职申请，系统 SHALL 拒绝重复 pending 申请
