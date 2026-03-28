## MODIFIED Requirements

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

### Requirement: Alembic 初始迁移覆盖所有表
系统 SHALL 包含 phase14 Alembic 迁移脚本，完成以下结构变更：将 `namespaces` 表重命名为 `departments`；将 `namespace_members` 表重命名为 `department_members`；将 `department_members.namespace_id` 列重命名为 `department_id`；将 `nodes.namespace_id` 列重命名为 `department_id`；将 `skills.namespace_id` 列重命名为 `department_id`；删除 `users.department` 列；更新所有相关 FK 约束名和索引名。迁移 SHALL 可逆（downgrade 可还原）。

#### Scenario: 执行 phase14 迁移后结构正确
- **WHEN** 在已有数据的数据库上执行 `alembic upgrade head`
- **THEN** 数据库 SHALL 包含 `departments`/`department_members` 表，`nodes.department_id` FK 正确指向 `departments.id`，`users` 表 SHALL NOT 含 `department` 列，现有数据无损

#### Scenario: 迁移可回滚
- **WHEN** 执行 `alembic downgrade -1`
- **THEN** 表名/列名 SHALL 恢复为 `namespaces`/`namespace_members`/`namespace_id`，`users.department` 列 SHALL 被还原
