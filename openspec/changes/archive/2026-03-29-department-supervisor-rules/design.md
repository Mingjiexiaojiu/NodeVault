## Context

NodeVault 的部门模型当前存在以下问题：

1. `admin_create_department` 创建部门时自动将超级管理员加入 `department_members`（`role="admin"`），导致管理员出现在部门成员列表中
2. `admin_delete_department` 无成员保护，可直接删除有成员的部门（级联删除）
3. `list_departments_public`（注册下拉框）返回全部部门，包含尚无主管的"空壳"部门
4. 主管审批通过后没有任何强制的部门分配步骤，主管可长期游离于任何部门之外
5. `add_member` 端点允许任意用户被设置为 `role="admin"`，无平台角色校验

核心约束：**无 schema 变更**，所有改动限于业务逻辑层，利用现有 `users.role`（0/1/2）和 `department_members.role`（admin/member）两个字段。

---

## Goals / Non-Goals

**Goals:**
- 定义"部门主管" = `User.role==1` AND `DepartmentMember.role=="admin"` 同时成立
- 每个部门最多 1 个主管（唯一性校验）
- 管理员创建部门时不自动成为成员
- 有成员的部门无法被直接删除
- 注册下拉框只展示有主管的部门
- 主管审批通过必须同时分配到一个部门（原子操作）
- `add_member` 保留 `role="admin"` 路径，但增加校验

**Non-Goals:**
- 不引入数据库 schema 变更或新数据库迁移
- 不改变普通用户（`User.role==2`）加入部门的流程
- 不处理主管跨部门调换（可在后续迭代支持）
- 不修改节点/技能与部门的关联逻辑

---

## Decisions

### 决策 1：`部门主管` 的判定方式

**选择**：联合条件判定 —— `User.role==1 AND DepartmentMember.role=="admin"`

**备选方案**：
- 方案 A：仅 `DepartmentMember.role=="admin"` → 不与平台角色体系挂钩，语义不清晰
- 方案 B：在 `departments` 表增加 `supervisor_id` 列 → 需要 schema 变更，成本高

**理由**：现有两个字段的组合已能完整表达"既是平台级主管，又担任该部门管理角色"的语义，无需引入新字段。

---

### 决策 2：审批时强制分配部门的实现位置

**选择**：在 `POST /admin/role-applications/{id}/approve` 中新增必填参数 `department_id`，审批和分配在同一事务中原子完成。

**备选方案**：
- 方案 A：审批和分配分两步（先批准，再单独分配）→ 存在主管"批准但未分配"的中间态
- 方案 B：注册时选择目标部门，审批时自动分配 → 注册时目标部门状态不确定（可能已有主管）

**理由**：单次事务消除中间态，管理员在审批弹窗中选择目标部门，逻辑清晰。

`RoleApplicationReviewPayload` 新增字段：
```python
department_id: uuid.UUID  # 仅 requested_role==1 时必填
```

审批逻辑增量：
1. 如果 `app.requested_role == 1`，则 `department_id` 必填
2. 检查目标部门是否已有主管（`User.role==1` 且 `DepartmentMember.role=="admin"`）
3. 若已有主管 → 返回 `409 Conflict`
4. 通过检查后：`user.role = 1` + `DepartmentMember(dept_id, user_id, role="admin")` 在同一事务提交

---

### 决策 3：`add_member` 端点的处理

**选择**：保留 `role="admin"` 选项，但增加双重校验：
1. 目标用户 `User.role` 必须为 `1`（平台主管）
2. 目标部门当前没有主管

**理由**：允许管理员后续手动调整主管（无需重走审批流），增加灵活性；校验保证主管唯一性不被绕过。

---

### 决策 4：`list_departments_public` 过滤逻辑

**选择**：`WHERE EXISTS` 子查询过滤：

```sql
SELECT d.id, d.slug, d.display_name
FROM departments d
WHERE EXISTS (
    SELECT 1 FROM department_members dm
    JOIN users u ON dm.user_id = u.id
    WHERE dm.department_id = d.id
      AND dm.role = 'admin'
      AND u.role = 1
)
ORDER BY d.display_name
```

**理由**：单次查询，无额外 JOIN 膨胀，语义直接，性能充足（部门数量不会很大）。

---

### 决策 5：删除部门的保护逻辑

**检查条件**：`SELECT COUNT(*) FROM department_members WHERE department_id = {id}` > 0

**响应**：返回 `400 Bad Request`，`detail="部门仍有成员，无法删除"`

**前端处理**：删除确认弹窗已展示 `member_count`，后端返回 400 时前端展示错误提示即可（现有 `doDelete` 的 `catch` 已有错误显示能力，需补充 UI 文案）。

---

## Risks / Trade-offs

- **[风险] 主管离职/角色降级时部门将失去主管** → 当前不在本次范围内处理，后续可增加"部门主管接替"功能
- **[风险] 批准时选择了已有主管的部门，409 对用户体验不友好** → 前端审批弹窗的部门下拉仅展示无主管的部门，从源头避免此冲突
- **[权衡] `add_member` 保留 `role="admin"` 路径** → 两条分配路径（审批流 + 手动添加）需要在文档中明确，避免混淆

---

## Migration Plan

无数据库迁移。所有变更为纯业务逻辑修改，直接上线即可。

**部署顺序**（均可同批次部署）：
1. 后端：`admin.py`、`role_applications.py`、`departments.py`、`schemas/role_application.py`
2. 前端：`ApplicationsView.vue`、`api/admin.ts`（或 `roleApplications.ts`）

**回滚**：git revert 即可，无状态变更。

---

## Open Questions

- 前端审批弹窗的部门下拉数据来源：复用 `GET /admin/departments` 并在前端过滤 `supervisor==null`，还是后端提供专用接口 `GET /admin/departments?has_supervisor=false`？（推荐前端过滤，避免新增端点）
- 当主管被 `admin` 降级为 `role=2` 时，其 `DepartmentMember.role` 是否自动降为 `member`？（当前不在范围内）
