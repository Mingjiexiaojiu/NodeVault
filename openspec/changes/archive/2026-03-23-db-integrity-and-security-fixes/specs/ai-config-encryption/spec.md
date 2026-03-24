## ADDED Requirements

### Requirement: AI 配置的 API Key 加密存储
系统 SHALL 使用 AES-256-GCM 对 `user_ai_configs` 中的 `api_key` 进行加密后存储，密文和 nonce 分别保存在 `api_key_encrypted` 和 `api_key_nonce` 字段，不得以明文形式持久化。

#### Scenario: 创建 AI 配置时加密存储
- **WHEN** 用户提交包含 `api_key` 的 AI 配置创建请求
- **THEN** 系统 SHALL 调用 `credential_vault.encrypt_value(api_key)` 得到 `(ciphertext, nonce)`，将其存入 `api_key_encrypted` 和 `api_key_nonce`，数据库中不存在明文 `api_key` 字段

#### Scenario: 更新 AI 配置时重新加密
- **WHEN** 用户提交包含新 `api_key` 的 AI 配置更新请求
- **THEN** 系统 SHALL 以新的随机 nonce 重新加密，覆盖原有密文和 nonce

#### Scenario: API 响应不返回明文 API Key
- **WHEN** 任意客户端请求 AI 配置详情或列表
- **THEN** 系统 SHALL 在响应中仅返回 `api_key_masked` 字段（格式：前4位明文 + `****` + 后4位明文），不得返回完整明文

#### Scenario: 调用 LLM 时解密使用
- **WHEN** 系统需要使用某条 AI 配置调用 LLM 服务（如生成 Skill.md）
- **THEN** 系统 SHALL 调用 `credential_vault.decrypt_value(api_key_encrypted, api_key_nonce)` 获得明文，仅在内存中使用，不持久化

#### Scenario: 加密密钥未配置时拒绝操作
- **WHEN** 环境变量 `CREDENTIAL_ENCRYPT_KEY` 未设置，且有创建/更新 AI 配置的请求
- **THEN** 系统 SHALL 返回 500 错误，提示密钥未配置，不存储任何数据

### Requirement: is_default 版本唯一性约束
系统 SHALL 通过数据库 Partial Unique Index 保证每个 node 最多只有一个 `is_default = true` 的版本，每个 skill 最多只有一个 `is_default = true` 的版本。

#### Scenario: 设置新默认版本时旧默认自动取消
- **WHEN** 应用层将某个版本的 `is_default` 设为 `true`
- **THEN** 应用层 SHALL 在同一事务中先将该 node/skill 的其他版本 `is_default` 置为 `false`，再写入新值，以满足唯一索引约束

#### Scenario: 并发设置默认版本时数据库拒绝违规写入
- **WHEN** 两个并发请求同时尝试将同一 node 的不同版本设为默认
- **THEN** 数据库 SHALL 通过唯一索引让其中一个事务失败，应用层 SHALL 捕获并返回 409 冲突错误

### Requirement: discovery_sessions.base_url 可为空
`discovery_sessions.base_url` 字段 SHALL 允许 NULL 值，系统不得使用空字符串 `''` 作为"无值"语义；所有读取该字段的代码 SHALL 统一使用 `is not None` 判断有效性。

#### Scenario: 手动导入 spec 时 base_url 可为空
- **WHEN** 用户通过 `source='manual'` 方式直接提供 spec_url 而不提供 base_url
- **THEN** 系统 SHALL 允许 `base_url` 为 NULL，不报验证错误

#### Scenario: 读取 base_url 时统一判空
- **WHEN** 任意代码读取 `discovery_session.base_url`
- **THEN** 该代码 SHALL 仅使用 `if base_url is not None` 判断，不使用 `if base_url` 或 `if base_url != ''`
