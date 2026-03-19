## Context

当前服务发现是一次性流程：用户输入 URL → 探测 → 预览接口 → 批量导入，全程数据仅存在前端内存。导入完成后历史不可查，也无法关联"此 Node 来自哪次发现"。

现有相关代码：
- `backend/api/v1/discovery.py` — probe / import 四个端点，无持久化
- `backend/core/probe.py` — 探测引擎，返回 `ProbeResult` dataclass
- `backend/models/node.py` — `Node` 已有 `source_path`、`source_credential_id`，加 FK 很自然
- `frontend/src/views/ServiceDiscoveryView.vue` — 三步向导，现在挂在 `/discover`
- `backend/database/migrations/versions/` — Alembic 迁移，已有 phase1-phase9

## Goals / Non-Goals

**Goals:**
- `DiscoverySession` 模型持久化每次探测的元数据（URL、状态、发现数、导入数）
- Node 增加 `discovery_session_id` 外键，支持追溯来源
- 前端路由拆分：列表 → `/discover`，向导 → `/discover/new`，详情 → `/discover/:id`
- 历史列表显示所有 session；详情页可查看已导入/未导入接口，可补充导入

**Non-Goals:**
- 不存储原始 spec 快照（JSON 体积大，意义有限，可未来扩展）
- 不支持 session 共享或多用户协作
- 不做探测进度的实时推送（仍然是同步请求）

## Decisions

### D1: Session 在探测开始时创建（status: "probing"）

**选择**：在 `POST /discovery/probe` 被调用**之前**，由前端先调用 `POST /discovery/sessions` 创建 session，拿到 `session_id`，再带着它做探测和导入。

**备选**：在 probe API 内部自动创建。

**理由**：前端显式创建更灵活——upload-spec 场景也能走同样流程；session_id 在整个向导生命周期中保持一致；且允许前端在 probe 失败时仍记录失败的 session（"避免反复探测同一个坏地址"的价值）。

### D2: Node.discovery_session_id 作为可空 FK（不强制关联）

**选择**：`nodes.discovery_session_id` 可空，手动注册的 Node 为 NULL。

**理由**：向后兼容所有已有 Node，不破坏现有导入逻辑；API 通过可选参数传递 session_id（向后兼容）。

### D3: 路由分离，ServiceDiscoveryView 保留三步结构不变

**选择**：`/discover` → 新的列表页；`/discover/new` → 现有向导（路由名改为 `discover-new`）；`/discover/:id` → 新的详情页。

**备选**：同页 state 切换。

**理由**：路由分离支持浏览器后退、详情页 permalink；`/discover/:id` 未来可独立扩展；现有 `ServiceDiscoveryView.vue` 改动极小（跳转 URL 从 `/nodes` 改为 `/discover`，加传 `session_id`）。

### D4: 详情页"补充导入"通过复用现有 batch-import API

**选择**：详情页拉取 session 关联的已导入 endpoint 列表，将剩余接口提交到 `POST /discovery/import`（带同一个 session_id）。

**理由**：无需新的导入 API，简单复用；session 的 `imported_count` 自动累加。

## Risks / Trade-offs

- **前端需要管理 session_id 状态**：向导组件需要在 probe 成功后记住 session_id，并在 import 时携带。若用户中途刷新页面，session 留在 "probing" 状态。
  → 缓解：前端将 session_id 存 `sessionStorage`，刷新页面时恢复；或接受"孤立的 probing 状态 session"（列表页可以标记为"未完成"）。

- **upload-spec 场景的 base_url 为空**：上传 Spec 文件时没有 base_url。
  → 接受：`DiscoverySession.base_url` 允许为空字符串，`source` 字段区分 `"probe"` vs `"upload"`，列表页展示时做适配。

- **Node 新增 migration**：`nodes` 表加列需要 Alembic migration（phase10）。
  → 低风险：可空列，无数据迁移。

## Migration Plan

1. 新增 Alembic migration `phase10_discovery_sessions`：创建 `discovery_sessions` 表，`nodes` 加 `discovery_session_id` 列
2. 后端新增 `DiscoverySession` model 和 `/discovery/sessions` CRUD
3. 修改 probe / import API 接收可选 `session_id`（向后兼容）
4. 前端：新增两个 View、调整路由、`ServiceDiscoveryView` 微调
5. 无需数据回填，老 Node 的 `discovery_session_id` 保持 NULL

**回滚**：
- 前端路由改动可独立回滚
- 数据库 migration 可 `alembic downgrade`（仅删表/删列，无数据干扰）

## Open Questions

- 详情页展示"未导入接口"需要重新 probe 还是存储接口列表快照？当前方案不存快照，详情页的"未导入接口"需重新探测。是否可接受？（可在 tasks 中明确为"重新探测"方案）
