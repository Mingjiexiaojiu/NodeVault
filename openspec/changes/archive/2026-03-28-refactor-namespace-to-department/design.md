## Context

项目数据库使用 `namespaces` / `namespace_members` 表承载多租户/组织单元的职责，但业务代码已经全面使用"部门"语义。当前存在以下问题：

1. **命名不一致**：数据库表名与业务概念脱节，新开发者难以理解
2. **个人空间污染**：注册时为每个用户自动创建同名 namespace，混入"部门"列表，语义模糊
3. **冗余字段**：`users.department` 文本字段与 `namespace_members` 关联关系重叠，存在数据不一致风险
4. **API 字段混用**：`namespace_id` 出现在节点、技能、管理后台等多处 API 响应，与前端"部门"概念不对应

技术栈：PostgreSQL + SQLAlchemy 2.x + Alembic + FastAPI + Vue 3。

## Goals / Non-Goals

**Goals:**
- 将 `namespaces` 表重命名为 `departments`，`namespace_members` 重命名为 `department_members`
- 将 `namespace_id` 列在所有相关表（`nodes`、`skills`、`department_members`）中重命名为 `department_id`
- 删除 `users.department` 文本列
- 移除注册时自动创建个人 namespace 的逻辑
- ORM 模型、Pydantic Schema、API 响应字段、前端类型定义全面同步更新
- 通过单个 Alembic 迁移脚本完成所有数据库结构变更，数据无损

**Non-Goals:**
- 不新增业务功能
- 不修改部门的 CRUD 业务逻辑（仅同步引用名称）
- 不修改 SDK 的深层业务逻辑，只同步字段名
- 不处理已有个人 namespace 数据的清洗（数据迁移仅做结构重命名）

## Decisions

### 决策 1：使用单个 Alembic 迁移脚本完成所有结构变更

**选择**：一个 phase14 迁移脚本完成全部 DDL：表重命名、列重命名、约束/索引重命名、删列。

**理由**：所有变更是原子的重构，不涉及数据转换逻辑，拆分成多个迁移会增加中间状态下的一致性风险。PostgreSQL 的 `ALTER TABLE RENAME` 系列操作均为快速元数据操作，不锁数据。

**备选方案**：分阶段迁移（先加列，迁移数据，再删旧列）→ 不需要，本次只是重命名，无数据迁移需求。

---

### 决策 2：`users.department` 文本字段直接删除，不做迁移保留

**选择**：直接 `DROP COLUMN users.department`，对应的 `UserResponse.department` 和 `ProfileUpdate.department` 字段一并删除。

**理由**：用户所属部门的权威数据来源是 `department_members` 关联表。保留文本字段会形成两个数据来源，导致不一致。项目尚未正式上线，不存在需要保护的历史数据。

**备选方案**：保留为"职位描述"字段，改名为 `job_department` → 增加维护成本，且意义重叠，放弃。

---

### 决策 3：注册时不再创建默认 Department

**选择**：`POST /api/v1/auth/register` 仅创建 `User` 记录，移除自动创建 `Namespace`/`NamespaceMember` 的代码。

**理由**：部门是组织结构概念，应由主管/管理员按需分配，而非由系统自动生成。注册即拥有个人部门的模式与企业内部系统语义不符。

**影响**：新注册用户的 `UserResponse.departments` 默认为空数组 `[]`，前端需能处理此情况（现有代码已能兼容）。

---

### 决策 4：模型文件随类名一起重命名

**选择**：`backend/models/namespace.py` → `backend/models/department.py`，所有 import 路径同步更新。

**理由**：文件名与核心类名保持一致是 Python 项目的常规约定，避免 `from models.namespace import Department` 这类令人困惑的路径。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Alembic 自动生成检测不到 RENAME（误判为 DROP+CREATE） | 手写迁移脚本，不使用 `--autogenerate`；使用 `op.rename_table` 和 `op.alter_column` |
| FK 约束名称在 PostgreSQL 中需显式重命名 | 迁移脚本中用 `op.execute("ALTER TABLE ... RENAME CONSTRAINT ...")` 逐一处理 |
| 前端遗漏某处 `namespace_id` 引用导致运行时报错 | 全量 grep `namespace_id` 和 `namespaces` 确认无遗漏后再提交 |
| 现有数据库中存在个人 namespace 记录（slug = username） | 迁移只做结构重命名，已有数据保留为普通部门记录，不删除 |
| SDK 客户端外部用户若已使用旧字段名会破坏兼容 | 这是预期的 breaking change，在 proposal 已标注；在 SDK changelog 中说明 |

## Migration Plan

1. 在 `backend/database/migrations/versions/` 中新建 `phase14_rename_namespace_to_department.py`
2. 迁移脚本执行顺序：
   ```
   a. DROP CONSTRAINT (FK constraints referencing namespaces)
   b. RENAME TABLE namespaces → departments
   c. RENAME TABLE namespace_members → department_members
   d. RENAME COLUMN department_members.namespace_id → department_id
   e. RENAME COLUMN nodes.namespace_id → department_id
   f. RENAME COLUMN skills.namespace_id → department_id (如有)
   g. DROP COLUMN users.department
   h. RENAME INDEX / CONSTRAINT names (uq_namespace_member → uq_department_member 等)
   i. RE-ADD FK constraints with new names
   ```
3. 先更新 ORM 模型和 Schema（让 Python 代码与新表结构对齐）
4. 全局替换所有代码引用
5. 运行 `alembic upgrade head` 应用迁移
6. 回滚策略：`alembic downgrade -1` 执行 `down_revision` 中的逆操作（RENAME 均可逆）

## Open Questions

- （无）本次变更范围已在 explore 阶段完全厘清，无未决技术问题。
