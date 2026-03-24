## 1. 后端基础设施

- [x] 1.1 在 `backend/auth/deps.py` 新增 `get_superadmin_user` 依赖函数（role != 0 时抛出 HTTP 403）
- [x] 1.2 新建 `backend/api/v1/admin.py`，注册空路由 prefix `/admin`，引入 `get_superadmin_user` 守卫
- [x] 1.3 在 `backend/api/v1/router.py` 中注册 admin 路由
- [x] 1.4 创建 Alembic migration，新增 `system_settings (key VARCHAR PK, value TEXT, updated_at TIMESTAMP)` 表
- [x] 1.5 新增 `backend/models/system_setting.py` ORM 模型
- [x] 1.6 新增 `backend/schemas/admin.py`，定义所有管理端 request/response schema

## 2. 用户管理 API

- [x] 2.1 实现 `GET /admin/users`——分页列表，支持 q/role/is_active 过滤
- [x] 2.2 实现 `GET /admin/users/{user_id}`——用户详情 + 资源统计（namespace/node/skill 数量）
- [x] 2.3 实现 `PATCH /admin/users/{user_id}/status`——封禁/解封，含唯一超管保护
- [x] 2.4 实现 `PATCH /admin/users/{user_id}/role`——角色变更，含唯一超管保护
- [x] 2.5 实现 `DELETE /admin/users/{user_id}`——删除用户，含唯一超管保护

## 3. 全局资源视图 API

- [x] 3.1 实现 `GET /admin/nodes`——跨 namespace 全局节点列表，支持 namespace_id/status/category_id 过滤
- [x] 3.2 实现 `PATCH /admin/nodes/{node_id}/status`——强制上下线节点
- [x] 3.3 实现 `GET /admin/namespaces`——所有 namespace 列表，含 member_count/node_count
- [x] 3.4 实现 `GET /admin/skills`——跨 namespace 全局技能列表

## 4. 分类管理权限收紧

- [x] 4.1 在 `backend/api/v1/categories.py` 的 POST/PUT/DELETE 端点改用 `get_superadmin_user` 守卫（或检查 role 后抛出 403）

## 5. 平台统计 API

- [x] 5.1 实现 `GET /admin/analytics/overview`——总用户/节点/技能/调用量 + 24h 新增统计
- [x] 5.2 实现 `GET /admin/analytics/invocations`——按 range=7d/30d/90d 的每日调用趋势
- [x] 5.3 实现 `GET /admin/analytics/top-nodes`——调用量最多的前 N 个节点
- [x] 5.4 实现 `GET /admin/analytics/top-users`——节点数最多的前 N 个用户

## 6. 系统设置 API

- [x] 6.1 实现 `GET /admin/settings`——返回所有系统配置项
- [x] 6.2 实现 `PUT /admin/settings/{key}`——更新配置项，校验 key 白名单
- [x] 6.3 实现 `GET /settings/announcement`（无需认证）——返回平台公告
- [x] 6.4 在 seed migration 中写入默认配置：`enable_registration=true`、`platform_announcement=`

## 7. 前端路由与布局

- [x] 7.1 新建 `frontend/src/layouts/AdminLayout.vue`——含侧边导航（用户管理/全局节点/分类管理/平台统计/系统设置）
- [x] 7.2 在 `frontend/src/router/index.ts` 新增 `/admin` 路由组，使用 AdminLayout，注册 5 个子路由
- [x] 7.3 在路由 `beforeEach` 守卫中添加 `/admin` 前缀检测，role !== 0 时重定向 `/`
- [x] 7.4 在 `frontend/src/stores/auth.ts` 暴露 `isSuperAdmin` 计算属性
- [x] 7.5 在主导航栏（MainLayout/NavBar）根据 `isSuperAdmin` 条件显示「管理控制台」入口链接

## 8. 前端管理页面

- [x] 8.1 实现 `frontend/src/views/admin/UserManageView.vue`——用户表格 + 搜索 + 封禁/角色操作
- [x] 8.2 实现 `frontend/src/views/admin/GlobalNodesView.vue`——全局节点表格 + 过滤 + 强制下线操作
- [x] 8.3 实现 `frontend/src/views/admin/AdminAnalyticsView.vue`——概览卡片 + 折线图（纯 SVG）+ 时间范围切换
- [x] 8.4 实现 `frontend/src/views/admin/AdminSettingsView.vue`——配置项列表 + 内联编辑 + 保存提示

## 9. 前端 API 层

- [x] 9.1 在 `frontend/src/api/` 新建 `admin.ts`，封装所有 `/admin/` 接口的 axios 调用

## 10. 测试与验证

- [x] 10.1 后端：为 `get_superadmin_user` 守卫编写单元测试（role=0 通过，role=1/2 返回 403）
- [x] 10.2 后端：为用户管理 API 编写集成测试（含唯一超管保护场景）
- [x] 10.3 后端：为全局资源 API 编写集成测试（验证跨 namespace 可见性）
- [ ] 10.4 前端：手动验证路由守卫——普通账号无法访问 `/admin/*`
- [ ] 10.5 端到端：用超管账号完整走一遍用户封禁、节点下线、设置修改流程
