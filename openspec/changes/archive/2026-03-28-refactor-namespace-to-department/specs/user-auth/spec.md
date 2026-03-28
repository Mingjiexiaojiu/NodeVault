## MODIFIED Requirements

### Requirement: 用户注册
系统 SHALL 提供 `POST /api/v1/auth/register` 端点，接受 `email`、`username`、`display_name` 和 `password` 字段。密码 SHALL 使用 bcrypt 哈希存储，明文密码 SHALL NOT 写入数据库。注册成功后 SHALL 仅创建 User 记录，SHALL NOT 自动创建任何 Department 或 DepartmentMember 记录。

#### Scenario: 注册成功
- **WHEN** 提供有效的 email 和符合强度要求的 password（≥8位，含大小写和数字）
- **THEN** 系统 SHALL 仅创建 User 记录，返回 201 和用户信息（不含密码），`departments` 字段为空数组 `[]`

#### Scenario: 邮箱已存在
- **WHEN** 使用已注册的 email 发起注册请求
- **THEN** 系统 SHALL 返回 409，提示邮箱已被使用

#### Scenario: 密码强度不足
- **WHEN** 提供长度不足 8 位或不含数字的密码
- **THEN** 系统 SHALL 返回 422 并说明密码规则


## ADDED Requirements

### Requirement: 用户信息响应（UserResponse）
系统 SHALL 在 `GET /api/v1/auth/me` 响应及注册成功响应中返回 `UserResponse` 结构，包含字段：`id`、`email`、`username`、`is_active`、`role`、`role_label`、`display_name`、`avatar_url`、`bio`、`phone`、`title`、`departments`（`UserDepartmentBrief` 数组）、`created_at`。响应中 SHALL NOT 包含 `department` 文本字段和 `namespaces` 字段。

#### Scenario: 获取当前用户信息
- **WHEN** 已认证用户调用 `GET /api/v1/auth/me`
- **THEN** 系统 SHALL 返回包含 `departments` 数组的用户信息，每项含 `id`/`slug`/`display_name`/`role`

#### Scenario: 新注册用户无部门
- **WHEN** 新用户注册后立即调用 `GET /api/v1/auth/me`
- **THEN** `departments` SHALL 为空数组 `[]`
