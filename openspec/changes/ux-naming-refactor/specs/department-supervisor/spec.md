## MODIFIED Requirements

### Requirement: 部门主管定义
系统 SHALL 将"部门主管"定义为同时满足以下两个条件的用户：
1. `User.role == 1`（平台级主管身份）
2. `DepartmentMember.role == "admin"`（在该团队内角色为主管）

#### Scenario: 识别部门主管
- **WHEN** 系统需要判断某用户是否为某团队的主管
- **THEN** 系统 SHALL 查询 `department_members` 表，确认该用户 `role="admin"` 且 `users.role=1`，两者缺一则不认定为主管

### Requirement: `add_member` 端点主管校验
`POST /api/v1/departments/{dept_id}/members` 端点在接收 `role="admin"` 时，系统 SHALL 进行以下校验：
1. 目标用户的 `User.role` 必须为 `1`
2. 目标团队当前不存在主管

#### Scenario: 非主管用户尝试以 admin 角色加入
- **WHEN** 管理员尝试将 `User.role==2` 的普通用户以 `role="admin"` 加入团队
- **THEN** 系统 SHALL 返回 `400 Bad Request`，`detail="只有平台主管（role=1）才能担任团队主管"`

#### Scenario: 团队已有主管时尝试以 admin 角色加入
- **WHEN** 管理员尝试将 `User.role==1` 的用户以 `role="admin"` 加入已有主管的团队
- **THEN** 系统 SHALL 返回 `409 Conflict`，`detail="该团队已有主管"`

### Requirement: 注册下拉框仅显示有主管的部门
`GET /api/v1/departments/public` SHALL 仅返回当前已有主管（满足"部门主管定义"）的团队列表，供用户注册时选择。响应 SHALL 包含所属组织名称（organization.name）和团队名称（team_name）。

#### Scenario: 无主管部门不出现在注册下拉框
- **WHEN** 用户访问注册页面，前端调用 `GET /api/v1/departments/public`
- **THEN** 响应 SHALL 只包含已有主管的团队，没有主管的团队 SHALL 不出现在结果中

#### Scenario: 返回组织和团队信息
- **WHEN** 前端调用 `GET /api/v1/departments/public`
- **THEN** 每条记录 SHALL 包含 id、organization_name、team_name、admin_username 字段

## ADDED Requirements

### Requirement: Department 关联 Organization
Department 表 SHALL 新增 `org_id` UUID 外键指向 `organizations.id`（NOT NULL）。原 `slug` 字段 SHALL 删除。原 `display_name` 字段 SHALL 重命名为 `team_name`。唯一约束 SHALL 改为 `UNIQUE(org_id, team_name)`。

#### Scenario: 创建团队关联组织
- **WHEN** 创建新团队时提供 org_id 和 team_name
- **THEN** 系统 SHALL 创建 Department 记录，org_id 指向对应 Organization

#### Scenario: 同一组织下团队名唯一
- **WHEN** 在同一 Organization 下尝试创建同名团队
- **THEN** 系统 SHALL 返回 409 Conflict

#### Scenario: 不同组织可同名团队
- **WHEN** 在不同 Organization 下分别创建同名团队
- **THEN** 系统 SHALL 均成功创建

### Requirement: 创建团队 API 改造
`POST /api/v1/departments` 端点 SHALL 接受 `org_name`（组织名称）和 `team_name`（团队名称）替代原来的 `slug` 和 `display_name`。如果 org_name 对应的 Organization 不存在，系统 SHALL 自动创建。

#### Scenario: 创建团队（已有组织）
- **WHEN** 用户提交 org_name 为已存在的组织名、team_name 为新名称
- **THEN** 系统 SHALL 创建团队关联到已有组织

#### Scenario: 创建团队（新组织）
- **WHEN** 用户提交 org_name 为不存在的组织名、team_name
- **THEN** 系统 SHALL 先创建 Organization，再创建团队关联

### Requirement: 团队详情返回组织信息
`GET /api/v1/departments/{dept_id}` 端点 SHALL 在响应中包含 organization_name 字段（来自关联的 Organization.name），不再返回 slug 字段。

#### Scenario: 获取团队详情
- **WHEN** 用户请求团队详情
- **THEN** 响应 SHALL 包含 id、organization_name、team_name、description、owner_id、members 列表

### Requirement: 前端角色标签变更
前端展示 SHALL 将 DepartmentMember.role="admin" 显示为"主管"（非"管理员"），将 owner_id 对应用户显示为"拥有者"。

#### Scenario: 团队成员列表展示角色
- **WHEN** 前端渲染团队成员列表
- **THEN** role=admin 的成员 SHALL 显示"主管"标签，非 admin 成员显示"成员"标签

#### Scenario: 团队详情展示拥有者
- **WHEN** 前端渲染团队详情页
- **THEN** owner_id 对应用户 SHALL 显示"拥有者"标签
