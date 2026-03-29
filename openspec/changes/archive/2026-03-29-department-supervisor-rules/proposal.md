## Why

当前部门管理存在多处逻辑漏洞：管理员创建部门时会被自动加入为成员、空部门可被随意解散、普通用户注册时能看到尚无主管的"空壳"部门、主管审批通过后也没有被强制分配到任何部门。这些问题导致部门生命周期缺乏约束，注册流程对用户造成困惑。

## What Changes

- **移除**：管理员通过 `/admin/departments` 创建部门时，不再自动将自身加入 `department_members`
- **新增**：删除部门前检查成员数，若部门仍有成员则阻止删除（返回 400）
- **新增**：定义"部门主管" = `User.role==1` 且 `DepartmentMember.role=="admin"` 同时成立
- **新增**：每个部门最多只允许一个主管（唯一性约束，在添加成员及审批流程中双重校验）
- **修改**：`/departments/public` 注册用公开部门列表，仅返回已有主管的部门
- **修改**：审批主管角色申请（`POST /admin/role-applications/{id}/approve`）时，必须同时指定目标部门，审批操作原子性地完成角色升级 + 加入部门（`role="admin"`）
- **修改**：`add_member` 端点添加校验——若 `role="admin"` 则目标用户须为 `User.role==1` 且该部门尚无主管
- **修改**：前端审批弹窗改为"审批 + 分配部门"合体弹窗，部门下拉仅展示无主管的部门

## Capabilities

### New Capabilities

- `department-supervisor`: 部门主管的定义、唯一性约束、生命周期规则（创建时为空、删除须无成员、注册可见性与主管绑定）

### Modified Capabilities

- `role-application`: 审批主管申请时新增必填字段 `department_id`，审批原子操作扩展为角色升级 + 部门主管分配
- `frontend-admin-console`: 审批操作由直接调用改为弹窗流程，新增部门选择（仅展示无主管部门）

## Impact

**后端**
- `backend/api/v1/admin.py` — `admin_create_department`、`admin_delete_department`
- `backend/api/v1/role_applications.py` — `approve_application`
- `backend/api/v1/departments.py` — `list_departments_public`、`add_member`
- `backend/schemas/role_application.py` — `RoleApplicationReviewPayload` 新增 `department_id`

**前端**
- `frontend/src/views/admin/ApplicationsView.vue` — 审批弹窗重构
- `frontend/src/api/admin.ts` 或 `roleApplications.ts` — `approveApplication` 新增参数

**数据库**：无 schema 变更，仅业务逻辑层约束
