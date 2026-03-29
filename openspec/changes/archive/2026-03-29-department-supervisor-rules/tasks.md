## 1. 后端 Schema 更新

- [x] 1.1 在 `backend/schemas/role_application.py` 的 `RoleApplicationReviewPayload` 中新增 `department_id: uuid.UUID` 必填字段

## 2. 后端 admin.py 修改

- [x] 2.1 `admin_create_department`：删除创建部门后自动添加管理员为成员的 `DepartmentMember` 插入语句
- [x] 2.2 `admin_delete_department`：在删除前查询 `department_members` 成员数，若 > 0 则返回 `400 Bad Request`，`detail="部门仍有成员，无法删除"`

## 3. 后端 role_applications.py 修改

- [x] 3.1 `approve_application`：接收并验证 `payload.department_id` 必填
- [x] 3.2 `approve_application`：查询目标部门是否已有主管（`DepartmentMember.role=="admin"` 且 `User.role==1`），若有则返回 `409 Conflict`
- [x] 3.3 `approve_application`：在同一事务中原子执行角色升级（`user.role = 1`）+ 部门成员创建（`DepartmentMember(dept_id, user_id, role="admin")`）

## 4. 后端 departments.py 修改

- [x] 4.1 `list_departments_public`：改写查询，使用 `WHERE EXISTS` 子查询仅返回有主管（`DepartmentMember.role=="admin"` 且 `User.role==1`）的部门
- [x] 4.2 `add_member`：当 `payload.role == "admin"` 时，校验目标用户 `User.role == 1`，否则返回 `400`，`detail="只有平台主管（role=1）才能担任部门管理员"`
- [x] 4.3 `add_member`：当 `payload.role == "admin"` 时，校验目标部门当前无主管，否则返回 `409`，`detail="该部门已有主管"`

## 5. 前端 API 层更新

- [x] 5.1 在 `frontend/src/api/admin.ts`（或 `roleApplications.ts`）中，`approveApplication` 函数新增 `department_id: string` 参数，并传入请求体

## 6. 前端 ApplicationsView.vue 重构

- [x] 6.1 新增审批弹窗的响应式状态：`approveModal`（包含 `open`、`app`、`departmentId`、`note` 字段）
- [x] 6.2 新增 `availableDepartments` computed/ref，从已加载的部门列表中过滤 `supervisor_username == null` 的部门（在弹窗打开时调用 `listAllDepartments` 获取）
- [x] 6.3 将"通过"按钮的点击事件从 `handleApprove(app)` 改为 `openApproveModal(app)`，弹出审批弹窗
- [x] 6.4 实现审批弹窗模板：展示申请人信息、部门下拉框（无可用部门时禁用并提示）、审批备注输入框、取消/确认按钮
- [x] 6.5 实现 `handleApprove` 函数：调用更新后的 `approveApplication(app.id, { department_id, review_note })`，成功后关闭弹窗并刷新列表

## 7. 前端 NamespaceManageView.vue 优化

- [x] 7.1 删除确认弹窗中展示当前成员数（`ns.member_count`），提示"该部门有 N 名成员，删除前请先移除所有成员"
- [x] 7.2 `doDelete` 捕获后端 400 错误，展示"部门仍有成员，无法删除"提示信息
