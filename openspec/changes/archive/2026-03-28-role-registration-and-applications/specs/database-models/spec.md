## ADDED Requirements

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
