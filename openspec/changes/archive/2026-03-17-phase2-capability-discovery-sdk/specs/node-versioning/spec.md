## ADDED Requirements

### Requirement: 版本兼容性检查
系统 SHALL 在发布新 Node 版本时自动运行兼容性检查，对比新旧版本的 input_schema 和 output_schema，识别破坏性变更。检查结果以 `compatibility` 字段随 `POST /api/v1/nodes/{node_id}/versions` 响应返回，不阻断发布操作。

#### Scenario: 新增必填字段为破坏性变更
- **WHEN** 新版本 input_schema 新增了 required 中的字段，且旧版本中该字段不存在
- **THEN** 系统 SHALL 在响应 `compatibility.breaking_changes` 中列出该字段，并建议版本号 bump 至下一个 major

#### Scenario: 删除已有字段为破坏性变更
- **WHEN** 新版本 output_schema 删除了旧版本中已有的字段
- **THEN** 系统 SHALL 在响应 `compatibility.breaking_changes` 中说明删除了哪些字段

#### Scenario: 新增可选字段为兼容变更
- **WHEN** 新版本 input_schema 新增字段，但该字段不在 required 列表中
- **THEN** 系统 SHALL 在响应 `compatibility.warnings` 中记录为提示信息，breaking_changes 为空，建议 bump minor

#### Scenario: 发布第一个版本时跳过检查
- **WHEN** Node 当前没有任何版本（首次发布）
- **THEN** 系统 SHALL 跳过兼容性检查，直接创建版本，compatibility 字段返回 `{"checked": false}`

---

### Requirement: 版本建议号计算
系统 SHALL 提供版本号建议能力：根据当前版本号和兼容性检查结果，按语义化版本规范（SemVer）自动计算建议的下一个版本号，并在兼容性检查响应中以 `compatibility.suggested_version` 返回。

#### Scenario: 破坏性变更建议升 major
- **WHEN** 兼容性检查发现破坏性变更，当前版本为 1.2.3
- **THEN** 系统 SHALL 返回建议版本 `2.0.0`

#### Scenario: 向后兼容新功能建议升 minor
- **WHEN** 兼容性检查无破坏性变更但有新增字段，当前版本为 1.2.3
- **THEN** 系统 SHALL 返回建议版本 `1.3.0`

#### Scenario: 仅修复建议升 patch
- **WHEN** 兼容性检查无任何变更（schema 相同），当前版本为 1.2.3
- **THEN** 系统 SHALL 返回建议版本 `1.2.4`

---

### Requirement: 版本回滚
系统 SHALL 提供 `POST /api/v1/nodes/{node_id}/versions/{version}/set-default` 端点（需认证，仅 Node 所有者），将指定版本设为该 Node 的默认版本，同时清除当前默认版本的 `is_default` 标记。

#### Scenario: 回滚到旧版本成功
- **WHEN** Node 所有者将 v1.0.0 设为默认版本（当前默认为 v1.2.0）
- **THEN** 系统 SHALL 返回 200，v1.0.0 的 `is_default` 变为 true，v1.2.0 的 `is_default` 变为 false

#### Scenario: 指定版本不存在
- **WHEN** 请求设置一个该 Node 下不存在的版本号为默认
- **THEN** 系统 SHALL 返回 404

#### Scenario: 非 Node 所有者操作
- **WHEN** 非 Node 所有者尝试回滚版本
- **THEN** 系统 SHALL 返回 403

---

### Requirement: 版本弃用
系统 SHALL 提供 `POST /api/v1/nodes/{node_id}/versions/{version}/deprecate` 端点（需认证，仅 Node 所有者），将指定版本标记为 deprecated。已弃用版本仍可调用，但在版本列表中 SHALL 显示 deprecated 状态，且调用时响应头 SHALL 包含弃用警告。

#### Scenario: 弃用版本成功
- **WHEN** Node 所有者调用 deprecate 接口
- **THEN** 系统 SHALL 返回 200，该版本 status 变为 deprecated

#### Scenario: 调用已弃用版本时返回警告
- **WHEN** 调用者指定调用一个 deprecated 版本的 Node
- **THEN** 系统 SHALL 正常执行调用并返回结果，且响应头包含 `X-NodeVault-Deprecation-Warning: This version is deprecated`

#### Scenario: 不允许弃用当前默认版本
- **WHEN** 尝试弃用当前 `is_default=true` 的版本
- **THEN** 系统 SHALL 返回 400，提示需先将另一版本设为默认

---

### Requirement: 版本变更记录查询
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}/changelog` 端点（需认证），返回该 Node 所有版本的发布记录，包含版本号、发布时间、兼容性状态、changelog 描述（来自发布时的 `release_notes` 字段）。

#### Scenario: 查询版本变更记录
- **WHEN** 调用 GET /api/v1/nodes/{node_id}/changelog
- **THEN** 系统 SHALL 返回按版本号倒序排列的版本记录列表，每条含 version/created_at/is_default/status/release_notes
