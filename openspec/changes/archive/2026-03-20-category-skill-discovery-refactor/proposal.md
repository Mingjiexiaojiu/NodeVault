## Why

当前系统中节点分类通过硬编码的 `NodeType` 枚举（8 固定值）和自由填写的 `category` 字符串两个字段共同承担，既不灵活也不一致。同时 Node 与 Skill 是一对多关系，无法满足"一个节点属于多个技能集"的需求。服务发现流程对重复 URL、连接失败、迭代更新等场景缺乏友好提示。需要一次性重构这三块能力。

## What Changes

- **BREAKING**: 合并 `Node.type`（枚举）+ `Node.category`（字符串）为 `Node.category_id`（FK → 新 `categories` 表），删除 `NodeType` 枚举
- **BREAKING**: 将 Node ↔ Skill 从一对多改为多对多（新增 `skill_nodes` 中间表），Node 表移除 `skill_id` 和 `usage_hint`，`usage_hint` 迁移到 `skill_nodes` 关联表
- 新增 `categories` 表，系统预设 8 个默认分类（对应原 `NodeType`），支持主管级用户自定义添加
- 每个默认分类自动创建一个同名系统 Skill（如 "risk-collection"）
- Skill 新增 `is_system` 标记，系统 Skill 不可随意删除；自定义 Skill 可删除
- 服务发现增强：探测前检测重复 URL 并提示历史记录、支持迭代检测（新增/已导入/已更新/已移除）、连接失败和文档未找到分类错误提示
- 迭代更新时，已有接口参数变化 → 在原 Node 上创建新版本
- 前端顶部导航新增"分类"入口（role ≤ 1 可见）

## Capabilities

### New Capabilities
- `category-management`: 分类表 CRUD、系统种子数据、角色权限控制（role ≤ 1 可增删）
- `frontend-category-management`: 分类管理前端页面与导航入口

### Modified Capabilities
- `node-registry`: Node 表字段变更（type+category → category_id），注册/更新逻辑适配
- `node-schema-standard`: 节点 schema 验证中 type → category_id，删除 NodeType 枚举
- `skill-collection`: Node ↔ Skill 改为多对多，Skill 新增 is_system 标记，自定义 Skill 可删除
- `skill-md-generator`: 从 skill_nodes 关联表读取 usage_hint 生成 SKILL.md
- `service-probe`: probe 错误细分（connection/timeout/dns/ssl/not_found/parse），返回 error_type
- `batch-import`: 重复 URL 检测、迭代更新逻辑（为变更接口创建新 Node 版本）
- `frontend-node-create`: 节点创建表单中 type 选择器 → 分类动态选择器
- `frontend-node-list`: 列表筛选从硬编码 NodeType → 动态分类
- `frontend-skill-collection`: 技能详情页多节点添加/移除 UI，系统技能标记
- `frontend-service-discovery`: 重复 URL 警告弹窗、迭代 diff 视图、细化错误提示
- `discovery-session`: session 支持迭代关联（同 base_url 多次探测）

## Impact

- **数据库**: 新增 `categories`、`skill_nodes` 表；Node 表删 3 列加 1 列；Skill 表加 `is_system`；需要数据迁移脚本（映射旧 type → category_id，搬迁 skill_id → skill_nodes）
- **后端 API**: 新增 `/api/v1/categories` CRUD 端点；修改节点、技能、发现相关端点
- **前端**: 新增分类管理页；修改节点创建/列表、技能详情、服务发现等页面
- **SDK**: `nodevault_sdk` 中 NodeType 引用需适配
- **搜索索引**: MeiliSearch 索引中 type 字段需迁移为 category 名称
