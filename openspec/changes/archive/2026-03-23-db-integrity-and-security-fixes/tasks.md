## 1. 数据库迁移

- [x] 1.1 新建 Alembic revision `db_integrity_security_fixes`，添加所有 DDL 变更的 upgrade/downgrade 函数骨架
- [x] 1.2 在 upgrade 中添加：`discovery_sessions.base_url` DROP DEFAULT，ALTER COLUMN 改为可空
- [x] 1.3 在 upgrade 中添加：修复存量 `node_versions` 重复 `is_default=true` 数据（保留最新，其余置 false）
- [x] 1.4 在 upgrade 中添加：修复存量 `skill_versions` 重复 `is_default=true` 数据（同上）
- [x] 1.5 在 upgrade 中添加：CREATE UNIQUE INDEX `uq_node_default_version` ON node_versions(node_id) WHERE is_default=true
- [x] 1.6 在 upgrade 中添加：CREATE UNIQUE INDEX `uq_skill_default_version` ON skill_versions(skill_id) WHERE is_default=true
- [x] 1.7 在 upgrade 中添加：user_ai_configs ADD COLUMN `api_key_encrypted BYTEA`、`api_key_nonce BYTEA`
- [x] 1.8 在 upgrade 数据迁移段：检查 `CREDENTIAL_ENCRYPT_KEY` 环境变量，未设置则 raise 中止
- [x] 1.9 在 upgrade 数据迁移段：SELECT id + api_key → encrypt → UPDATE api_key_encrypted + api_key_nonce
- [x] 1.10 在 upgrade 中添加：DROP COLUMN `api_key`（在数据转换完成后）
- [x] 1.11 编写对应的 downgrade 函数（逆序：ADD api_key → decrypt → DROP 加密字段，DROP 索引）
- [ ] 1.12 在 staging 环境执行 `alembic upgrade head`，验证无报错

## 2. ORM 模型更新

- [x] 2.1 修改 `backend/models/ai_config.py`：删除 `api_key: Text` 字段，新增 `api_key_encrypted: LargeBinary` 和 `api_key_nonce: LargeBinary`

## 3. Schema 更新

- [x] 3.1 修改 `backend/schemas/ai_config.py`：`AIConfigCreate` 和 `AIConfigUpdate` 保留 `api_key: str` 入参字段（前端仍传明文）
- [x] 3.2 修改 `backend/schemas/ai_config.py`：`AIConfigResponse` 删除 `api_key` 字段，新增 `api_key_masked: str` 字段（格式：前4位+`****`+后4位）

## 4. API 层加解密逻辑

- [x] 4.1 找到 AI 配置的创建接口，写入前调用 `credential_vault.encrypt_value(api_key)` 获得 `(ciphertext, nonce)`，存入对应字段
- [x] 4.2 找到 AI 配置的更新接口，同上，用新 nonce 重新加密
- [x] 4.3 找到 AI 配置的查询接口，构造 `api_key_masked`：先解密得明文，再生成脱敏串返回（或直接用 `key_prefix` 若有缓存）
- [x] 4.4 找到调用 LLM 的业务逻辑（skill_md_generator 等），从 DB 读取后调用 `credential_vault.decrypt_value()` 获得明文传给 LLM client
- [x] 4.5 全局 grep `discovery_sessions` + `base_url`，确认所有 `if base_url` 已正确处理 None（无需修改）

## 5. 应用层 is_default 事务保护

- [x] 5.1 确认 `nodes.py:set_default_version()` 和 `skill_registry.py:create_version()` 已采用先清再设的事务模式
- [x] 5.2 在 `nodes.py:set_default_version()` 和 `skills.py:create_version()` 的异常处理中捕获 `IntegrityError`，返回 HTTP 409

## 6. 测试

- [x] 6.1 新增 `TestAIConfigEncryption`：创建/更新/列表时验证响应含 `api_key_masked`，无明文泄漏
- [x] 6.2 新增测试：`api_key_masked` 格式验证（前4位 + **** + 后4位）
- [x] 6.3 新增 `TestIsDefaultUnique`：set_default_version 后同 node 仅有 1 个默认版本
- [x] 6.4 新增 `TestDiscoveryBaseUrlNullable`：discovery session 创建时 base_url 可为 NULL
- [ ] 6.5 运行全量测试套件，确认无回归：`pytest backend/tests/ -x`
