## Why

服务发现流程目前是无状态的——探测结果存在前端内存中，刷新即丢失，也无法追溯每次发现了什么、导入了哪些接口。将每次探测会话持久化到数据库，既能提供操作历史，也能在会话列表页作为入口统一管理服务发现。

## What Changes

- 新增 `DiscoverySession` 数据库模型，记录每次探测和导入的元数据
- `Node` 模型增加 `discovery_session_id` 外键，关联其来源会话
- 探测 API 在开始时创建 session，导入完成后更新 session 状态与统计
- 前端路由拆分：`/discover` 变为会话历史列表，`/discover/new` 是现有三步向导，`/discover/:id` 是会话详情
- 会话详情页支持查看已导入 / 未导入接口，并可对未导入接口补充导入

## Capabilities

### New Capabilities

- `discovery-session`: 探测会话的生命周期管理——创建、状态流转（probing → found/failed → completed）、与 Node 的关联
- `frontend-discovery-history`: 服务发现历史列表页与会话详情页

### Modified Capabilities

- `frontend-service-discovery`: 路由结构变更（`/discover` → `/discover/new`），导入完成后跳转到历史列表
- `batch-import`: 批量导入接口增加 `session_id` 参数，导入后更新会话统计

## Impact

- **Backend**: 新增 `DiscoverySession` model、Alembic migration、sessions CRUD API（`/discovery/sessions`）
- **Frontend**: 新增 `DiscoverySessionListView`、`DiscoverySessionDetailView`，路由调整，`ServiceDiscoveryView` 微调
- **Database**: 新表 `discovery_sessions`，`nodes` 表新增 `discovery_session_id` 列
- **现有 API**: `/discovery/probe`、`/discovery/import` 接收可选 `session_id` 参数（向后兼容）
