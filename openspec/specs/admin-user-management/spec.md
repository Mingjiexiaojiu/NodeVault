## Purpose
为超级管理员提供用户管理后台能力，包括查看、禁用/解禁、角色变更以及主管申请审批等操作。
## Requirements
### Requirement: List all users
系统 SHALL 提供 `GET /api/v1/admin/users` 端点，返回平台所有用户的分页列表，支持按 username/email 关键词过滤，支持按 role/is_active 过滤。

#### Scenario: Superadmin lists all users
- **WHEN** 超管请求 `GET /admin/users`
- **THEN** 系统返回所有用户的分页列表，每条记录包含 id/email/username/role/is_active/created_at/display_name

#### Scenario: Filter by keyword
- **WHEN** 超管请求 `GET /admin/users?q=alice`
- **THEN** 系统返回 email 或 username 中包含 "alice" 的用户列表

#### Scenario: Filter by status
- **WHEN** 超管请求 `GET /admin/users?is_active=false`
- **THEN** 系统只返回已被封禁的用户

---

### Requirement: Get user detail
系统 SHALL 提供 `GET /api/v1/admin/users/{user_id}` 端点，返回指定用户详情及其拥有的 **department** 数量（`department_count`）、node 数量、skill 数量。响应中 SHALL NOT 包含 `namespace_count` 字段。

#### Scenario: Get existing user detail
- **WHEN** 超管请求 `GET /admin/users/{valid_id}`
- **THEN** 系统返回用户完整信息及资源摘要统计，统计字段包含 `department_count`/`node_count`/`skill_count`

#### Scenario: Get non-existent user
- **WHEN** 超管请求一个不存在的 user_id
- **THEN** 系统返回 HTTP 404

### Requirement: Ban or unban user
系统 SHALL 提供 `PATCH /api/v1/admin/users/{user_id}/status` 端点，允许超管设置用户的 `is_active` 状态。

#### Scenario: Ban an active user
- **WHEN** 超管 PATCH `{"is_active": false}` 到某普通用户
- **THEN** 系统将该用户 is_active 设为 false，该用户后续登录/API请求返回 401

#### Scenario: Cannot ban the only superadmin
- **WHEN** 超管尝试封禁自身且系统中只有一个 role=0 用户
- **THEN** 系统返回 HTTP 400，提示 "Cannot disable the only superadmin"

---

### Requirement: Change user role
系统 SHALL 提供 `PATCH /api/v1/admin/users/{user_id}/role` 端点，允许超管修改用户角色（0/1/2）。

#### Scenario: Promote user to manager
- **WHEN** 超管 PATCH `{"role": 1}` 到某普通用户
- **THEN** 系统将该用户 role 更新为 1

#### Scenario: Cannot demote the only superadmin
- **WHEN** 超管尝试将自身 role 改为非 0 且系统中只有一个 role=0 用户
- **THEN** 系统返回 HTTP 400，提示 "Cannot demote the only superadmin"

---

### Requirement: Delete user
系统 SHALL 提供 `DELETE /api/v1/admin/users/{user_id}` 端点，级联删除用户及其所有资源（通过 DB 外键级联）。

#### Scenario: Delete ordinary user
- **WHEN** 超管 DELETE 某普通用户
- **THEN** 系统删除该用户及其关联的 namespace/nodes/skills/credentials

#### Scenario: Cannot delete the only superadmin
- **WHEN** 超管尝试删除自身且系统中只有一个 role=0 用户
- **THEN** 系统返回 HTTP 400，提示 "Cannot delete the only superadmin"

### Requirement: 节点和技能管理后台列表字段
系统 SHALL 在 `GET /api/v1/admin/nodes` 和 `GET /api/v1/admin/skills` 响应的每条记录中使用 `department_id` 和 `department_slug` 字段（替代 `namespace_id` 和 `namespace_slug`）标识所属部门。

#### Scenario: 管理后台列出节点
- **WHEN** 超管请求 `GET /api/v1/admin/nodes`
- **THEN** 每条节点记录 SHALL 包含 `department_id`（UUID）和 `department_slug`（string）字段，SHALL NOT 包含 `namespace_id` 或 `namespace_slug` 字段

#### Scenario: 管理后台列出技能
- **WHEN** 超管请求 `GET /api/v1/admin/skills`
- **THEN** 每条技能记录 SHALL 包含 `department_id` 和 `department_slug` 字段，SHALL NOT 包含 `namespace_id` 或 `namespace_slug` 字段

### Requirement: 管理员审批主管申请
系统 SHALL 提供主管申请的审批接口（见 role-application spec），管理员通过"申请管理"页可查看所有 pending 申请并执行审批/拒绝操作。审批通过后，系统 SHALL 原子性地更新 `role_applications.status='approved'` 和 `users.role=1`。

#### Scenario: 审批通过后用户角色变更
- **WHEN** 管理员审批通过某用户的主管申请
- **THEN** 该用户 `role` SHALL 变为 1，再次调用 `/me` 时 `pending_role_application` SHALL 为 null

#### Scenario: 拒绝申请
- **WHEN** 管理员拒绝某用户的主管申请并填写备注
- **THEN** `role_applications.status` SHALL 变为 `rejected`，用户 `role` SHALL 不变，`review_note` SHALL 被保存

