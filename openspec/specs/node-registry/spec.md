## ADDED Requirements

### Requirement: 注册 Node
系统 SHALL 提供 `POST /api/v1/nodes` 端点（需认证），接受 `NodeCreate` 请求体，在调用者的默认 Namespace 下创建 Node 记录和 v1.0.0 NodeVersion 记录。Node `name` 在同一 Namespace 内 SHALL 唯一。请求体 SHALL 支持可选字段 `skill_id`（UUID）和 `usage_hint`（字符串，最长 500 字符）。

#### Scenario: 注册 Node 成功
- **WHEN** 已认证用户提供合法的 NodeCreate 请求体（name/type/input_schema/output_schema/runtime 均有效）
- **THEN** 系统 SHALL 创建 Node 和 NodeVersion 记录，返回 201 和 NodeResponse（含 id/name/type/status/版本号/skill_id/usage_hint）

#### Scenario: 同命名空间内 name 重复
- **WHEN** 同一用户尝试注册与已有 Node 同名的新 Node
- **THEN** 系统 SHALL 返回 409，提示名称在该命名空间已存在

#### Scenario: 字段校验复用 NodeSchemaBase 规则
- **WHEN** 提供不符合 snake_case 的 name 或不符合 SemVer 的 version
- **THEN** 系统 SHALL 返回 422 并说明具体字段的校验错误

#### Scenario: skill_id 不存在时注册失败
- **WHEN** 提供的 skill_id 在数据库中不存在
- **THEN** 系统 SHALL 返回 422，提示"指定的技能集不存在"

### Requirement: Node 支持 usage_hint 字段
Node 记录 SHALL 包含可选字段 `usage_hint`（字符串，最长 500 字符），描述该节点的适用场景，供 LLM 生成 SKILL.md 时使用。`PATCH /api/v1/nodes/{node_id}` SHALL 支持更新 usage_hint，更新后 SHALL 触发所属 Skill 的 is_stale 置为 true。

#### Scenario: 更新 usage_hint 成功
- **WHEN** Node 所有者 PATCH 更新 usage_hint
- **THEN** 系统 SHALL 返回 200，NodeResponse 含更新后的 usage_hint，且所属 Skill 的 is_stale 被置为 true

#### Scenario: usage_hint 超长被拒绝
- **WHEN** 提供的 usage_hint 超过 500 字符
- **THEN** 系统 SHALL 返回 422

### Requirement: Node 支持 skill_id 字段
Node 记录 SHALL 包含可选字段 `skill_id`（UUID 外键，指向 skills 表），`PATCH /api/v1/nodes/{node_id}` SHALL 支持更新 skill_id（含置 null），变更 skill_id SHALL 触发新旧两个 Skill 的 is_stale 置为 true。

#### Scenario: 变更 skill_id 触发双侧 is_stale
- **WHEN** 节点从 Skill A 移动到 Skill B（更新 skill_id）
- **THEN** 系统 SHALL 将 Skill A 和 Skill B 的 is_stale 均置为 true

---

### Requirement: 查询 Node 列表
系统 SHALL 提供 `GET /api/v1/nodes` 端点（需认证），返回当前用户有权访问的 Node 列表，支持按 `type`、`status`、`tag`、`source_credential_id` 过滤，支持 `page` / `page_size` 分页（默认 page=1，page_size=20，最大 100）。

#### Scenario: 无过滤条件查询
- **WHEN** 不携带任何查询参数调用 GET /api/v1/nodes
- **THEN** 系统 SHALL 返回 200 和当前用户命名空间内的 Node 列表（已归档节点默认不返回）

#### Scenario: 按 type 过滤
- **WHEN** 携带 `?type=nlp` 查询参数
- **THEN** 系统 SHALL 只返回 type 为 nlp 的 Node

#### Scenario: 按 tag 过滤
- **WHEN** 携带 `?tag=data` 查询参数
- **THEN** 系统 SHALL 只返回关联该 tag 的 Node

#### Scenario: 按 source_credential_id 过滤
- **WHEN** 携带 `?source_credential_id=<uuid>` 查询参数
- **THEN** 系统 SHALL 只返回来自该凭证的 Node

#### Scenario: 分页
- **WHEN** 携带 `?page=2&page_size=5`
- **THEN** 系统 SHALL 返回第 6-10 条记录

---

### Requirement: 获取 Node 详情
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}` 端点（需认证），返回指定 Node 的完整信息，包含当前默认版本的 input_schema/output_schema/runtime_config。

#### Scenario: 获取存在的 Node
- **WHEN** 使用有效的 node_id 调用 GET /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 200 和包含该 Node 完整信息与默认版本详情的 NodeDetailResponse

#### Scenario: Node 不存在
- **WHEN** 使用不存在的 node_id
- **THEN** 系统 SHALL 返回 404

---

### Requirement: Node 注册时同步搜索索引
系统 SHALL 在 `POST /api/v1/nodes` 成功创建 Node 后，自动将该 Node 的可搜索字段（id/name/display_name/description/tags/type/status/namespace/invocation_count）同步到 MeiliSearch 索引。同步失败 SHALL 记录告警日志，但 NOT 影响 Node 注册的成功响应。

#### Scenario: 注册 Node 后索引同步
- **WHEN** 成功注册一个新 Node
- **THEN** 系统 SHALL 向 MeiliSearch 写入该 Node 的文档，使其可被搜索接口发现

#### Scenario: 索引同步失败不影响注册
- **WHEN** MeiliSearch 服务不可用，但 Node 注册数据库写入成功
- **THEN** 系统 SHALL 返回 201（注册成功），并记录索引同步失败的告警日志

---

### Requirement: 更新 Node 元信息
系统 SHALL 提供 `PATCH /api/v1/nodes/{node_id}` 端点（需认证），允许更新 `display_name`、`description`、`category`、`visibility`、`status` 字段。`name` 和 `type` 创建后 SHALL NOT 被修改。更新成功后，系统 SHALL 同步更新 MeiliSearch 中对应 Node 的索引文档。

#### Scenario: 更新 display_name 成功
- **WHEN** Node 所有者 PATCH 更新 display_name 为新值
- **THEN** 系统 SHALL 返回 200 和更新后的 NodeResponse

#### Scenario: 非所有者无法更新
- **WHEN** 非 Node 所有者尝试 PATCH 更新
- **THEN** 系统 SHALL 返回 403

#### Scenario: 更新后索引同步
- **WHEN** Node 元信息更新成功
- **THEN** 系统 SHALL 更新 MeiliSearch 中该 Node 的文档，使搜索结果反映最新数据

---

### Requirement: 软删除 Node
系统 SHALL 提供 `DELETE /api/v1/nodes/{node_id}` 端点（需认证），将 Node status 改为 `archived`，不物理删除记录。已归档的 Node SHALL NOT 出现在默认列表查询结果中。软删除成功后，系统 SHALL 从 MeiliSearch 索引中删除该 Node 文档。

#### Scenario: 软删除成功
- **WHEN** Node 所有者调用 DELETE /api/v1/nodes/{node_id}
- **THEN** 系统 SHALL 返回 204，Node status 变为 archived

#### Scenario: 归档后不出现在列表
- **WHEN** 调用 GET /api/v1/nodes（不带 status 过滤）
- **THEN** 系统 SHALL NOT 返回 status 为 archived 的 Node

#### Scenario: 归档后从搜索索引移除
- **WHEN** Node 被软删除后
- **THEN** 系统 SHALL 从 MeiliSearch 索引中删除该 Node 文档，使其不再出现在搜索结果中

---

### Requirement: Node 版本管理
系统 SHALL 提供 `GET /api/v1/nodes/{node_id}/versions` 和 `POST /api/v1/nodes/{node_id}/versions` 端点（需认证），用于查看版本列表和发布新版本。同一 Node 下版本号 SHALL 唯一，新发布的版本如标记 `is_default=true` SHALL 替换旧的默认版本。

#### Scenario: 查看版本列表
- **WHEN** 调用 GET /api/v1/nodes/{node_id}/versions
- **THEN** 系统 SHALL 返回该 Node 所有版本，按创建时间倒序排列

#### Scenario: 发布新版本
- **WHEN** Node 所有者 POST 提交合法的 NodeVersionCreate（含新版本号、schemas、runtime）
- **THEN** 系统 SHALL 创建 NodeVersion 记录，返回 201

#### Scenario: 版本号重复拒绝
- **WHEN** 提交与已有版本号相同的新版本
- **THEN** 系统 SHALL 返回 409

---

### Requirement: Node runtime_config supports credential_id
The system SHALL support an optional `credential_id` field in Node's runtime_config. When present, the system SHALL use the referenced credential for authentication and combine the credential's `base_url` with the Node's relative `endpoint` to form the full request URL.

#### Scenario: Node created with credential_id
- **WHEN** a Node is created via batch import with `credential_id` referencing a valid credential
- **THEN** the Node's runtime_config SHALL contain `credential_id` and a relative `endpoint` (e.g., `/translate` instead of `https://api.xxx.com/translate`)

#### Scenario: Node without credential_id (backward compatible)
- **WHEN** an existing Node has no `credential_id` in its runtime_config
- **THEN** the system SHALL continue using the full `endpoint` URL and the existing `auth` config from runtime_config (no behavior change)

### Requirement: Batch create Nodes endpoint
The system SHALL provide `POST /api/v1/nodes/batch` endpoint that accepts an array of Node definitions and creates them all in a single transaction.

#### Scenario: Batch create succeeds
- **WHEN** authenticated user submits an array of 4 valid Node definitions with a shared credential_id
- **THEN** the system SHALL create all 4 Nodes and their initial versions in one transaction, returning 201 with an array of NodeResponse objects

#### Scenario: Batch create with name conflict
- **WHEN** one of the batch items has a name that conflicts with an existing Node in the namespace
- **THEN** the system SHALL reject the entire batch with 409, indicating which name(s) conflict

#### Scenario: Batch create atomic rollback
- **WHEN** any Node in the batch fails validation
- **THEN** the system SHALL rollback the entire transaction (no partial creates)
