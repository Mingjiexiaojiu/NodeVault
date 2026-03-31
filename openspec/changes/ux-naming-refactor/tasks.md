## 1. Organization 模型与 API

- [x] 1.1 创建 Organization SQLAlchemy 模型（backend/models/organization.py）：id(UUID PK)、name(VARCHAR(128) UNIQUE NOT NULL)、created_at
- [x] 1.2 在 backend/models/__init__.py 中注册 Organization 模型
- [x] 1.3 创建 Organization 相关 schema（OrganizationCreate、OrganizationResponse）
- [x] 1.4 创建 Organization API 路由（backend/api/v1/organizations.py）：GET /organizations（列表+团队数量）、POST /organizations（创建，role≤1）
- [x] 1.5 在 API router 中注册 organizations 路由

## 2. Department 表改造

- [x] 2.1 修改 Department 模型：新增 org_id(UUID FK → organizations.id NOT NULL)、重命名 display_name → team_name、删除 slug 字段、添加 UNIQUE(org_id, team_name) 约束、添加 Organization relationship
- [x] 2.2 创建 Alembic migration：创建 organizations 表、从现有 departments.slug 去重填充 Organization 记录、departments 表添加 org_id 列并回填、重命名 display_name → team_name、删除 slug 列和索引、添加 UNIQUE(org_id, team_name)
- [x] 2.3 更新 Department 相关 schema：DepartmentCreate 改为接受 org_name + team_name（替代 slug + display_name）、DepartmentResponse 包含 organization_name + team_name
- [x] 2.4 更新 departments API 路由：创建团队时按 org_name 查找或创建 Organization 后关联；详情返回包含 organization_name；公开列表返回包含 organization_name + team_name
- [x] 2.5 更新 admin API 中部门相关逻辑：AdminDepartmentListItem 和创建端点改用 org_name + team_name

## 3. Node Response 字段调整

- [x] 3.1 更新 NodeResponse schema（backend/schemas/node.py）：department_slug 替换为 organization_name + team_name
- [x] 3.2 更新 AdminNodeListItem schema（backend/schemas/admin.py）：department_slug 替换为 organization_name + team_name
- [x] 3.3 更新 nodes API 路由中返回 department 信息的代码：填充 organization_name 和 team_name
- [x] 3.4 更新 auth API 中 UserDepartmentBrief：返回 organization_name + team_name 替代 slug

## 4. Category 字段简化

- [x] 4.1 修改 Category 模型：删除 name 字段、display_name 添加 UNIQUE 约束
- [x] 4.2 创建 Alembic migration：categories 表 display_name 加 UNIQUE 约束、删除 name 列和索引
- [x] 4.3 更新 Category schema：CategoryCreate 移除 name 字段、CategoryResponse 移除 name 字段
- [x] 4.4 更新 categories API 路由：创建时不再需要 name、唯一性校验改到 display_name
- [x] 4.5 更新默认分类种子数据：移除 name，只保留 display_name
- [x] 4.6 更新系统 Skill 自动创建逻辑：name 生成策略从 category.name 改为基于 display_name

## 5. Skill 创建交互优化

- [x] 5.1 修改 Skill 模型：display_name 改为 NOT NULL
- [x] 5.2 创建 Alembic migration：skills 表 display_name 改为 NOT NULL（先将 NULL 值填充为 name）
- [x] 5.3 更新 Skill schema：SkillCreate 中 display_name 改为必填、name 改为可选
- [x] 5.4 实现 name 自动生成逻辑：添加 pypinyin 依赖、创建 kebab-case 转换工具函数、处理冲突时追加数字后缀
- [x] 5.5 更新 skills API 路由：创建 Skill 时若不提供 name 则自动生成
- [x] 5.6 更新 skill_md_generator.py：优先使用 display_name 作为展示名

## 6. 搜索索引调整

- [x] 6.1 更新 backend/core/search.py：索引文档中 department_slug / team 字段替换为 organization_name + team_name
- [x] 6.2 更新 MeiliSearch 索引配置：可搜索和可过滤字段修改

## 7. 前端 — 类型定义与 API 层

- [x] 7.1 新建 frontend/src/api/organizations.ts：Organization 接口定义、获取列表 API
- [x] 7.2 更新 frontend/src/api/departments.ts：Department 接口去掉 slug、加 organization_name + team_name；创建函数改为接受 org_name + team_name
- [x] 7.3 更新 frontend/src/api/nodes.ts：NodeItem 接口 department_slug 替换为 organization_name + team_name
- [x] 7.4 更新 frontend/src/api/admin.ts：AdminNodeListItem、AdminDepartmentListItem 等接口调整

## 8. 前端 — 部门/团队视图改造

- [x] 8.1 重构 DepartmentListView.vue：列表展示"部门名称"+"团队名称"列、创建表单改为组织下拉（combobox）+ 团队名称输入、角色标签"管理员"→"主管"
- [x] 8.2 重构 DepartmentDetailView.vue：展示"部门名称"+"团队名称"、成员角色标签改为"主管"/"成员"、owner_id 显示为"拥有者"

## 9. 前端 — 节点相关视图调整

- [x] 9.1 更新 DashboardView.vue：节点 badge 从 department_slug 改为 team_name
- [x] 9.2 更新 NodeListView.vue：节点列表部门信息改为“组织/团队”格式、筛选器改用组织和团队
- [x] 9.3 更新 NodeDetailView.vue：节点详情部门信息改为“组织/团队”格式
- [x] 9.4 更新 SearchView.vue：搜索结果中部门信息改为“组织/团队”格式

## 10. 前端 — 分类管理视图简化

- [x] 10.1 更新 CategoryManageView.vue：创建表单移除"标识(name)"输入框、列表移除"标识"列、唯一名称字段标签改为"名称"

## 11. 前端 — 技能集视图优化

- [x] 11.1 更新 SkillListView.vue：创建表单主字段改为"技能集名称"(display_name) 必填、name 输入移到"高级选项"折叠区
- [x] 11.2 更新 SkillDetailView.vue：标题以 display_name 为主、name 为副标题 monospace

## 12. 前端 — 管理后台视图

- [x] 12.1 更新 admin/GlobalNodesView.vue：department_slug 列替换为 organization_name + team_name
- [x] 12.2 更新 admin/AdminAnalyticsView.vue：统计中部门信息展示调整
- [x] 12.3 更新管理后台部门管理相关视图（如有）：创建/编辑表单匹配新字段

## 13. 测试与验证

- [x] 13.1 更新后端测试：department 相关测试适配新模型（org_id + team_name）
- [x] 13.2 更新后端测试：category 相关测试适配删除 name 后的逻辑
- [x] 13.3 更新后端测试：skill 创建测试适配 display_name 必填 + name 自动生成
- [x] 13.4 更新数据库 SQL 文件（database/nodevault.sql）匹配新表结构
- [x] 13.5 运行全量测试确保无回归
