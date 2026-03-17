## 1. 基础设施与配置

- [x] 1.1 更新 `deploy/docker-compose.dev.yml`，添加 MeiliSearch 服务（meilisearch/meilisearch:latest，port 7700）
- [x] 1.2 更新 `backend/core/config.py`，新增 `MEILISEARCH_URL`（默认 `http://localhost:7700`）和 `MEILISEARCH_API_KEY`（可选）配置项
- [x] 1.3 在 `pyproject.toml` 的依赖中添加 `meilisearch`（Python client）
- [x] 1.4 新增 Alembic 迁移：为 `invocation_logs` 表的 `(node_id, created_at)` 添加复合索引；为 `nodes` 表添加 `invocation_count` 整型字段（默认 0）

## 2. MeiliSearch 搜索核心

- [x] 2.1 创建 `backend/core/search.py`，实现 `NodeSearchIndex` 类（`setup_index`、`upsert_node`、`delete_node`、`search`、`_build_filter` 方法）
- [x] 2.2 在 `backend/main.py` 的 `lifespan` 中调用 `NodeSearchIndex().setup_index()`，异常时记录告警日志不阻断启动
- [x] 2.3 编写 `NodeSearchIndex` 单元测试（mock MeiliSearch client，覆盖搜索、upsert、delete、filter 构建）

## 3. 搜索 API

- [x] 3.1 创建 `backend/api/v1/search.py`，实现 `GET /api/v1/search/nodes`（全参数搜索）和 `GET /api/v1/search/suggest`（自动补全）
- [x] 3.2 实现 `POST /api/v1/search/reindex` 管理员接口，批量将数据库 active Node 同步到 MeiliSearch
- [x] 3.3 在 `backend/api/v1/router.py` 中挂载 search 路由
- [x] 3.4 编写搜索接口集成测试（关键词搜索、标签过滤、排序、MeiliSearch 不可用返回 503）

## 4. Node Registry 修改（索引同步）

- [x] 4.1 修改 `backend/api/v1/nodes.py` 的 Node 创建接口（`POST /api/v1/nodes`），成功写库后调用 `NodeSearchIndex.upsert_node()`，异常时仅记录日志
- [x] 4.2 修改 `backend/api/v1/nodes.py` 的 Node 更新接口（`PATCH /api/v1/nodes/{node_id}`），更新成功后同步更新索引
- [x] 4.3 修改 `backend/api/v1/nodes.py` 的 Node 删除接口（`DELETE /api/v1/nodes/{node_id}`），归档成功后调用 `NodeSearchIndex.delete_node()`
- [x] 4.4 更新 nodes 相关测试，确认索引同步被调用（mock NodeSearchIndex）

## 5. 版本管理增强

- [x] 5.1 创建 `backend/core/versioning.py`，实现 `VersionCompatibilityChecker`（`check_compatibility`、`suggest_version_bump` 方法）
- [x] 5.2 修改 `POST /api/v1/nodes/{node_id}/versions`，发布新版本时调用兼容性检查，将结果附加到响应的 `compatibility` 字段
- [x] 5.3 实现 `POST /api/v1/nodes/{node_id}/versions/{version}/set-default`（版本回滚接口）
- [x] 5.4 实现 `POST /api/v1/nodes/{node_id}/versions/{version}/deprecate`（版本弃用接口），并在调用已弃用版本时添加响应头 `X-NodeVault-Deprecation-Warning`
- [x] 5.5 实现 `GET /api/v1/nodes/{node_id}/changelog`（版本变更记录接口）
- [x] 5.6 编写 `VersionCompatibilityChecker` 单元测试（破坏性变更检测、版本号建议计算）
- [x] 5.7 编写版本管理 API 集成测试（回滚、弃用、changelog 查询、弃用版本调用时警告头）

## 6. 标签管理 API

- [x] 6.1 创建 `backend/api/v1/tags.py`，实现 `GET /api/v1/tags`（热门标签统计，基于数据库聚合查询）
- [x] 6.2 实现 `GET /api/v1/tags/{tag}/nodes`（按标签浏览 Node，含分页）
- [x] 6.3 在 `backend/api/v1/router.py` 中挂载 tags 路由
- [x] 6.4 编写标签接口测试（热门标签排序、按标签过滤、空结果返回空列表）

## 7. 调用统计 API

- [x] 7.1 创建 `backend/api/v1/stats.py`，实现 `GET /api/v1/nodes/{node_id}/stats`（聚合 invocation_logs，计算 total/success_rate/avg_latency/p95/p99/daily_trend/top_callers）
- [x] 7.2 修改 `backend/api/v1/invoke.py`（或 runtime），调用完成后异步递增 `nodes.invocation_count` 字段
- [x] 7.3 在 `backend/api/v1/router.py` 中挂载 stats 路由
- [x] 7.4 编写统计接口测试（正常统计、days 边界检查、无记录时返回零值）

## 8. Python SDK

- [x] 8.1 创建 `sdk/` 目录，添加独立 `pyproject.toml`（包名 `nodevault-sdk`，依赖 `httpx>=0.27`）
- [x] 8.2 实现 `sdk/nodevault_sdk/exceptions.py`（`NodeVaultError`、`AuthError`、`NodeNotFoundError`）
- [x] 8.3 实现 `sdk/nodevault_sdk/models.py`（`NodeResponse`、`InvokeResponse` Pydantic 模型）
- [x] 8.4 实现 `sdk/nodevault_sdk/client.py`（`NodeVaultClient`：登录、register、get、search、list_nodes、invoke）
- [x] 8.5 实现 `sdk/nodevault_sdk/client.py` 中的 `node()` 装饰器（含类型注解自动推断 schema、auto_register 参数）
- [x] 8.6 实现 `sdk/nodevault_sdk/async_client.py`（`AsyncNodeVaultClient`：异步 invoke、_get_node）
- [x] 8.7 实现 `sdk/nodevault_sdk/__init__.py`，导出 `NodeVaultClient`、`AsyncNodeVaultClient`、异常类
- [x] 8.8 编写 SDK 单元测试（mock httpx，覆盖登录/注册/get/search/invoke/装饰器/异常映射），目标覆盖率 ≥ 80%
- [x] 8.9 在项目根 `README.md` 的 SDK 章节添加快速入门示例

## 9. API 文档增强

- [x] 9.1 更新 `backend/main.py` 中 FastAPI 实例的 `description` 字段，补充认证说明和功能概览
- [x] 9.2 为所有新增路由（search/tags/stats/versioning）的每个端点添加 `summary`、`description`、`responses` 参数

## 10. 验收测试

- [x] 10.1 运行全量测试套件（`pytest --cov=backend`），确认覆盖率无下降，无新增失败用例
- [ ] 10.2 启动 docker-compose（含 MeiliSearch），手动验证：注册 Node → 搜索命中 → 调用 → 查看统计
- [ ] 10.3 验证 SDK 端到端：`pip install -e ./sdk`，运行 SDK 使用示例脚本，确认注册/搜索/调用全流程正常
