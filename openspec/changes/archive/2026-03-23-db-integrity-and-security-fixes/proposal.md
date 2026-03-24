## Why

数据库存在多个安全性和数据完整性问题：`user_ai_configs` 明文存储用户 API Key（与 `service_credentials` 的加密方案不一致）；`is_default` 字段缺乏唯一约束导致并发写入可能产生多个默认版本；`base_url` 使用空字符串作为默认值增加了空值判断复杂度。这些问题随着用户量和并发量增加将造成实质性风险，应尽早修复。

## What Changes

- **BREAKING** `user_ai_configs.api_key` 字段从明文 `text` 改为加密存储，新增 `api_key_encrypted (bytea)` 和 `api_key_nonce (bytea)`，删除原 `api_key` 字段
- `node_versions` 表新增 Partial Unique Index，保证每个 node 只能有一个 `is_default = true` 的版本
- `skill_versions` 表新增 Partial Unique Index，保证每个 skill 只能有一个 `is_default = true` 的版本
- `discovery_sessions.base_url` 默认值从空字符串 `''` 改为 `NULL`，字段改为可空
- 对应的后端加解密逻辑、Schema、API 接口同步更新

## Capabilities

### New Capabilities

- `ai-config-encryption`: 用户 AI 配置中 API Key 的加密存储与读取能力，与 `service_credentials` 复用同一套加密工具

### Modified Capabilities

- 无（本次变更为实现层修复，不涉及对外行为规格变更）

## Impact

- **数据库迁移**：需要 Alembic migration，涉及 `user_ai_configs` 表结构变更和两张表的索引新增
- **后端**：`backend/models/ai_config.py`、`backend/schemas/ai_config.py`、`backend/api/v1/` 中 AI 配置相关接口、`backend/core/credential_vault.py`（复用加解密）
- **现有数据**：`user_ai_configs` 中已有的明文 `api_key` 数据需要在迁移脚本中一次性加密转换
- **前端**：AI 配置页面的读写逻辑无感知变化（API 响应保持脱敏展示）
