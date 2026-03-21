## MODIFIED Requirements

### Requirement: 技能集详情页
前端 SHALL 在 /skills/{id} 页面展示 Skill 详情，包含名称、描述、所含节点列表、版本历史等信息。

#### Scenario: 节点列表展示多对多关系
- **WHEN** 用户打开技能集详情页
- **THEN** 节点列表 SHALL 从 skill_nodes 多对多关系获取（API 响应中 nodes 数组包含 node 基本信息 + usage_hint），替代原有的一对多 Node.skill_id 查询
- **AND** 每个节点行 SHALL 展示：节点名称、display_name、分类标签（category.display_name）、状态、usage_hint（可编辑）

#### Scenario: 添加节点到技能集
- **WHEN** 用户点击"添加节点"按钮
- **THEN** 前端 SHALL 弹出节点选择对话框，展示当前 namespace 下所有 active 节点（可搜索/筛选），用户选择后填写 usage_hint（可选），确认后调用 `POST /api/v1/skills/{skill_id}/nodes`，body 为 `{"node_id": "<UUID>", "usage_hint": "..."}`
- **AND** 添加成功后刷新节点列表

#### Scenario: 从技能集移除节点
- **WHEN** 用户点击某节点行的"移除"按钮
- **THEN** 前端 SHALL 弹出确认对话框，确认后调用 `DELETE /api/v1/skills/{skill_id}/nodes/{node_id}`
- **AND** 移除成功后刷新节点列表

#### Scenario: 编辑节点的 usage_hint
- **WHEN** 用户点击某节点行的 usage_hint 区域（支持行内编辑）
- **THEN** 前端 SHALL 切换为可编辑文本框，失焦或按 Enter 后调用 `PATCH /api/v1/skills/{skill_id}/nodes/{node_id}`，body 为 `{"usage_hint": "..."}`

#### Scenario: 系统技能集标识
- **WHEN** 技能集的 is_system 为 true
- **THEN** 详情页 SHALL 在名称旁显示「系统」badge（蓝色），且"删除技能集"按钮不可见

#### Scenario: 删除自定义技能集
- **WHEN** 技能集 is_system 为 false 且用户点击"删除技能集"
- **THEN** 前端 SHALL 弹出确认对话框（含技能集名称），确认后调用 `DELETE /api/v1/skills/{skill_id}`
- **AND** 删除成功后跳转到 /skills 列表页

### Requirement: 技能集列表页
前端 SHALL 在 /skills 页面展示技能集列表。

#### Scenario: 列表区分系统与自定义技能集
- **WHEN** 用户打开技能集列表
- **THEN** 每个卡片/行 SHALL 展示 is_system 状态：系统技能集显示「系统」badge，自定义技能集可显示「自定义」badge
- **AND** 支持按 is_system 筛选
