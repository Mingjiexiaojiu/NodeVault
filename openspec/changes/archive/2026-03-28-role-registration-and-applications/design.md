## Context

系统已完成部门化改造（namespaces → departments），用户角色体系为：0=超级管理员、1=主管、2=普通用户。目前所有注册用户默认 role=2，没有途径主动申请成为主管；管理员后台的"授权管理"页面当前展示 API Key 审计，与页面名称语义不符。本次变更在现有角色体系上叠加申请审批流程，不改变已有权限校验逻辑。

## Goals / Non-Goals

**Goals:**

- 注册表单支持角色意向选择（普通用户 / 主管申请）
- 普通用户注册时可选择期望加入的部门，注册后自动发起 `DepartmentMember` 加入申请（status=pending，等待主管审批）
- 主管申请者注册后账号立即可用（role 暂为 2），申请记录写入 `role_applications` 表，管理员审批通过后 role 升为 1
- 管理员"申请管理"页展示 `role_applications` 列表，支持一键审批/拒绝
- 管理员导航：平台统计移至第 4 位（正中间），"授权管理"改为"申请管理"
- API Key 管理入口迁移至"系统设置"页

**Non-Goals:**

- 不支持普通用户在注册后自助发起主管申请（可后续迭代）
- 不支持邮件通知审批结果（可后续迭代）
- 不修改主管对部门成员申请的审批流程（已有逻辑）

## Decisions

### D1：新建 `role_applications` 表，不在 `users` 表加字段

**选择**：独立表，完整审计记录。

**理由**：用户可能多次申请，需要保存历史；需要记录审批人、审批时间、备注；在 users 表加字段会导致 schema 膨胀，且无法支持多条记录。

**放弃的方案**：`users.pending_role` 字段——简单但无审计能力。

### D2：主管申请人注册后账号立即可用，role 不变

**选择**：role 保持 2，通过 `role_applications.status` 表达申请状态。

**理由**：阻断账号登录（is_active=False 等待审批）体验差；现有 role=2 权限集合不影响正常使用；审批通过后数据库 UPDATE users.role=1 即可，改动极小。

### D3：部门加入申请复用现有 `DepartmentMember` pending 机制

**选择**：注册时若选择了部门，创建 `DepartmentMember(role='member', status='pending')` 记录。

**理由**：现有 `department_members` 表已有 `role` 字段，只需增加 `status` 字段（'active'/'pending'/'rejected'）即可支持申请流程，无需新表。主管在部门管理页审批成员申请的逻辑可复用。

**注意**：`department_members` 表需要在现有 Alembic 迁移之上追加 `status` 字段迁移。

### D4：API Key 管理迁移至"系统设置"页

**选择**：在 `AdminSettingsView.vue` 中增加"API 密钥"Tab/区块。

**理由**：API Key 是系统级审计资源，与"系统设置"的语义更接近；"授权管理"这个名字用于"申请管理"更为贴切。

### D5：导航顺序调整为 7 项固定布局

新顺序：`用户管理 | 全局节点 | 分类管理 | 平台统计 | 部门管理 | 申请管理 | 系统设置`

平台统计（第 4 项）作为数据概览放中间，两侧是管理类操作，视觉和语义都更均衡。

## Risks / Trade-offs

- **[风险] `department_members.status` 新字段**：现有代码对 `DepartmentMember` 的查询未过滤 status，可能把 pending 成员展示为正式成员。→ **缓解**：所有查询正式成员的地方加 `status='active'` 过滤；新注册加入申请默认写 `status='pending'`。
- **[风险] 主管申请人 role=2 期间权限混乱**：用户申请了主管但仍是普通用户，界面没有提示。→ **缓解**：注册成功页显示"申请已提交，等待管理员审批"提示；`/me` 接口返回 `pending_role_application` 状态字段供前端展示。
- **[权衡] 注册步骤增加**：选择身份、选择部门增加了注册摩擦。→ 接受：这符合企业级组织管理语义，部门非必填（可跳过）。

## Migration Plan

1. 新建 Alembic 迁移：新增 `role_applications` 表；为 `department_members` 增加 `status` 字段（默认 `'active'`，保持现有数据不受影响）
2. 更新 ORM 模型、Pydantic schema、API 端点
3. 更新注册前端逻辑
4. 更新管理后台导航和"申请管理"页
5. Rollback：`alembic downgrade -1` 删除新增字段和表，前端回滚 navItems 顺序
