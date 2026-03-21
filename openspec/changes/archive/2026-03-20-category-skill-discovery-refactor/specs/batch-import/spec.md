## ADDED Requirements

### Requirement: 批量注册节点
系统 SHALL 提供 `POST /api/v1/nodes/batch` 端点（需认证），接受符合 NodeSchema 标准的节点数组（最多 500 条），进行逐条验证后批量写入，返回成功/失败列表。

#### Scenario: 批量创建时使用 category_id
- **WHEN** 已认证用户提交节点数组
- **THEN** 每条节点 SHALL 使用 `category_id`（UUID，外键到 categories 表）替代原有的 `type` 字段；若 category_id 不存在于 categories 表则该条验证失败

#### Scenario: 批量创建时不再接受 skill_id 和 usage_hint
- **WHEN** 提交的节点数据包含 skill_id 或 usage_hint 字段
- **THEN** 系统 SHALL 忽略这些字段（不报错），因为节点与 Skill 的关联已移至 skill_nodes 多对多关系

### Requirement: 批量导入前检测重复 URL
系统 SHALL 在批量导入节点前检测 base_url 在当前 namespace 下是否已有节点注册（含相同路径模式的 endpoint），并返回重复信息供用户决策。

#### Scenario: 发现重复 URL
- **WHEN** 提交的 base_url 在目标 namespace 已注册过节点（根据 nodes.source_path 前缀匹配）
- **THEN** 系统 SHALL 返回 409，body 包含 `{"duplicate": true, "existing_session_id": "<UUID>", "existing_count": N, "message": "该服务已注册过 N 个节点，您可以选择迭代更新"}`
- **AND** 前端可选择强制导入（跳过重复）或切换到迭代模式

### Requirement: 迭代导入（更新已有节点）
当同一 base_url 再次被发现时，系统 SHALL 支持迭代模式，将探测到的 endpoint 与已有节点进行比对，返回 new / imported / updated / removed 状态。

#### Scenario: 调用迭代比对 API
- **WHEN** 用户对已有 base_url 发起 `POST /api/v1/discovery/sessions/{session_id}/compare`，body 包含 `{"previous_session_id": "<旧session_id>"}`
- **THEN** 系统 SHALL 返回端点比对结果数组，每条含 `{"path": "/xxx", "method": "GET", "status": "new|imported|updated|removed"}`
  - **new**: 仅在新探测中出现
  - **imported**: 两次完全一致
  - **updated**: path+method 相同但 schema 变化
  - **removed**: 仅在旧探测中出现

#### Scenario: 确认迭代导入
- **WHEN** 用户调用 `POST /api/v1/discovery/sessions/{session_id}/iterate`，body 含 `{"actions": [{"path":"/xxx","method":"GET","action":"import|skip|update"}]}`
- **THEN** 系统 SHALL 对 action=import 的 new 端点创建新 Node，对 action=update 的 updated 端点在已有 Node 上创建新 NodeVersion（保留旧版本），对 skip 和 removed 不做操作
- **AND** 返回执行报告 `{"imported": N, "updated": N, "skipped": N}`

#### Scenario: updated 端点创建新版本
- **WHEN** 某端点在迭代中 status=updated 且 action=update
- **THEN** 系统 SHALL 在已有 Node 上调用版本创建逻辑，input_schema/output_schema 更新为新探测值，version 号自增，旧 NodeVersion 保留为历史
