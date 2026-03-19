## Context

服务发现导入完成后，从同一个 OpenAPI 服务导入的多个节点在模型层面没有来源追踪。`credential_id` 虽然存在于 `runtime_config` JSONB 中，但无法做 FK 约束、索引查询或 diff 比较。现有模型：

```
ServiceCredential ──(credential_id in JSONB)──► NodeVersion.runtime_config
          无 FK，无索引，无法反查
```

## Goals / Non-Goals

**Goals:**
- Node 模型新增 `source_credential_id` 和 `source_path` 字段，建立显式来源关联
- 支持按 `source_credential_id` 过滤节点列表
- 探测同一服务时能 diff 出已导入/未导入的接口
- 前端服务发现页面展示 diff 状态

**Non-Goals:**
- 不引入独立的 `Service` 模型——用 `ServiceCredential` 作为服务的代理已足够
- 不改变调用链——`runtime_config.credential_id` 仍是调用时读取凭证的入口
- 不改变现有手动注册节点的流程

## Decisions

### 1. 在 Node 上加字段而非创建 Service 模型

**选择**: 在 `nodes` 表新增 `source_credential_id` (FK) 和 `source_path` (varchar)

**替代方案**: 创建独立的 `services` 表，`nodes` 通过 `service_id` 关联

**理由**: 当前 `ServiceCredential` 已经承载了服务的核心信息（name、base_url、auth）。再建一层 `Service` 模型只会增加复杂度。两个 nullable 字段就能满足来源追踪 + diff + 按服务筛选的需求，最小成本最大收益。

### 2. source_credential_id 与 runtime_config.credential_id 共存

```
Node.source_credential_id    → 来源追踪（管理视角："这个节点从哪来"）
NodeVersion.runtime_config.credential_id → 调用认证（运行视角："调用时用哪个凭证"）
```

**理由**: 两者职责不同。来源和运行凭证可能不一致——用户可能从服务 A 导入后，更换为服务 B 的凭证进行调用。职责分离避免耦合。

### 3. 删除凭证时 SET NULL

**选择**: `ON DELETE SET NULL`——删除 `ServiceCredential` 后，`source_credential_id` 置 null

**理由**: 删除凭证不应该影响节点本身。节点失去来源标记但继续存在。

### 4. diff 逻辑：source_credential_id + source_path 做匹配

探测同一服务时，查询 `WHERE source_credential_id = X`，用 `source_path` 与探测结果做集合比较：

```
已探测到路径 ∩ 数据库已有路径 → 已导入（标绿）
已探测到路径 - 数据库已有路径 → 新增（可勾选）
数据库已有路径 - 已探测到路径 → 已删除（标灰/警告）
```

## Risks / Trade-offs

- **[回填精度]** → 已有导入节点的 `source_credential_id` 需要从 `runtime_config.credential_id` 回填。JSON 字段存的是字符串 UUID，需要转换。通过 SQL `CAST` 处理。
- **[source_path 唯一性]** → 同一服务下同一路径 + 同一方法不应重复导入。但不做 UNIQUE 约束（用户可能有正当理由创建同路径不同配置的节点），改为在批量导入时做应用层去重检测。
- **[前端改动范围]** → 服务发现页面需要增加 diff 逻辑和展示，涉及额外的 API 调用。通过新增一个 `GET /api/v1/discovery/imported?credential_id=X` 接口集中获取已导入路径，避免前端逻辑过重。
