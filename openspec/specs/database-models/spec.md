## ADDED Requirements

### Requirement: User ORM 模型
系统 SHALL 定义 `User` SQLAlchemy ORM 模型，包含字段：`id`（UUID 主键）、`email`（唯一索引）、`username`（唯一索引）、`hashed_password`（字符串）、`is_active`（布尔，默认 True）、`created_at`、`updated_at`。

#### Scenario: User 模型定义完整
- **WHEN** 运行 `alembic revision --autogenerate`
- **THEN** 生成的迁移脚本 SHALL 包含 `users` 表的完整字段定义，含 email/username 唯一索引

---

### Requirement: Namespace ORM 模型
系统 SHALL 定义 `Namespace` SQLAlchemy ORM 模型，包含字段：`id`（UUID 主键）、`slug`（唯一索引，kebab-case，如 `alice`）、`owner_id`（外键 users.id）、`display_name`、`created_at`。

#### Scenario: Namespace 与 User 关联
- **WHEN** 创建一个 User 记录并自动创建默认 Namespace
- **THEN** Namespace.owner_id SHALL 指向该 User.id，Namespace.slug SHALL 等于 User.username

---

### Requirement: Node/NodeVersion/NodeTag ORM 模型
系统 SHALL 定义以下 ORM 模型：
- `Node`：id/name/namespace_id/owner_id/display_name/description/type/category/status/visibility/created_at/updated_at，(name, namespace_id) 联合唯一约束
- `NodeVersion`：id/node_id/version/input_schema(JSONB)/output_schema(JSONB)/runtime_config(JSONB)/changelog/is_default/is_deprecated/created_at/created_by，(node_id, version) 联合唯一约束
- `NodeTag`：id/node_id/tag，(node_id, tag) 联合唯一约束

#### Scenario: Node 联合唯一约束生效
- **WHEN** 尝试在同一 Namespace 下插入两个同名 Node
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
系统 SHALL 生成并可执行包含所有 Phase 1 ORM 模型的 Alembic 初始迁移脚本。`migrations/env.py` SHALL import 所有模型模块以确保 `autogenerate` 能发现全部表定义。

#### Scenario: 一键迁移建表
- **WHEN** 在空数据库上执行 `alembic upgrade head`
- **THEN** 数据库 SHALL 包含 users/namespaces/nodes/node_versions/node_tags/node_invocation_logs 共 6 张表，含所有索引和约束

#### Scenario: 迁移可回滚
- **WHEN** 执行 `alembic downgrade -1`
- **THEN** 刚刚创建的所有表 SHALL 被删除，数据库恢复到迁移前状态
