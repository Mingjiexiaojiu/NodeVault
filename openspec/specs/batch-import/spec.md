## ADDED Requirements

### Requirement: Parse OpenAPI operations into Node drafts
The system SHALL parse an OpenAPI document and generate a list of Node draft objects, each representing one API operation.

#### Scenario: Map operation to Node draft
- **WHEN** an OpenAPI document contains `POST /translate` with operationId `translateText`, summary, requestBody schema, and response schema
- **THEN** system SHALL generate a draft with suggested name derived from operationId, display_name from summary, input_schema from requestBody, output_schema from 200 response, endpoint as relative path, and method as POST

#### Scenario: Operation without operationId
- **WHEN** an operation has no operationId
- **THEN** system SHALL generate a suggested name from `{method}_{path}` in snake_case (e.g., `post_translate`)

### Requirement: Filter noise endpoints
The system SHALL identify and default-exclude health check, metrics, and documentation endpoints from the draft list.

#### Scenario: Health endpoint filtered
- **WHEN** the OpenAPI document includes `GET /health` and `GET /metrics`
- **THEN** these operations SHALL appear in the draft list but with `selected: false` by default

#### Scenario: User can override filter
- **WHEN** a filtered endpoint is shown as unchecked in the preview
- **THEN** user SHALL be able to manually check it for inclusion

### Requirement: User customizes Node names
The system SHALL present suggested Node names but allow users to override each name before import.

#### Scenario: Custom name provided
- **WHEN** user changes the suggested name `translate_text` to `鏅鸿兘缈昏瘧`
- **THEN** the created Node SHALL use `鏅鸿兘缈昏瘧` as its display_name, and the system SHALL generate a valid snake_case `name` field

### Requirement: Batch create Nodes
The system SHALL create all selected Node drafts in a single batch operation, with an optional `session_id` to link Nodes to a discovery session.

#### Scenario: Import 4 out of 5 discovered operations
- **WHEN** user selects 4 of 5 discovered operations and confirms import
- **THEN** system SHALL create 4 Nodes, each with runtime_config containing the relative endpoint path and the shared credential_id; each Node SHALL have version `1.0.0`

#### Scenario: Import with session_id
- **WHEN** user confirms import with 4 selected operations and a `session_id` is present
- **THEN** system SHALL create 4 Nodes with `discovery_session_id` set to the given session's ID, and update the session's `imported_count` and `status` to `"completed"`

#### Scenario: Import without session_id (backward compatible)
- **WHEN** batch import is called without a `session_id`
- **THEN** system SHALL create Nodes with `discovery_session_id = NULL`, maintaining full backward compatibility

#### Scenario: Name conflict during import
- **WHEN** a generated Node name conflicts with an existing Node in the same namespace
- **THEN** system SHALL report the conflict and require user to change the name before proceeding

### Requirement: Support spec file upload
The system SHALL accept uploaded OpenAPI spec files (JSON and YAML) as an alternative to URL probing.

#### Scenario: Upload JSON spec file
- **WHEN** user uploads a valid OpenAPI 3.x JSON file and provides a base_url
- **THEN** system SHALL parse it and present the same Node draft preview as URL-based discovery

#### Scenario: Upload YAML spec file
- **WHEN** user uploads a valid OpenAPI YAML file
- **THEN** system SHALL parse it identically to JSON format

#### Scenario: Invalid spec file
- **WHEN** user uploads a file that is not valid OpenAPI
- **THEN** system SHALL return an error indicating the file could not be parsed as OpenAPI 2.x or 3.x

### Requirement: Record import source metadata
The system SHALL record the discovery source on each imported Node for traceability.

#### Scenario: Node metadata after import
- **WHEN** a Node is created via batch import from `https://api.example.com` discovered at `/openapi.json`
- **THEN** the Node's metadata SHALL include `source_url`, `spec_path`, and `discovered_at` fields

### Requirement: Shared configuration for batch import
The system SHALL allow users to set common fields (category, tags, visibility) that apply to all Nodes in the import batch.

#### Scenario: Set shared category and tags
- **WHEN** user sets category to "NLP" and tags to ["缈昏瘧", "澶氳瑷�"] before importing
- **THEN** all imported Nodes SHALL have category "NLP" and tags ["缈昏瘧", "澶氳瑷�"]


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

#### Scenario: 确认迭代导入
- **WHEN** 用户调用 `POST /api/v1/discovery/sessions/{session_id}/iterate`，body 含 actions 数组
- **THEN** 系统 SHALL 对 action=import 的 new 端点创建新 Node，对 action=update 的 updated 端点在已有 Node 上创建新 NodeVersion，返回执行报告 `{"imported": N, "updated": N, "skipped": N}`

#### Scenario: updated 端点创建新版本
- **WHEN** 某端点在迭代中 status=updated 且 action=update
- **THEN** 系统 SHALL 在已有 Node 上调用版本创建逻辑，input_schema/output_schema 更新为新探测值，version 号自增，旧 NodeVersion 保留为历史
