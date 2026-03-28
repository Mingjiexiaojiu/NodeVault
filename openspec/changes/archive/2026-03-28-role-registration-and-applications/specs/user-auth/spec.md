## MODIFIED Requirements

### Requirement: 用户注册
系统 SHALL 提供 `POST /api/v1/auth/register` 端点，接受 `email`、`password`、`username`、`display_name` 字段，以及可选的 `requested_role`（int，1=申请主管，默认 2=普通用户）和 `department_id`（UUID，普通用户选择加入的部门）。密码 SHALL 使用 bcrypt 哈希存储，明文密码 SHALL NOT 写入数据库。注册后 SHALL NOT 自动创建任何 Department 或 DepartmentMember 记录（除非用户选择了 `department_id`）。

#### Scenario: 注册成功（普通用户，无部门选择）
- **WHEN** 提供有效的基本信息，`requested_role` 为 2 或未提供，未提供 `department_id`
- **THEN** 系统 SHALL 创建 User 记录（role=2），返回 201 和用户信息

#### Scenario: 注册成功（普通用户，选择部门）
- **WHEN** 提供有效基本信息，`requested_role` 为 2，提供有效的 `department_id`
- **THEN** 系统 SHALL 创建 User 记录（role=2）和 `DepartmentMember`（status='pending', role='member'），返回 201

#### Scenario: 注册成功（申请主管）
- **WHEN** 提供有效基本信息，`requested_role` 为 1
- **THEN** 系统 SHALL 创建 User 记录（role=2），同时创建 `RoleApplication`（status='pending', requested_role=1），返回 201，响应体包含 `pending_role_application` 信息

#### Scenario: 邮箱已存在
- **WHEN** 使用已注册的 email 发起注册请求
- **THEN** 系统 SHALL 返回 409，提示邮箱已被使用

#### Scenario: 密码强度不足
- **WHEN** 提供长度不足 8 位或不含数字的密码
- **THEN** 系统 SHALL 返回 422 并说明密码规则
