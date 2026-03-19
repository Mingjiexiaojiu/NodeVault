## 1. 数据库迁移

- [x] 1.1 在 `backend/models/node.py` 的 `Node` 模型新增 `source_credential_id`（UUID, FK → service_credentials.id, ON DELETE SET NULL, nullable, index）和 `source_path`（String(512), nullable）字段
- [x] 1.2 在 `Node` 模型添加 `source_credential` relationship（lazy="joined"）
- [x] 1.3 创建 Alembic 迁移：新增两列 + 外键 + 索引
- [x] 1.4 编写回填迁移：从 `node_versions.runtime_config->>'credential_id'` 回填 `nodes.source_credential_id`，从 `node_versions.runtime_config->>'endpoint'` 提取路径回填 `source_path`
- [x] 1.5 运行迁移并验证

## 2. 后端 Schema 更新

- [x] 2.1 在 `backend/schemas/node.py` 的 `NodeResponse` 添加可选字段：`source_credential_id`、`source_path`、`source_service_name`
- [x] 2.2 `source_service_name` 通过 `source_credential` relationship 从 `ServiceCredential.name` 获取

## 3. 节点列表过滤

- [x] 3.1 在 `GET /api/v1/nodes` 添加可选查询参数 `source_credential_id: UUID`
- [x] 3.2 在 `backend/core/registry.py` 的 `list_nodes` 方法中实现按 `source_credential_id` 过滤
- [x] 3.3 编写过滤测试

## 4. 批量导入写入来源

- [x] 4.1 修改 `backend/core/registry.py` 的 `batch_register` 方法，接受 `source_path_map: dict[str, str]`（name → path 映射），写入 `source_credential_id` 和 `source_path`
- [x] 4.2 修改 `backend/api/v1/discovery.py` 的批量导入接口，传入来源信息
- [x] 4.3 修改 `backend/schemas/discovery.py` 的 `BatchImportItem` 添加 `source_path` 字段
- [x] 4.4 编写批量导入来源字段测试

## 5. 已导入路径查询 API

- [x] 5.1 在 `backend/api/v1/discovery.py` 新增 `GET /api/v1/discovery/imported?credential_id=<uuid>` 端点，返回 `[{node_id, source_path, name}]`
- [x] 5.2 编写已导入路径查询测试

## 6. 前端 API 层

- [x] 6.1 在 `frontend/src/api/discovery.ts` 添加 `getImportedPaths(credentialId)` 函数
- [x] 6.2 更新 `BatchImportItem` 类型定义添加 `source_path`

## 7. 前端服务发现页面 diff

- [x] 7.1 在 `ServiceDiscoveryView.vue` Step 2（预览）增加 diff 逻辑：探测完成后如有凭证，请求已导入路径
- [x] 7.2 对探测结果做 diff 标记：已导入（标绿、禁用勾选）、新增（可勾选）
- [x] 7.3 导入时将 `source_path` 传入批量导入请求

## 8. 前端节点详情来源展示

- [x] 8.1 在 `NodeDetailView.vue` 展示来源信息区块（来源服务名 + 原始路径），仅在 `source_credential_id` 非空时显示
