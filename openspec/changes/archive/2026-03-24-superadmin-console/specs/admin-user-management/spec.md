## ADDED Requirements

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
系统 SHALL 提供 `GET /api/v1/admin/users/{user_id}` 端点，返回指定用户详情及其拥有的 namespace 数量、node 数量、skill 数量。

#### Scenario: Get existing user detail
- **WHEN** 超管请求 `GET /admin/users/{valid_id}`
- **THEN** 系统返回用户完整信息及资源摘要统计

#### Scenario: Get non-existent user
- **WHEN** 超管请求一个不存在的 user_id
- **THEN** 系统返回 HTTP 404

---

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
