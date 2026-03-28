## 1. 数据库迁移

- [x] 1.1 新建 Alembic 迁移脚本（`phase15_role_applications_and_dept_member_status.py`），`down_revision` 指向最新迁移
- [x] 1.2 在 `upgrade()` 中：创建 `role_applications` 表（含所有字段、FK 约束、index on user_id/status）
- [x] 1.3 在 `upgrade()` 中：为 `department_members` 表新增 `status` VARCHAR(16) 字段，默认值 `'active'`，NOT NULL
- [x] 1.4 实现 `downgrade()` 逆操作（删除 `role_applications` 表，删除 `department_members.status` 字段）

## 2. ORM 模型

- [x] 2.1 新建 `backend/models/role_application.py`：定义 `RoleApplication` ORM 模型，含所有字段和与 User 的 relationship
- [x] 2.2 更新 `backend/models/department.py`：为 `DepartmentMember` 新增 `status` 字段（VARCHAR(16)，默认 `'active'`）
- [x] 2.3 更新 `backend/models/__init__.py`：导出 `RoleApplication`
- [x] 2.4 更新 `backend/database/migrations/env.py`：确保 import `RoleApplication` 模型

## 3. Pydantic Schema 更新

- [x] 3.1 更新 `backend/schemas/auth.py`：`UserRegister` 新增可选字段 `requested_role: int = 2` 和 `department_id: uuid.UUID | None = None`；`UserResponse` 新增 `pending_role_application` 字段（可为空的嵌套对象）
- [x] 3.2 新建 `backend/schemas/role_application.py`：定义 `RoleApplicationCreate`、`RoleApplicationResponse`、`RoleApplicationReviewPayload` 等 Pydantic 模型
- [x] 3.3 更新 `backend/schemas/admin.py`：新增 `AdminRoleApplicationListItem` schema

## 4. 后端 API 实现

- [x] 4.1 更新 `backend/api/v1/auth.py` 注册逻辑：解析 `requested_role` 和 `department_id`；若 `requested_role=1` 则创建 `RoleApplication(status='pending')`；若提供 `department_id` 则创建 `DepartmentMember(status='pending')`
- [x] 4.2 更新 `backend/api/v1/auth.py` `/me` 端点：查询并附加 `pending_role_application` 字段到响应
- [x] 4.3 新建 `backend/api/v1/role_applications.py`：实现 `GET /admin/role-applications`（分页，支持 status 过滤）、`POST /admin/role-applications/{id}/approve`、`POST /admin/role-applications/{id}/reject`
- [x] 4.4 更新 `backend/main.py`（或路由注册处）：注册新路由 `/admin/role-applications`
- [x] 4.5 更新所有查询 `DepartmentMember` 正式成员的逻辑：添加 `.where(DepartmentMember.status == 'active')` 过滤

## 5. 前端类型更新

- [x] 5.1 更新 `frontend/src/api/auth.ts`：`RegisterPayload` 新增 `requested_role?: number` 和 `department_id?: string`；`UserResponse` 新增 `pending_role_application` 可选字段
- [x] 5.2 新建 `frontend/src/api/roleApplications.ts`：定义 `RoleApplicationItem` 类型和 `listRoleApplications`、`approveApplication`、`rejectApplication` API 函数

## 6. 前端注册页改造

- [x] 6.1 更新 `RegisterView.vue`：在表单中添加身份选择单选区块（普通用户 / 申请成为主管）
- [x] 6.2 添加条件式部门选择下拉框（仅普通用户选中时显示），初始化时调用 `GET /api/v1/departments` 加载部门列表
- [x] 6.3 选择"申请成为主管"时显示提示文字，隐藏部门选择区块
- [x] 6.4 注册提交逻辑：根据身份选择携带 `requested_role` 或 `department_id` 字段
- [x] 6.5 主管申请注册成功后显示一次性提示："主管申请已提交，管理员审批通过后权限将自动升级"

## 7. 管理员后台改造

- [x] 7.1 更新 `AdminLayout.vue` navItems：调整顺序为 `用户管理 | 全局节点 | 分类管理 | 平台统计 | 部门管理 | 申请管理 | 系统设置`，路由 `/admin/auth` 改为 `/admin/applications`，label 改为"申请管理"
- [x] 7.2 新建（或改写）`frontend/src/views/admin/ApplicationsView.vue`：展示主管申请列表，包含统计卡片（待审批/已批准/已拒绝）、表格（申请人信息、状态徽章、操作按钮）
- [x] 7.3 实现审批操作：点击"通过"调用 `approveApplication`，点击"拒绝"弹出备注输入框后调用 `rejectApplication`，操作后刷新列表
- [x] 7.4 实现 status 筛选 Tab（全部/待审批/已批准/已拒绝）
- [x] 7.5 更新 `AdminSettingsView.vue`：将原 `AuthManageView.vue` 的 API Key 管理区块迁移至系统设置页
- [x] 7.6 更新前端路由（`router/index.ts`）：`/admin/applications` 指向 `ApplicationsView.vue`
- [x] 7.7 原 `AuthManageView.vue` 内容可清空或删除（保留文件壳或直接删除由路由决定）

## 8. 验证

- [x] 8.1 后端语法检查：`python -m py_compile` 所有新增/修改文件无报错
- [ ] 8.2 执行 `alembic upgrade head`，确认新表和新字段创建成功
- [x] 8.3 前端 TypeScript 类型检查：`npx tsc --noEmit` 零错误
- [ ] 8.4 手动测试：以"申请成为主管"注册 → 后台"申请管理"可见申请 → 审批通过 → 用户 role 变为 1
- [ ] 8.5 手动测试：以"普通用户+选择部门"注册 → 部门管理页可见 pending 成员 → 主管审批后成员正式加入
