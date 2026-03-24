## Context

当前数据库存在 7 个不同级别的问题，已在 explore 阶段完成分析。本设计文档聚焦于其中影响最大的 **4 个可落地修复项**：

1. `user_ai_configs.api_key` 明文存储（🔴 安全）
2. `node_versions` / `skill_versions` 的 `is_default` 缺乏唯一约束（🟠 数据完整性）
3. `discovery_sessions.base_url` 默认空字符串（🟢 细节）
4. 两个较轻的结构性建议暂不修复（`users.department` 冗余、调用日志 version 无 FK），记录为 Non-Goals，在后续单独变更中处理

加密基础设施已就绪：`backend/core/credential_vault.py` 提供 AES-256-GCM 的 `encrypt_value` / `decrypt_value`，`service_credentials` 已在使用。本次直接复用，无需引入新依赖。

## Goals / Non-Goals

**Goals:**

- `user_ai_configs` 的 API Key 改为与 `service_credentials` 相同的加密存储方案
- 存量数据通过 Alembic 迁移脚本一次性加密转换，不丢失数据
- `node_versions` 和 `skill_versions` 各自增加 Partial Unique Index，数据库层强制单一默认版本
- `discovery_sessions.base_url` 默认值改为 NULL，统一空值语义

**Non-Goals:**

- 不处理 `users.department` 与 namespace 的语义重叠（需要产品层面决策）
- 不处理 `node_invocation_logs.version` 改为 FK（涉及日志保留策略讨论）
- 不处理两套角色系统统一（需要权限系统专项变更）
- 不修改前端 UI 逻辑

## Decisions

### Decision 1：API Key 加密 — 复用 credential_vault，不另起炉灶

**选择**：直接调用 `credential_vault.encrypt_value()` / `decrypt_value()`。

**放弃的方案**：
- 用 PostgreSQL `pgcrypto` 扩展在数据库层加密 → 密钥管理复杂，且已有应用层方案
- 单独写一套加密工具 → 重复代码，密钥来源不统一

**字段变更**：

```
旧：api_key TEXT NOT NULL
新：api_key_encrypted BYTEA NOT NULL
    api_key_nonce      BYTEA NOT NULL
```

**读写时机**：
- **写入**（创建/更新）：在 API 层收到明文 api_key → `encrypt_value()` → 存 bytea
- **读取**（调用 AI）：从 DB 取 bytea → `decrypt_value()` → 传给 LLM client
- **API 响应**：永远不返回明文，返回 `"api_key_masked": "sk-...****"` 格式的脱敏串

### Decision 2：is_default 唯一性 — Partial Unique Index（不用应用锁）

**选择**：数据库层 Partial Unique Index。

```sql
-- node_versions
CREATE UNIQUE INDEX uq_node_default_version
  ON node_versions (node_id)
  WHERE is_default = true;

-- skill_versions  
CREATE UNIQUE INDEX uq_skill_default_version
  ON skill_versions (skill_id)
  WHERE is_default = true;
```

**放弃的方案**：
- 应用层事务加 SELECT FOR UPDATE → 仍有竞态，且每次设默认版本都要额外查询
- 触发器 → 可移植性差，调试复杂

**迁移时的数据处理**：如存量数据已有多个 `is_default = true`，迁移脚本先修复（保留最新的，其余置 false），再建索引，避免建索引时报错。

### Decision 3：base_url 默认值 — 改为 NULL，保持可选语义

```sql
ALTER TABLE discovery_sessions
  ALTER COLUMN base_url DROP DEFAULT,
  ALTER COLUMN base_url DROP NOT NULL;
```

应用层凡是判断 `base_url` 有效性的地方，统一改为 `if base_url is not None and base_url`，消除空串判断分支。

### Decision 4：迁移策略 — 单次 Alembic migration，数据迁移内嵌

将所有变更合并为一个 Alembic revision（`db_integrity_security_fixes`），按以下顺序执行：

```
1. discovery_sessions.base_url: DROP DEFAULT → ALTER NULLABLE
2. 修复存量 is_default 重复数据（node_versions + skill_versions）
3. CREATE UNIQUE INDEX ... WHERE is_default = true（两张表）
4. user_ai_configs: ADD api_key_encrypted + api_key_nonce
5. 数据转换：SELECT id, api_key → encrypt → UPDATE encrypted fields
6. DROP COLUMN api_key
```

**回滚方案**（downgrade）：逆序操作，解密数据恢复明文字段。需要在 migration 中实现完整的 downgrade 函数。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 迁移时 `CREDENTIAL_ENCRYPT_KEY` 未配置导致加密失败 | migration 脚本开头检查环境变量，不存在则 raise 并中止 |
| 存量 `is_default` 重复数据修复策略不当导致错误版本被保留 | 保留 `created_at` 最大（最新）的那条，其余置 false，并在 migration 日志中打印受影响的记录 |
| `base_url` 改 NULL 后现有查询未适配 | 全局 grep `discovery_sessions` 和 `base_url` 相关代码，逐一检查 |
| migration 执行中途失败（数据加密转换阶段） | PostgreSQL 事务保证原子性，失败自动回滚；上线前在 staging 环境先跑一遍 |

## Migration Plan

1. **staging 验证**：在测试环境执行 migration，检查加密后数据可正常解密
2. **备份**：`pg_dump` 备份 `user_ai_configs` 表
3. **执行**：`alembic upgrade head`
4. **验证**：跑 `backend/tests/test_credential_vault.py` 和 AI 配置相关测试
5. **回滚预案**：如有问题执行 `alembic downgrade -1`

## Open Questions

- `user_ai_configs` 的 `api_key_masked` 脱敏格式：显示前几位？（建议前4后4，中间用 `****`）
- 是否需要同步修复 `users.department` 冗余问题？（建议单独 change，不在本次处理）
