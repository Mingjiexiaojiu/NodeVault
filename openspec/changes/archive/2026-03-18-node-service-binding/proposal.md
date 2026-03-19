## Why

服务发现导入功能（`service-discovery-import`）已完成，用户可以从 OpenAPI 服务批量导入节点。但导入的节点与来源服务之间没有显式关联——`credential_id` 只存在于 `runtime_config` JSONB 字段中，无法在模型层面追溯节点来源。这导致无法按服务查看节点、批量管理某服务下的全部节点、以及再次探测时识别已导入的接口。

## What Changes

- Node 模型新增两个可选字段：`source_credential_id`（FK → service_credentials）和 `source_path`（记录原始 OpenAPI 路径）
- 创建 Alembic 迁移，回填已有导入节点的来源信息
- 批量导入 API 写入来源字段
- 节点列表/详情 API 返回来源信息
- 探测引擎支持与已导入节点做 diff（标识哪些路径已导入、哪些是新增）
- 前端服务发现页面展示 diff 状态（已导入标绿、新增可选）
- 前端节点详情展示来源服务信息

## Capabilities

### New Capabilities
- `node-service-binding`: Node 与 ServiceCredential 之间的轻量来源绑定，包括数据模型、API 返回、按服务筛选节点

### Modified Capabilities
- `node-registry`: 批量注册接口需写入 `source_credential_id` 和 `source_path`

## Impact

- **数据库**: `nodes` 表新增 2 列 + 外键 + 索引，需 Alembic 迁移
- **后端 API**: `NodeResponse` schema 新增可选来源字段；节点列表支持按 `source_credential_id` 过滤
- **前端**: 服务发现页面增加 diff 展示逻辑；节点详情页展示来源信息
- **不涉及破坏性变更**: 新字段均为 nullable，现有 API 完全兼容
