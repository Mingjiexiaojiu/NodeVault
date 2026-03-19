# Node Service Binding Spec

## Overview
节点与来源服务的绑定关系规范。通过服务发现导入的节点 SHALL 记录其来源凭证 ID 和原始 OpenAPI 路径，支持按来源凭证过滤节点，以及探测时的 diff 展示。

---

### Requirement: Node 来源字段
Node 模型 SHALL 支持可选的 `source_credential_id`（UUID, FK → service_credentials.id, ON DELETE SET NULL）和 `source_path`（varchar(512), nullable）字段。手动创建的 Node 两字段均为 null；通过服务发现导入的 Node SHALL 写入对应的凭证 ID 和原始 OpenAPI 路径。

#### Scenario: 服务导入节点携带来源字段
- **WHEN** 通过批量导入 API 从某 ServiceCredential 导入节点
- **THEN** 系统 SHALL 将 `source_credential_id` 设为该凭证 ID，`source_path` 设为原始 OpenAPI 路径（如 `/api/v1/users`）

#### Scenario: 手动注册节点无来源字段
- **WHEN** 用户通过 `POST /api/v1/nodes` 手动注册节点
- **THEN** `source_credential_id` 和 `source_path` SHALL 为 null

#### Scenario: 删除凭证后来源置空
- **WHEN** 删除一个被节点引用的 ServiceCredential
- **THEN** 引用该凭证的所有节点的 `source_credential_id` SHALL 被设为 null

---

### Requirement: 节点详情展示来源信息
`GET /api/v1/nodes/{node_id}` 的 `NodeResponse` SHALL 包含可选的 `source_credential_id`、`source_path` 和 `source_service_name` 字段。`source_service_name` 从关联的 ServiceCredential.name 获取（如凭证已删除则为 null）。

#### Scenario: 查看导入节点的来源信息
- **WHEN** 查看一个通过服务导入的节点详情
- **THEN** 响应 SHALL 包含 `source_credential_id`、`source_path` 和 `source_service_name`

#### Scenario: 查看手动节点的来源信息
- **WHEN** 查看一个手动注册的节点
- **THEN** `source_credential_id`、`source_path`、`source_service_name` 均为 null

---

### Requirement: 查询已导入路径
系统 SHALL 提供 `GET /api/v1/discovery/imported?credential_id=<uuid>` 端点（需认证），返回该凭证下已导入的所有节点的 `source_path` 列表，用于探测时做 diff。

#### Scenario: 查询已导入路径列表
- **WHEN** 以有效 credential_id 调用该端点
- **THEN** 系统 SHALL 返回该凭证下所有节点的 `imported_paths` 列表

#### Scenario: 凭证无已导入节点
- **WHEN** 指定的凭证下无任何导入节点
- **THEN** 系统 SHALL 返回空数组

---

### Requirement: 探测 diff 展示
前端服务发现页面在探测完成后，如果当前选择了凭证，SHALL 请求已导入路径并对探测结果做 diff 标记：已导入（不可勾选，标绿）、新增（可勾选）。

#### Scenario: 探测已导入过的服务
- **WHEN** 用户探测一个之前已导入过部分接口的服务
- **THEN** 预览列表中已导入的接口 SHALL 标记为"已导入"且不可勾选，未导入的接口可正常勾选导入

#### Scenario: 服务新增了接口
- **WHEN** 服务比上次导入新增了接口
- **THEN** 新接口 SHALL 标记为"新增"并默认勾选
