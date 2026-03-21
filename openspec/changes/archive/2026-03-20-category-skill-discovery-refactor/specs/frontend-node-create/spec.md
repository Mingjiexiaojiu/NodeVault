## ADDED Requirements

### Requirement: 节点创建表单
前端 SHALL 提供节点创建 / 编辑表单，包含所有 NodeCreate schema 要求的字段，提交后调用 POST /api/v1/nodes（创建）或 PUT /api/v1/nodes/{id}（编辑）。

#### Scenario: 分类选择器替代原有 type 下拉
- **WHEN** 用户打开节点创建或编辑表单
- **THEN** 表单 SHALL 显示「分类」下拉选择器，选项从 `GET /api/v1/categories` 动态加载，展示 display_name，提交时传 category_id（UUID）
- **AND** 不再显示旧的「类型」下拉（NodeType 枚举）

#### Scenario: 创建时分类为必填
- **WHEN** 用户未选择分类就提交表单
- **THEN** 前端 SHALL 高亮分类字段并显示"请选择分类"校验提示

