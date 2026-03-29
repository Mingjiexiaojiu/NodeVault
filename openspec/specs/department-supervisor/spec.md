## Requirements

### Requirement: 部门主管定义
系统 SHALL 将"部门主管"定义为同时满足以下两个条件的用户：
1. `User.role == 1`（平台级主管身份）
2. `DepartmentMember.role == "admin"`（在该部门内角色为管理员）

#### Scenario: 识别部门主管
- **WHEN** 系统需要判断某用户是否为某部门的主管
- **THEN** 系统 SHALL 查询 `department_members` 表，确认该用户 `role="admin"` 且 `users.role=1`，两者缺一则不认定为主管

---

### Requirement: 部门主管唯一性
每个部门 SHALL 最多拥有一个主管（即满足"部门主管定义"条件的成员）。

#### Scenario: 阻止重复分配主管
- **WHEN** 管理员尝试将第二个 `User.role==1` 的用户以 `role="admin"` 加入已有主管的部门
- **THEN** 系统 SHALL 返回 `409 Conflict`，`detail="该部门已有主管"`

#### Scenario: 无主管时可正常分配
- **WHEN** 管理员将 `User.role==1` 的用户以 `role="admin"` 加入当前没有主管的部门
- **THEN** 系统 SHALL 成功创建 `DepartmentMember` 记录

---

### Requirement: 管理员创建部门不自动加入成员
超级管理员通过 `POST /api/v1/admin/departments` 创建部门时，系统 SHALL 不自动将其添加为部门成员。新创建的部门初始成员列表为空。

#### Scenario: 管理员创建部门后成员列表为空
- **WHEN** 超级管理员成功调用 `POST /api/v1/admin/departments`
- **THEN** 系统 SHALL 创建部门记录，`department_members` 表中 SHALL 没有该部门对应的记录

---

### Requirement: 有成员的部门不可删除
系统 SHALL 在删除部门前检查成员数量，若部门仍有成员（`department_members` 记录数 > 0），则拒绝删除请求。

#### Scenario: 阻止删除有成员的部门
- **WHEN** 超级管理员尝试删除成员数 > 0 的部门
- **THEN** 系统 SHALL 返回 `400 Bad Request`，`detail="部门仍有成员，无法删除"`

#### Scenario: 允许删除空部门
- **WHEN** 超级管理员尝试删除成员数为 0 的部门
- **THEN** 系统 SHALL 成功删除该部门记录

---

### Requirement: 注册下拉框仅显示有主管的部门
`GET /api/v1/departments/public` SHALL 仅返回当前已有主管（满足"部门主管定义"）的部门列表，供用户注册时选择。

#### Scenario: 无主管部门不出现在注册下拉框
- **WHEN** 用户访问注册页面，前端调用 `GET /api/v1/departments/public`
- **THEN** 响应 SHALL 只包含已有主管的部门，没有主管的部门 SHALL 不出现在结果中

#### Scenario: 部门分配主管后立即可见
- **WHEN** 管理员成功将主管分配到某部门（使该部门从无主管变为有主管）
- **THEN** 后续调用 `GET /api/v1/departments/public` SHALL 包含该部门

---

### Requirement: `add_member` 端点主管校验
`POST /api/v1/departments/{dept_id}/members` 端点在接收 `role="admin"` 时，系统 SHALL 进行以下校验：
1. 目标用户的 `User.role` 必须为 `1`
2. 目标部门当前不存在主管

#### Scenario: 非主管用户尝试以 admin 角色加入
- **WHEN** 管理员尝试将 `User.role==2` 的普通用户以 `role="admin"` 加入部门
- **THEN** 系统 SHALL 返回 `400 Bad Request`，`detail="只有平台主管（role=1）才能担任部门管理员"`

#### Scenario: 部门已有主管时尝试以 admin 角色加入
- **WHEN** 管理员尝试将 `User.role==1` 的用户以 `role="admin"` 加入已有主管的部门
- **THEN** 系统 SHALL 返回 `409 Conflict`，`detail="该部门已有主管"`
