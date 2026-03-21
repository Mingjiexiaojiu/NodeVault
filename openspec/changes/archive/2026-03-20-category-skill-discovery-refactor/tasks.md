## 1. 数据库模型与迁移

- [x] 1.1 创建 Category 模型（backend/models/category.py）：id, name, display_name, icon, sort_order, is_default, created_by, created_at
- [x] 1.2 创建 SkillNode 关联模型（backend/models/skill_node.py）：id, skill_id, node_id, usage_hint, sort_order, created_at；UNIQUE(skill_id, node_id)
- [x] 1.3 Skill 模型添加 is_system 布尔字段（默认 false）
- [x] 1.4 Node 模型添加 category_id 字段（UUID FK → categories.id）
- [x] 1.5 更新 models/__init__.py 导出新模型
- [x] 1.6 创建 Alembic 迁移脚本：建 categories 表 + 种子 8 条默认分类 → 建 skill_nodes 表 → 加 skills.is_system → 加 nodes.category_id(nullable) → 数据迁移(type→category_id) → 迁移 skill_id+usage_hint 到 skill_nodes → 创建系统 Skill → 设 category_id NOT NULL → 删除 nodes.type/category/skill_id/usage_hint 旧列
- [x] 1.7 Node 模型移除 type, category, skill_id, usage_hint 字段；更新 relationships（添加 categories 和 skill_nodes 关系）
- [x] 1.8 Skill 模型更新 relationships（nodes 改为通过 skill_nodes 多对多关系）

## 2. Schema 与枚举适配

- [x] 2.1 删除 NodeType 枚举（backend/schemas/enums.py）
- [x] 2.2 创建 Category schemas（backend/schemas/category.py）：CategoryCreate, CategoryUpdate, CategoryRead
- [x] 2.3 创建 SkillNode schemas：SkillNodeCreate(node_id, usage_hint), SkillNodeUpdate(usage_hint), SkillNodeRead
- [x] 2.4 更新 NodeCreate/NodeUpdate schema：type → category_id(UUID, required)，移除 skill_id 和 usage_hint
- [x] 2.5 更新 NodeRead schema：返回 category 对象（id+display_name），移除 type/category/skill_id/usage_hint
- [x] 2.6 更新 SkillRead schema：nodes 列表从 skill_nodes 关联获取（含 usage_hint），增加 is_system 字段
- [x] 2.7 更新 ProbeResult schema：添加 error_type 枚举字段（connection_refused|timeout|dns_error|ssl_error|spec_not_found|parse_error）
- [x] 2.8 更新 DiscoverySession 相关 schema：添加 CompareRequest, CompareResult, IterateRequest, IterateResult

## 3. 分类管理后端 API

- [x] 3.1 创建分类 CRUD 路由（backend/api/v1/categories.py）：GET 列表, GET 详情, POST 创建(role≤1), PUT 更新(role≤1), DELETE 删除(role≤1, 非 is_default)
- [x] 3.2 创建角色检查依赖函数（require_manager_role）：检查 current_user.role ≤ 1，否则 403
- [x] 3.3 注册分类路由到 API v1 router
- [ ] 3.4 编写分类 API 单元测试

## 4. 节点注册适配

- [x] 4.1 更新节点 CRUD（registry.py）：创建/更新使用 category_id 替代 type；校验 category_id 存在
- [x] 4.2 更新节点查询：支持 category_id 筛选参数，替代原 type 筛选
- [x] 4.3 更新节点 API 路由中 query 参数（type → category_id）
- [x] 4.4 更新 MeiliSearch 索引同步：type 字段改为 category_name（JOIN categories 取 display_name）
- [ ] 4.5 更新节点相关测试用例（test_nodes.py 等）

## 5. 技能集多对多重构

- [x] 5.1 更新 Skill CRUD：列表/详情从 skill_nodes 关联获取节点（含 usage_hint）
- [x] 5.2 新增 Skill 节点管理端点：POST /skills/{id}/nodes（添加节点）、DELETE /skills/{id}/nodes/{node_id}（移除）、PATCH /skills/{id}/nodes/{node_id}（更新 usage_hint）
- [x] 5.3 更新 is_stale 触发逻辑：skill_nodes 关联变更时标记 is_stale=true
- [x] 5.4 系统 Skill 删除保护（is_system=true 时普通删除返回 403）
- [x] 5.5 自定义 Skill（is_system=false）删除时级联清理 skill_nodes
- [x] 5.6 更新 SkillVersion 快照逻辑：node_snapshot 包含 skill_nodes.usage_hint
- [ ] 5.7 更新技能集相关测试用例

## 6. SKILL.md 生成器适配

- [x] 6.1 更新 skill_md_generator.py：从 skill_nodes 关联表读取节点及对应 usage_hint（替代 Node.usage_hint）
- [x] 6.2 usage_hint 为空时回退到 node.description 推断场景描述
- [ ] 6.3 更新生成器测试用例

## 7. 服务探测增强

- [x] 7.1 更新 probe.py：在各异常捕获分支设置 error_type（ConnectionRefusedError→connection_refused, TimeoutError→timeout, socket.gaierror→dns_error, SSLError→ssl_error, 路径全未命中→spec_not_found, 解析失败→parse_error）
- [x] 7.2 ProbeResult 返回值包含 error_type + 中文 message
- [ ] 7.3 更新探测测试用例

## 8. 批量导入与迭代发现

- [x] 8.1 更新批量导入端点：节点数据使用 category_id 替代 type；忽略提交的 skill_id/usage_hint
- [x] 8.2 新增重复 URL 检测逻辑：导入前查询 discovery_sessions + nodes 判断 base_url 是否已注册
- [x] 8.3 新增端点比对 API（POST /discovery/sessions/{id}/compare）：path+method 匹配，返回 new/imported/updated/removed 状态
- [x] 8.4 新增迭代导入 API（POST /discovery/sessions/{id}/iterate）：根据 actions 执行 import(创建新Node)/update(创建新NodeVersion)/skip
- [x] 8.5 新增 DiscoverySession 历史查询（GET /discovery/sessions?base_url=xxx）
- [ ] 8.6 编写迭代发现测试用例

## 9. 前端 — 分类管理页面

- [x] 9.1 创建分类 API service（frontend/src/api/categories.ts）
- [x] 9.2 创建分类管理页面（/categories 路由，CategoryManageView.vue）：列表 + 增删改 + 排序
- [x] 9.3 在 AppLayout.vue 顶部导航添加“分类”入口，v-if="user.role <= 1" 条件渲染
- [x] 9.4 添加路由守卫：role > 1 访问 /categories 时重定向

## 10. 前端 — 节点页面适配

- [x] 10.1 更新节点创建/编辑表单：type 下拉 → 分类动态选择器（从 GET /categories 加载）
- [x] 10.2 移除节点创建/编辑表单中的 skill_id 下拉和 usage_hint 文本框
- [x] 10.3 更新节点列表页筛选区：type 筛选 → 分类动态筛选
- [x] 10.4 更新节点卡片/行：type badge → category.display_name badge

## 11. 前端 — 技能集页面适配

- [x] 11.1 更新技能集详情页：节点列表从 skill_nodes 关联展示（含 usage_hint 行内编辑）
- [x] 11.2 技能集详情页添加"添加节点"对话框（节点搜索 + usage_hint 输入）
- [x] 11.3 技能集详情页节点"移除"按钮 + 确认对话框
- [x] 11.4 技能集列表/详情展示 is_system badge（系统/自定义标识）
- [x] 11.5 自定义技能集"删除"按钮 + 确认对话框；系统技能集隐藏删除按钮

## 12. 前端 — 服务发现增强

- [x] 12.1 发现页分类选择器替代 type 选择器（动态加载）
- [x] 12.2 新增重复 URL 检测提示弹窗（迭代更新 / 重新导入 / 取消）
- [x] 12.3 新增迭代比对差异视图（new 绿/imported 灰/updated 黄/removed 红 badge + 勾选操作）
- [x] 12.4 迭代导入确认 + 执行报告展示（imported/updated/skipped 计数）
- [x] 12.5 探测失败结构化错误展示（按 error_type 渲染图标 + 提示文案 + 重试按钮）

## 13. SDK 适配与搜索索引

- [x] 13.1 更新 nodevault_sdk 中 NodeType 引用 → 移除或替换为 category_id
- [x] 13.2 更新 MeiliSearch reindex 脚本（scripts/reindex_search.py）：type → category_name
- [x] 13.3 更新种子数据脚本（scripts/seed_data.py）适配新分类模型

## 14. 集成测试与验收

- [x] 14.1 端到端测试：创建分类 → 创建节点(category_id) → 添加到 Skill → 生成 SKILL.md
- [x] 14.2 端到端测试：探测服务 → 检测重复 → 迭代比对 → 确认导入 → 验证新版本
- [x] 14.3 验证 Alembic upgrade/downgrade 完整可逆
- [x] 14.4 验证前端所有修改页面无控制台错误
