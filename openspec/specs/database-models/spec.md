## Purpose
定义 NodeVault 平台的核心数据库 ORM 模型及 Alembic 迁移策略。
## Requirements
### Requirement: User ORM 模型
系统 SHALL 定义 `User` SQLAlchemy ORM 模型，包含字段：`id`（UUID 主键）、`email`（唯一索引）、`username`（唯一索引）、`hashed_password`（字符串）、`is_active`（布尔，默认 True）、`created_at`、`updated_at`。

#### Scenario: User 模型定义完整
- **WHEN** 运行 `alembic revision --autogenerate`
- **THEN** 生成的迁移脚本 SHALL 包含 `users` 表的完整字段定义，含 email/username 唯一索引

---

### Requirement: Namespace ORM 模型
系统 SHALL 定义 `Department` SQLAlchemy ORM 模型（文件 `backend/models/department.py`），包含字段：`id`（UUID 主键）、`slug`（唯一索引）、`owner_id`（外键 users.id，CASCADE 删除）、`display_name`（String 256，可为空）、`description`（Text，可为空）、`created_at`。对应数据库表名为 `departments`。同时定义 `DepartmentMember` 模型，表名 `department_members`，字段：`id`、`department_id`（外键 departments.id，CASCADE 删除）、`user_id`（外键 users.id，CASCADE 删除）、`role`（string: admin/member，默认 member）、`joined_at`；含 `(department_id, user_id)` 联合唯一约束。

#### Scenario: Department 与 User 关联
- **WHEN** 通过 `POST /api/v1/departments` 创建一个 Department 记录
- **THEN** Department.owner_id SHALL 指向创建者的 User.id，创建者被自动加入 department_members 且 role=admin

#### Scenario: DepartmentMember 唯一约束生效
- **WHEN** 尝试向同一 department 重复添加同一 user
- **THEN** 数据库 SHALL 抛出唯一约束违反错误（HTTP 409）

---

### Requirement: Node/NodeVersion/NodeTag ORM 模型
系统 SHALL 定义以下 ORM 模型：
- `Node`：id/name/**department_id**/owner_id/display_name/description/type/category/status/visibility/created_at/updated_at，`(name, department_id)` 联合唯一约束（约束名 `uq_node_name_department`）
- `NodeVersion`：id/node_id/version/input_schema(JSONB)/output_schema(JSONB)/runtime_config(JSONB)/changelog/is_default/is_deprecated/created_at/created_by，(node_id, version) 联合唯一约束
- `NodeTag`：id/node_id/tag，(node_id, tag) 联合唯一约束

#### Scenario: Node 联合唯一约束生效
- **WHEN** 尝试在同一 Department 下插入两个同名 Node
- **THEN** 数据库 SHALL 抛出唯一约束违反错误

#### Scenario: NodeVersion 版本号唯一约束生效
- **WHEN** 尝试为同一 Node 插入两个版本号相同的 NodeVersion
- **THEN** 数据库 SHALL 抛出唯一约束违反错误

---

### Requirement: NodeInvocationLog ORM 模型
系统 SHALL 定义 `NodeInvocationLog` ORM 模型，包含字段：`id`（UUID 主键）、`node_id`（外键）、`version`、`invoked_by`（外键 users.id，可为空）、`input_data`（JSONB）、`output_data`（JSONB）、`status`（string: success/failure/timeout）、`latency_ms`（整数）、`error_message`（Text，可为空）、`created_at`（有索引）。

#### Scenario: 日志记录创建
- **WHEN** 向 node_invocation_logs 插入一条 status=failure 的记录
- **THEN** 记录 SHALL 被成功写入，error_message 字段保存错误文本

---

### Requirement: Alembic 初始迁移覆盖所有表
系统 SHALL 包含 phase14 Alembic 迁移脚本，完成以下结构变更：将 `namespaces` 表重命名为 `departments`；将 `namespace_members` 表重命名为 `department_members`；将 `department_members.namespace_id` 列重命名为 `department_id`；将 `nodes.namespace_id` 列重命名为 `department_id`；将 `skills.namespace_id` 列重命名为 `department_id`；删除 `users.department` 列；更新所有相关 FK 约束名和索引名。迁移 SHALL 可逆（downgrade 可还原）。

#### Scenario: 执行 phase14 迁移后结构正确
- **WHEN** 在已有数据的数据库上执行 `alembic upgrade head`
- **THEN** 数据库 SHALL 包含 `departments`/`department_members` 表，`nodes.department_id` FK 正确指向 `departments.id`，`users` 表 SHALL NOT 含 `department` 列，现有数据无损

#### Scenario: 迁移可回滚
- **WHEN** 执行 `alembic downgrade -1`
- **THEN** 表名/列名 SHALL 恢复为 `namespaces`/`namespace_members`/`namespace_id`，`users.department` 列 SHALL 被还原

### Requirement: RoleApplication 数据模型
系统 SHALL 定义 `RoleApplication` ORM 模型，`__tablename__ = "role_applications"`，字段如下：`id`（UUID PK）、`user_id`（UUID FK→users.id，NOT NULL，ondelete=CASCADE）、`requested_role`（Integer，NOT NULL）、`status`（VARCHAR(16)，NOT NULL，默认 'pending'）、`reason`（Text，可空）、`review_note`（Text，可空）、`reviewed_by`（UUID FK→users.id，可空）、`created_at`（DateTime，NOT NULL，默认 now()）、`reviewed_at`（DateTime，可空）。索引：`user_id`、`status`。

#### Scenario: 迁移脚本创建 role_applications 表
- **WHEN** 执行新增的 Alembic 迁移脚本（upgrade）
- **THEN** 数据库 SHALL 新增 `role_applications` 表，含所有字段、外键约束和索引

#### Scenario: 迁移可回滚
- **WHEN** 执行 `alembic downgrade -1`
- **THEN** `role_applications` 表 SHALL 被删除，`department_members.status` 字段 SHALL 被移除，数据库恢复至迁移前状态

---

### Requirement: department_members 表新增 status 字段
系统 SHALL 为 `department_members` 表新增 `status` 字段（VARCHAR(16)，NOT NULL，默认 `'active'`，枚举：active/pending/rejected）。现有数据 SHALL 自动填充默认值 `'active'` 保证向后兼容。所有查询正式成员的逻辑 SHALL 过滤 `status='active'`。

#### Scenario: 现有成员不受影响
- **WHEN** 执行新增 status 字段的 Alembic 迁移
- **THEN** 所有现有 `department_members` 记录 `status` SHALL 被设置为 `'active'`

#### Scenario: 新申请加入的成员状态为 pending
- **WHEN** 普通用户注册时选择部门，系统创建 DepartmentMember 记录
- **THEN** 该记录 `status` SHALL 为 `'pending'`，不出现在部门正式成员列表中

