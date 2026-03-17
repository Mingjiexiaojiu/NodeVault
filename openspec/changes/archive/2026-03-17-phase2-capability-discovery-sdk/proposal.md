## Why

Phase 1 让 NodeVault 具备了基础的 Node 注册与调用能力，但开发者和 Agent 仍难以**快速发现所需能力**——缺乏全文搜索、缺乏语义检索入口，且每次与 NodeVault 交互都需要手写大量 HTTP 请求。Phase 2 通过引入全文搜索引擎（MeiliSearch）和 Python SDK，让"找到并使用正确的 Node"从繁琐变为一行代码。

## What Changes

- **全文搜索**：集成 MeiliSearch，支持关键词、标签、类型组合查询，以及搜索自动补全
- **版本管理增强**：版本兼容性检查器、版本回滚与弃用 API
- **标签管理**：热门标签查询、按标签浏览 Node 的 API
- **调用统计**：Node 调用量、成功率、延迟分布等统计接口
- **Python SDK（同步 + 异步）**：封装全部 API 交互，提供 `NodeVaultClient` 及 `@vault.node` 装饰器
- **API 文档增强**：完善 FastAPI OpenAPI 描述，所有接口添加 summary / response 示例

## Capabilities

### New Capabilities

- `node-search`: 基于 MeiliSearch 的 Node 全文搜索与自动补全接口
- `node-versioning`: Node 语义化版本兼容性检查、版本回滚与弃用接口
- `node-tags`: 标签管理接口（热门标签、按标签浏览）
- `node-stats`: Node 调用统计接口（成功率、延迟、调用趋势）
- `python-sdk`: NodeVault Python SDK（同步 client、异步 client、装饰器）

### Modified Capabilities

- `node-registry`: 新增 Node 注册时自动同步到 MeiliSearch 索引、更新时更新索引、删除时清除索引
- `node-invocation`: 调用完成后写入统计数据（调用量 +1、记录延迟）

## Impact

- **新依赖**：`meilisearch`（Python client）、`httpx`（SDK HTTP 层）
- **新服务**：MeiliSearch Docker 容器，需更新 `docker-compose.dev.yml`
- **后端新增文件**：`backend/core/search.py`、`backend/core/versioning.py`、`backend/api/v1/search.py`、`backend/api/v1/stats.py`、`backend/api/v1/tags.py`
- **新增 SDK 包**：`sdk/` 目录（`client.py`、`async_client.py`、`decorator.py`、`models.py`、`exceptions.py`）
- **配置变更**：`core/config.py` 新增 `meilisearch_url`、`meilisearch_api_key` 配置项
- **数据库**：Node 调用统计可写入已有 `InvocationLog` 表，无需新增迁移
