## Context

NodeVault 当前使用硬编码 `NodeType` 枚举（8 值）+ 自由文本 `category` 字段来分类节点；Node 与 Skill 是一对多关系（Node.skill_id FK）；服务发现不检测重复 URL 也不区分连接错误类型。

本次重构涉及三个交叉领域：分类管理、技能多对多、发现增强。因为分类替换影响 Node 表核心字段，与 Skill 关系重构同时进行可以合并为一次数据迁移。

当前技术栈：FastAPI + SQLAlchemy async + PostgreSQL + Alembic + Vue3/TS 前端。

## Goals / Non-Goals

**Goals:**
- 用动态 `categories` 表替代 `NodeType` 枚举，主管级可自定义分类
- Node ↔ Skill 改为多对多，`usage_hint` 绑定到关联关系
- 每个默认分类自动创建系统级 Skill
- 服务发现探测前检测重复 URL，提供迭代更新能力
- 细化 probe 错误分类，前端给出友好提示

**Non-Goals:**
- 分类层级（树形）— 本期只做扁平列表
- 接口自动更新 — 迭代检测后仍由用户手动确认导入
- 重新设计完整的 RBAC 权限系统 — 仅复用现有 `User.role` 字段

## Decisions

### D1: 分类模型设计 — 独立 `categories` 表

**选择**: 新建 `categories` 表（id, name, display_name, icon, sort_order, is_default, created_by）

**备选方案**:
- A) 改 `NodeType` 为数据库驱动的字符串表 — 不够规范，缺少元信息
- B) 用 Tag 系统替代 — Tag 是多对多的补充信息，不适合做互斥的主分类

**理由**: 独立表支持动态增删、排序、显示名、图标，且与 Node 是多对一关系语义明确。

### D2: Node 字段变更策略

**选择**: 
- 删除 `Node.type`（VARCHAR）、`Node.category`（VARCHAR）、`Node.skill_id`（UUID FK）、`Node.usage_hint`（VARCHAR）
- 新增 `Node.category_id`（UUID FK → `categories.id`，NOT NULL）

**迁移**: 
1. 先创建 `categories` 表并种子 8 条默认数据
2. 新增 `Node.category_id` 列（nullable）
3. `UPDATE nodes SET category_id = (SELECT id FROM categories WHERE name = nodes.type)`
4. `ALTER TABLE nodes ALTER COLUMN category_id SET NOT NULL`
5. 删除旧列

### D3: Node ↔ Skill 多对多 — 中间表 `skill_nodes`

**选择**: 新建关联表 `skill_nodes`（id, skill_id, node_id, usage_hint, sort_order, created_at），UNIQUE(skill_id, node_id)

**备选方案**:
- A) 保持一对多，通过多个 skill_id 列支持 — 不可扩展
- B) JSONB 数组存 skill_ids — 失去 FK 约束和 JOIN 能力

**理由**: 经典多对多模式，且 `usage_hint` 本质是关系属性（同一节点在不同技能中说明不同），放中间表语义最准确。

**迁移**:
1. 创建 `skill_nodes` 表
2. `INSERT INTO skill_nodes (skill_id, node_id, usage_hint) SELECT skill_id, id, usage_hint FROM nodes WHERE skill_id IS NOT NULL`
3. 删除 `Node.skill_id` 和 `Node.usage_hint`

### D4: 系统 Skill 与默认分类联动

**选择**: Skill 表新增 `is_system: bool`。迁移脚本为每个 `is_default=true` 的分类创建对应系统 Skill（`{name}-collection`）。系统 Skill 不可由普通用户删除。

### D5: 探测错误分类

**选择**: `ProbeResult` 新增 `error_type` 字段，枚举值：
- `connection_refused` — 连接被拒绝
- `timeout` — 连接超时
- `dns_error` — 域名解析失败
- `ssl_error` — TLS 握手失败
- `spec_not_found` — 探测路径均未命中
- `parse_error` — 找到文档但解析失败

**理由**: 当前只有一个 `error` 字符串字段，前端无法做结构化的 UI 提示。

### D6: 重复 URL 检测与迭代更新

**选择**: 
- 探测前查 `discovery_sessions WHERE base_url = ?`，有历史记录时返回提示
- 重新探测后，对比新 spec 端点与该 base_url 下已导入节点（通过 `Node.source_path` 匹配）
- 端点分为四类：🟢新增、🔵已导入、🟡已更新（参数变化）、🔴已移除
- 已更新端点导入时 → 在原 Node 上调用 `registry.create_version()` 创建新版本

### D7: 权限与前端入口

**选择**: 
- 分类管理入口放在顶部导航栏（与看板/节点/搜索同级），只在 `role ≤ 1` 时渲染链接
- API 端点用装饰器检查 `current_user.role <= 1`，否则 403
- 不引入新的权限框架，复用 `User.role` 字段（0=超管, 1=主管, 2=普通）

## Risks / Trade-offs

- **[数据迁移复杂度]** → 分类+多对多两处迁移合并到一个 Alembic revision，先在 dev 环境验证。提供 downgrade 脚本。
- **[NodeType 删除影响面广]** → 所有引用 NodeType 的代码（schema 验证、前端筛选、搜索索引、SDK）都要适配。通过 grep 全量扫描确保无遗漏。
- **[迭代检测的匹配准确性]** → 通过 `(base_url + source_path + method)` 三元组匹配。如果用户修改了 source_path 则无法自动关联，这是可接受的限制。
- **[系统 Skill 锁定]** → `is_system=true` 的 Skill 禁止普通删除。超管可以通过确认流程删除。

## Migration Plan

1. 创建 Alembic 迁移脚本（单 revision）：
   - `categories` 表 + 种子数据
   - `skill_nodes` 表
   - `skills.is_system` 列
   - 数据迁移（type→category_id, skill_id→skill_nodes）
   - 删除旧列
   - 创建系统 Skill
2. 更新 MeiliSearch 索引配置（type → category_name）
3. 前端部署后清除本地缓存的 NodeType 枚举

**回滚**: Alembic downgrade 恢复旧列 + 数据反向迁移。
