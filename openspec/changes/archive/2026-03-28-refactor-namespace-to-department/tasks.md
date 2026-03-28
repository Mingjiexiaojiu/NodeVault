## 1. Alembic 数据库迁移

- [x] 1.1 新建迁移脚本 `backend/database/migrations/versions/phase14_rename_namespace_to_department.py`，`down_revision` 指向 phase13
- [x] 1.2 在 `upgrade()` 中：使用 `op.rename_table` 将 `namespaces` 重命名为 `departments`
- [x] 1.3 在 `upgrade()` 中：使用 `op.rename_table` 将 `namespace_members` 重命名为 `department_members`
- [x] 1.4 在 `upgrade()` 中：用 `op.alter_column` 将 `department_members.namespace_id` 重命名为 `department_id`
- [x] 1.5 在 `upgrade()` 中：用 `op.alter_column` 将 `nodes.namespace_id` 重命名为 `department_id`
- [x] 1.6 在 `upgrade()` 中：用 `op.alter_column` 将 `skills.namespace_id` 重命名为 `department_id`（如有该列）
- [x] 1.7 在 `upgrade()` 中：用 `op.drop_column` 删除 `users.department` 列
- [x] 1.8 在 `upgrade()` 中：用 `op.execute` 重命名所有相关 FK 约束和唯一索引名称（`uq_namespace_member` → `uq_department_member` 等）
- [x] 1.9 实现 `downgrade()` 逆操作（还原所有重命名和删除的列）
- [ ] 1.10 在本地执行 `alembic upgrade head` 验证迁移无报错

## 2. ORM 模型重构

- [x] 2.1 将 `backend/models/namespace.py` 重命名为 `backend/models/department.py`
- [x] 2.2 将文件中 `Namespace` 类改名为 `Department`，`__tablename__` 改为 `"departments"`
- [x] 2.3 将 `NamespaceMember` 类改名为 `DepartmentMember`，`__tablename__` 改为 `"department_members"`
- [x] 2.4 将 `DepartmentMember.namespace_id` 列及 FK 引用改为 `department_id`，指向 `departments.id`
- [x] 2.5 更新所有 relationship 引用名称（`namespace` → `department`，`members` 保持）
- [x] 2.6 更新唯一约束名：`uq_namespace_member` → `uq_department_member`
- [x] 2.7 更新 `backend/models/user.py`：删除 `department` 文本列；`owned_namespaces` relationship 改名为 `owned_departments`，`memberships` 改名为 `department_memberships`；更新 `foreign_keys` 指向
- [x] 2.8 更新 `backend/models/node.py`：列名 `namespace_id` → `department_id`，FK 引用 `departments.id`，relationship 名称更新
- [x] 2.9 更新 `backend/models/skill.py`（如有 `namespace_id`）：列名和 FK 同步更新
- [x] 2.10 更新 `backend/database/migrations/env.py`（或 `base.py`）中的 import 路径，将 `namespace` 改为 `department`

## 3. Pydantic Schema 更新

- [x] 3.1 更新 `backend/schemas/auth.py`：`UserNamespaceBrief` → `UserDepartmentBrief`，`UserResponse.namespaces` → `UserResponse.departments`，删除 `UserResponse.department` 字段，删除 `ProfileUpdate.department` 字段
- [x] 3.2 更新 `backend/schemas/admin.py`：`namespace_count` → `department_count`，`namespace_id` → `department_id`，`namespace_slug` → `department_slug`
- [x] 3.3 更新 `backend/schemas/node.py`：`namespace_id` → `department_id`
- [x] 3.4 检查 `backend/schemas/skill.py`、`backend/schemas/discovery.py` 等其余 Schema 文件，同步更新所有 `namespace_id`/`namespace` 字段名

## 4. API 路由 & Core 更新

- [x] 4.1 更新 `backend/api/v1/auth.py`：删除注册时自动创建 Namespace/NamespaceMember 的代码块；更新 import 路径（`namespace` → `department`）；将组装 `namespaces` 列表的逻辑改为 `departments`
- [x] 4.2 更新 `backend/api/v1/departments.py`：将所有 `Namespace`/`NamespaceMember` import 和引用改为 `Department`/`DepartmentMember`
- [x] 4.3 更新 `backend/api/v1/nodes.py`：将 `namespace_id` 相关查询参数、过滤逻辑、响应字段全部改为 `department_id`
- [x] 4.4 更新 `backend/api/v1/skills.py`：同步更新 `namespace_id` → `department_id`
- [x] 4.5 更新 `backend/api/v1/admin.py`：更新 import、字段名（`namespace_id`/`namespace_slug`/`namespace_count` → `department_*`）
- [x] 4.6 更新 `backend/api/v1/discovery.py`：`namespace_id` → `department_id`
- [x] 4.7 更新 `backend/api/v1/search.py`：`namespace_id` 过滤参数改为 `department_id`
- [x] 4.8 更新 `backend/core/registry.py`：所有 `namespace`/`Namespace`/`namespace_id` 引用全量替换为 `department`/`Department`/`department_id`；方法名如 `_get_namespace` → `_get_department`，`_check_namespace_permission` → `_check_department_permission`
- [x] 4.9 更新 `backend/core/skill_registry.py`：同 4.8，全量替换
- [x] 4.10 更新 `backend/core/search.py`：`namespace_id` 索引字段和过滤逻辑改为 `department_id`

## 5. 前端 API 类型更新

- [x] 5.1 更新 `frontend/src/api/auth.ts`：`UserNamespaceBrief` → `UserDepartmentBrief`，`namespaces` → `departments`，删除 `department` 文本字段
- [x] 5.2 更新 `frontend/src/api/nodes.ts`：请求/响应中 `namespace_id` → `department_id`
- [x] 5.3 更新 `frontend/src/api/skills.ts`：`namespace_id` → `department_id`
- [x] 5.4 更新 `frontend/src/api/discovery.ts`：`namespace_id` → `department_id`
- [x] 5.5 全局搜索前端代码中所有 `namespace_id`、`namespaces`（非 CSS 类名）的引用，逐一更新到 `department_id`/`departments`
- [x] 5.6 更新 `frontend/src/api/admin.ts`：`AdminNamespaceListItem` → `AdminDepartmentListItem`，`listAllNamespaces` → `listAllDepartments`，所有 `namespace_*` 字段改为 `department_*`
- [x] 5.7 更新所有 Vue 视图文件中的 `namespace_slug`/`.namespaces` 引用

## 6. SDK 更新

- [x] 6.1 更新 `sdk/nodevault_sdk/models.py`：`NodeResponse.namespace_id` → `department_id`，其他相关字段同步更新

## 7. 验证

- [x] 7.1 后端 ORM 模型导入无报错，所有 Python 语法检查通过
- [ ] 7.2 执行 `alembic upgrade head` 和 `alembic downgrade -1` 均无报错
- [x] 7.3 前端 TypeScript 类型检查零错误（`npx tsc --noEmit`）
- [x] 7.4 全局 grep `namespace_id` 和 `Namespace`（排除注释和历史迁移文件），确认无遗漏引用
