## Context

NodeVault Phase 1 已完成：用户认证、Node CRUD、基于 HTTP/Docker 的 Node 调用、调用日志等核心功能。当前 Node 查询仅支持数据库字段精确过滤（name、type、status），无法满足关键词模糊搜索、中文分词、标签聚合等场景。

对接方（Agent、开发者）集成 NodeVault 时仍需手写 HTTP 请求，缺乏官方 SDK，接入成本高。Phase 2 在此基础上叠加搜索层与 SDK 层，不改变现有数据模型和接口，以"渐进增强"方式引入。

## Goals / Non-Goals

**Goals:**
- 为 Node 提供全文搜索能力（关键词 + 标签 + 类型联合查询）
- 提供搜索自动补全接口，支持前端搜索框实时提示
- 版本兼容性检查：注册新版本时检测破坏性变更并给出建议版本号
- 提供版本回滚与弃用接口
- 标签管理：热门标签统计、按标签浏览 Node
- Node 调用统计接口（调用量、成功率、P95/P99 延迟）
- Python SDK 同步版 + 异步版，封装登录、Node CRUD、搜索、调用
- `@vault.node` 装饰器支持从函数类型注解自动生成 input/output schema

**Non-Goals:**
- 语义向量搜索（Phase 3+）
- GraphQL 接口
- SDK 发布到 PyPI（本阶段仅输出本地可安装包）
- Node 调用统计的实时仪表盘前端（仅后端 API）
- 调用统计数据库新表（复用已有 `invocation_logs`）

## Decisions

### 1. 搜索引擎选型：MeiliSearch vs Elasticsearch

**选择：MeiliSearch**

| 维度 | MeiliSearch | Elasticsearch |
|------|-------------|---------------|
| 部署复杂度 | 单二进制/Docker，零配置 | 需要 JVM，配置繁琐 |
| 中文分词 | 内置 Unicode 分词，可接受 | 需要 ik-analyzer 插件 |
| 容错搜索 | 原生支持 typo tolerance | 需要模糊查询配置 |
| 性能 | Rust 实现，低内存占用 | Java，内存消耗大 |
| 开发体验 | REST API 极简 | 学习曲线陡峭 |

结论：MeiliSearch 在开发友好性和资源占用上显著优于 ES，适合当前规模。

### 2. 搜索索引同步策略：同步 vs 异步

**选择：同步写入（注册/更新 Node 时立即同步到 MeiliSearch）**

- MeiliSearch 写入为异步任务队列，`add_documents` 返回 `taskUid` 后索引在后台更新（通常 < 100ms）
- 对 NodeVault 场景（Node 注册频率低，非高并发写），无需引入额外消息队列
- 若 MeiliSearch 不可用，Node 注册仍成功，仅搜索功能降级（容错处理：try/except + 日志告警）

### 3. 版本兼容性检查时机：注册时 vs 独立接口

**选择：注册新版本时自动运行兼容性检查**

- 在 `POST /api/v1/nodes/{id}/versions` 或现有 `PUT /api/v1/nodes/{id}` 中，当 `version` 字段变更时触发
- 检查结果以 warning 字段随响应返回，不阻塞注册（由调用方决定是否忽略）
- 破坏性变更建议 bump major 版本，兼容变更建议 bump minor

### 4. SDK 包结构：独立包 vs 嵌入 backend

**选择：`sdk/` 独立目录，可独立安装**

- 路径：`sdk/nodevault_sdk/`，含独立 `pyproject.toml`
- 与 `backend/` 完全解耦，不共享代码
- 安装方式：`pip install -e ./sdk`（本阶段），后续可发布 PyPI
- 同步客户端基于 `httpx.Client`；异步客户端基于 `httpx.AsyncClient`

### 5. 调用统计数据来源：复用 invocation_logs vs 新增统计表

**选择：聚合查询 `invocation_logs`**

- 现有表已有 `node_id`、`status`、`latency_ms`、`created_at` 字段，足以支撑统计
- 无需新增表和 Alembic 迁移
- 对于 P95/P99 延迟，使用 SQLAlchemy 的 `percentile_cont` 或应用层排序计算
- 若未来数据量大，可在此基础上加物化视图，不影响接口契约

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| MeiliSearch 服务不可用导致搜索接口 500 | 搜索层捕获连接异常，返回 503 + 明确错误消息；Node 注册/调用流程不依赖 MeiliSearch |
| Node 注册后搜索索引未及时更新（MeiliSearch 异步队列延迟） | 在文档中说明索引最终一致性，必要时提供 `POST /search/reindex` 管理接口 |
| SDK `@vault.node` 从函数签名自动推断 schema 不准确 | 装饰器支持手动传入 `input_schema`/`output_schema` 覆盖自动推断结果 |
| `invocation_logs` 数据量增大导致统计查询变慢 | 统计接口增加 `days` 参数限制查询范围（默认 30 天），并为 `node_id + created_at` 加索引 |
| Python SDK 版本与后端 API 版本不同步 | SDK 内嵌 `MIN_API_VERSION` 常量，连接时校验后端版本兼容性 |

## Migration Plan

1. 更新 `docker-compose.dev.yml` 添加 MeiliSearch 服务（port 7700）
2. 更新 `core/config.py` 新增 `MEILISEARCH_URL`、`MEILISEARCH_API_KEY`（可选）配置项
3. 创建 `core/search.py`，实现 `NodeSearchIndex` 并在应用启动时调用 `setup_index()`
4. 修改 `api/v1/nodes.py` 的创建/更新/删除接口，添加索引同步调用
5. 新增路由文件 `api/v1/search.py`、`api/v1/tags.py`、`api/v1/stats.py`，并挂载到 `router.py`
6. 创建 `core/versioning.py`，实现 `VersionCompatibilityChecker`
7. 创建 `sdk/` 目录，实现 SDK 包
8. 为 `invocation_logs.node_id + created_at` 添加复合索引（新增 Alembic 迁移）
9. 对现有已注册 Node 执行一次全量索引同步：`POST /api/v1/search/reindex`（管理员接口）

**回滚**：MeiliSearch 为只读附加层，关闭容器即可完全降级；SDK 不影响后端；核心数据模型无变更。

## Open Questions

- MeiliSearch 是否需要设置 API Key（生产环境鉴权）？当前 dev 环境暂不启用，配置项预留
- 统计接口的 P95/P99 是否在应用层计算（简单但有性能压力）还是用数据库函数（依赖 PostgreSQL）？建议优先应用层实现，若性能不足再切换
- SDK 是否需要支持 `api_key` 认证模式（Phase 3 API Key 功能）？当前仅实现 email/password 登录，`api_key` 参数预留接口但不实现
