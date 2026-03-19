## 1. 数据库模型

- [x] 1.1 新增 `DiscoverySession` SQLAlchemy model（`backend/models/discovery.py`）：字段 `id`, `user_id`, `base_url`, `source`, `status`, `spec_url`, `total_operations`, `imported_count`, `created_at`, `completed_at`
- [x] 1.2 在 `Node` model 增加可空字段 `discovery_session_id`（FK → `discovery_sessions.id`）
- [x] 1.3 在 `backend/models/__init__.py` 导出 `DiscoverySession`
- [x] 1.4 编写 Alembic migration `phase10_discovery_sessions`：创建 `discovery_sessions` 表，`nodes` 表加 `discovery_session_id` 列

## 2. Schemas

- [x] 2.1 在 `backend/schemas/discovery.py` 新增 `DiscoverySessionCreate`、`DiscoverySessionSchema`、`DiscoverySessionDetail`（含 linked nodes 列表）
- [x] 2.2 `BatchImportRequest` 增加可选字段 `session_id: UUID | None`

## 3. 后端 API

- [x] 3.1 新增 `POST /discovery/sessions`：创建 session（status: "probing"）
- [x] 3.2 新增 `PATCH /discovery/sessions/{id}`：更新 status、spec_url、total_operations、imported_count
- [x] 3.3 新增 `GET /discovery/sessions`：分页返回当前用户的 session 列表，按 `created_at` 降序
- [x] 3.4 新增 `GET /discovery/sessions/{id}`：返回 session 详情 + 关联 Node 列表
- [x] 3.5 修改 `POST /discovery/import`：接受可选 `session_id`，导入成功后将 Node 的 `discovery_session_id` 设为该 session ID，并 PATCH session 为 `completed` + 更新 `imported_count`

## 4. 前端 API 层

- [x] 4.1 在 `frontend/src/api/discovery.ts` 新增 `createSession`、`updateSession`、`listSessions`、`getSession` 函数
- [x] 4.2 更新 `batchImport` 函数签名，接受可选 `session_id`

## 5. 前端路由调整

- [x] 5.1 在 `frontend/src/router/index.ts` 将 `/discover` 改为 `DiscoverySessionListView`，新增 `/discover/new` 指向 `ServiceDiscoveryView`，新增 `/discover/:id` 指向 `DiscoverySessionDetailView`
- [x] 5.2 修复 `AppLayout.vue` 导航高亮：`/discover`、`/discover/new`、`/discover/:id` 都激活"发现"链接

## 6. ServiceDiscoveryView 调整

- [x] 6.1 probe 之前调用 `createSession` 拿到 `session_id`，存入组件 state
- [x] 6.2 probe 成功后调用 `updateSession`（status: "found", spec_url, total_operations）
- [x] 6.3 probe 失败后调用 `updateSession`（status: "failed"）
- [x] 6.4 `batchImport` 调用时携带 `session_id`
- [x] 6.5 导入成功后跳转到 `/discover`（原来跳 `/nodes`）

## 7. DiscoverySessionListView（新页面）

- [x] 7.1 创建 `frontend/src/views/DiscoverySessionListView.vue`，调用 `listSessions` 并渲染表格：创建时间、来源 URL / 文件上传、发现数、导入数、状态 Badge
- [x] 7.2 状态 Badge：`probing` → 灰色 spinner，`found` → 蓝色，`failed` → 红色，`completed` → 绿色
- [x] 7.3 空状态：展示提示文案 + "新建发现"按钮
- [x] 7.4 点击行跳转到 `/discover/:id`；顶部"新建发现"按钮跳转到 `/discover/new`

## 8. DiscoverySessionDetailView（新页面）

- [x] 8.1 创建 `frontend/src/views/DiscoverySessionDetailView.vue`，调用 `getSession` 渲染 session 元数据（URL、状态、时间）
- [x] 8.2 渲染已关联 Node 列表（name、display_name、source_path、状态）并链接到各自详情页
- [x] 8.3 顶部"← 返回"按钮跳转到 `/discover`
