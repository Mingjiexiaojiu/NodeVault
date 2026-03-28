## Why

注册流程目前没有角色区分，所有新用户默认为普通用户（role=2），无法表达自己想成为主管的意愿；管理员也没有统一的申请审批入口来管理角色晋升请求。随着部门化改造完成，需要配套的角色申请机制让注册流程更合理、更有组织管理意义。

## What Changes

- **注册表单新增身份选择**：注册时单选"普通用户"或"申请成为主管"两种身份
- **普通用户注册**：在身份选择后追加"选择部门"步骤，注册完成后自动生成部门加入申请（待该部门主管审批）
- **主管申请注册**：注册后创建 `role_applications` 记录（status=pending），账号立即可用（role 暂为 2），管理员审批通过后 role 升为 1
- **新建 `role_applications` 表**：完整审计记录，支持申请理由、审批备注、审批人等字段
- **管理员"申请管理"页**：原"授权管理（API Key 管理）"改名为"申请管理"，内容替换为主管申请列表，支持审批/拒绝操作；API Key 管理入口迁移至"系统设置"
- **管理员导航调整**：将"平台统计"从第一项移至导航栏正中间位置（第4项，共7项）

## Capabilities

### New Capabilities

- `role-application`: 主管角色申请的完整生命周期——申请提交、审批流程、状态通知、`role_applications` 数据模型

### Modified Capabilities

- `user-auth`: 注册流程新增身份选择（普通用户/主管申请）和部门选择步骤，`UserRegister` schema 新增 `requested_role` 和 `department_id` 字段
- `frontend-auth`: 注册页面 UI 改造，新增角色单选、条件式部门选择步骤
- `admin-user-management`: 管理员可审批主管申请，`AdminUserDetail` 补充申请状态信息
- `frontend-admin-console`: 管理员导航重排（平台统计移至中间），"授权管理"改为"申请管理"页面，API Key 管理迁移至系统设置
- `database-models`: 新增 `role_applications` 表定义和 Alembic 迁移

## Impact

- **后端**：新增 `backend/models/role_application.py`，新增 `backend/api/v1/role_applications.py`，修改 `backend/api/v1/auth.py`（注册逻辑），修改 `backend/api/v1/admin.py`（审批接口），新增 Alembic 迁移脚本
- **前端**：修改 `RegisterView.vue`（注册步骤），修改 `AdminLayout.vue`（导航顺序），修改 `AuthManageView.vue`（改为申请管理内容），修改 `AdminSettingsView.vue`（补充 API Key 管理）
- **数据库**：新增 `role_applications` 表，无破坏性变更
- **API**：新增 `/api/v1/role-applications/` 端点，注册接口请求体新增可选字段（向后兼容）
