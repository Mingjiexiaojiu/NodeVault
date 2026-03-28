## Why

数据库层使用 `namespaces` / `namespace_members` 表，而业务代码和前端已全面使用"部门"概念（`/departments` 路由、中文注释），造成名实不符。同时，注册时自动为每位用户创建个人 namespace 的逻辑与"部门"语义不符，需要一并清除。趁项目尚未上线，整体对齐命名。

## What Changes

- **BREAKING** 数据库表 `namespaces` 重命名为 `departments`
- **BREAKING** 数据库表 `namespace_members` 重命名为 `department_members`
- **BREAKING** 相关列名 `namespace_id` → `department_id`（影响 `department_members`、`nodes`、`skills` 表）
- **BREAKING** 删除 `users.department` 文本字段（部门归属改由 `department_members` 关联关系承载）
- **BREAKING** 注册流程中删除自动创建个人 namespace 的逻辑，用户注册后默认不属于任何部门
- ORM 模型 `Namespace` → `Department`，`NamespaceMember` → `DepartmentMember`
- 模型文件 `models/namespace.py` → `models/department.py`
- Pydantic Schema：`UserNamespaceBrief` → `UserDepartmentBrief`，`UserResponse.namespaces` → `UserResponse.departments`，删除 `ProfileUpdate.department` 字段
- 后端所有引用（API 路由、Core、Schemas）同步更新
- 前端 API 类型定义同步更新（`namespace_id` → `department_id`，`namespaces` → `departments`）
- 新增 Alembic 迁移脚本（phase14）完成数据库结构变更

## Capabilities

### New Capabilities

（无新增能力，本次为纯重构）

### Modified Capabilities

- `database-models`：`Namespace`/`NamespaceMember` ORM 模型更名为 `Department`/`DepartmentMember`；`users.department` 文本列删除；注册时不再自动创建默认记录
- `user-auth`：注册成功后 SHALL NOT 创建默认 Department；`UserResponse.namespaces` 字段更名为 `departments`；`ProfileUpdate` 中删除 `department` 字段
- `node-registry`：`Node.namespace_id` 列重命名为 `department_id`；相关 API 字段、Schema 同步更新
- `admin-user-management`：`namespace_count` → `department_count`；`namespace_id`/`namespace_slug` → `department_id`/`department_slug`

## Impact

- **后端**：`models/`（2 文件）、`api/v1/`（7 文件）、`core/`（2 文件）、`schemas/`（4 文件）、`database/migrations/`（新增 1 文件）
- **前端**：`src/api/`（4 文件）、`src/views/`（涉及 `namespace_id`/`namespaces` 字段引用的组件）
- **数据库**：3 张表改名/改列、若干 FK 约束与索引重命名、`users` 表删除 1 列
- **SDK**：`nodevault_sdk/models.py` 中 `namespace_id` 字段更新
- **破坏性**：所有外部已持久化的 API 请求（含 `namespace_id` 字段）需更新；现有数据无损（仅结构重命名）
