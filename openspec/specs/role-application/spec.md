## Requirements

### Requirement: RoleApplication ORM 模型
系统 SHALL 定义 `RoleApplication` SQLAlchemy ORM 模型，包含字段：`id`（UUID 主键，默认 gen_random_uuid()）、`user_id`（外键 users.id，NOT NULL）、`requested_role`（Integer，NOT NULL，目前仅支持 1=主管）、`status`（VARCHAR(16)，默认 `'pending'`，枚举：pending/approved/rejected）、`reason`（Text，可为空，申请人说明）、`review_note`（Text，可为空，审批备注）、`reviewed_by`（外键 users.id，可为空）、`created_at`（timestamp，默认 now()）、`reviewed_at`（timestamp，可为空）。

#### Scenario: 申请记录创建
- **WHEN** 用户注册时选择"申请成为主管"
- **THEN** 系统 SHALL 在 `role_applications` 表中创建一条 status=pending 的记录，user_id 指向新用户

#### Scenario: 审批通过
- **WHEN** 管理员对某条 pending 申请执行审批通过操作
- **THEN** 系统 SHALL 将 `role_applications.status` 更新为 `approved`，同时将 `users.role` 更新为 1，记录 `reviewed_by` 和 `reviewed_at`

#### Scenario: 审批拒绝
- **WHEN** 管理员对某条 pending 申请执行拒绝操作，可填写拒绝备注
- **THEN** 系统 SHALL 将 `role_applications.status` 更新为 `rejected`，`users.role` 保持不变，记录 `review_note`

---

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

#### Scenario: 重复申请检查
- **WHEN** 已有 pending 申请的用户再次调用注册接口
- **THEN** 此场景不适用（注册只触发一次）；若后续支持在职申请，系统 SHALL 拒绝重复 pending 申请

---

### Requirement: /me 接口返回申请状态
系统 SHALL 在 `GET /api/v1/auth/me` 的响应中包含 `pending_role_application` 字段（可为空），当用户存在 status=pending 的 `role_applications` 记录时返回该申请的 `requested_role` 和 `created_at`。

#### Scenario: 存在待审批申请
- **WHEN** 已提交主管申请的用户调用 `/me` 接口
- **THEN** 响应 SHALL 包含 `pending_role_application: { requested_role: 1, created_at: "..." }`

#### Scenario: 无待审批申请
- **WHEN** 普通用户调用 `/me` 接口
- **THEN** 响应中 `pending_role_application` SHALL 为 null
