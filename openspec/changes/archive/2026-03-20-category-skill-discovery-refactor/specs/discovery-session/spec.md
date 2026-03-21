## ADDED Requirements

### Requirement: 迭代发现支持（同一 base_url 多次探测）
系统 SHALL 支持同一 base_url 的多次探测（迭代），每次探测创建新的 DiscoverySession，并可与历史 Session 进行端点比对。

#### Scenario: 创建迭代 Session
- **WHEN** 用户对一个已有 Session 的 base_url 再次发起探测
- **THEN** 系统 SHALL 创建新的 DiscoverySession，base_url 相同，session_id 不同；旧 Session 保留不变

#### Scenario: 查询同一 base_url 的历史 Sessions
- **WHEN** 调用 `GET /api/v1/discovery/sessions?base_url={url}`
- **THEN** 系统 SHALL 返回该 base_url 对应的所有 DiscoverySession，按 created_at 倒序排列

### Requirement: 端点比对 API
系统 SHALL 提供 `POST /api/v1/discovery/sessions/{session_id}/compare` 端点，接受 `{"previous_session_id": "<UUID>"}` body，比较两次探测的 endpoint 差异。

#### Scenario: 比对返回差异列表
- **WHEN** 调用 compare 接口，提供新旧两个 session_id
- **THEN** 系统 SHALL 以 path+method 作为唯一标识进行匹配，返回数组：
  ```json
  [
    {"path": "/users", "method": "GET", "status": "imported", "changes": null},
    {"path": "/users", "method": "POST", "status": "updated", "changes": {"input_schema": "changed"}},
    {"path": "/orders", "method": "GET", "status": "new", "changes": null},
    {"path": "/legacy", "method": "DELETE", "status": "removed", "changes": null}
  ]
  ```
  - **new**: 仅在新 Session 中出现
  - **imported**: 两次完全一致（path+method+schema 均相同），且已有对应 Node
  - **updated**: path+method 相同但 input_schema 或 output_schema 发生变化
  - **removed**: 仅在旧 Session 中出现

#### Scenario: previous_session_id 不存在
- **WHEN** 提供的 previous_session_id 不存在
- **THEN** 系统 SHALL 返回 404，message 为"历史发现会话不存在"

#### Scenario: 两个 Session 的 base_url 不一致
- **WHEN** 新旧 Session 的 base_url 不同
- **THEN** 系统 SHALL 返回 422，message 为"比对的两个会话必须属于同一服务（base_url 一致）"

### Requirement: 迭代导入执行 API
系统 SHALL 提供 `POST /api/v1/discovery/sessions/{session_id}/iterate` 端点，根据用户选择的 actions 执行创建/更新/跳过操作。

#### Scenario: 执行迭代导入
- **WHEN** 调用 iterate 接口，body 含 actions 数组
- **THEN** 系统 SHALL 按 action 执行：
  - `import`（针对 new）：创建新 Node，关联当前 DiscoverySession
  - `update`（针对 updated）：在已有 Node 上创建新 NodeVersion，更新 input_schema/output_schema
  - `skip`：不操作
- **AND** 返回执行报告 `{"imported": N, "updated": N, "skipped": N}`

#### Scenario: 无效的 action 组合
- **WHEN** action=import 但 status 不是 new，或 action=update 但 status 不是 updated
- **THEN** 系统 SHALL 返回 422，指出哪些条目的 action 与 status 不匹配
