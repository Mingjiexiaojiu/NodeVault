## MODIFIED Requirements

### Requirement: 创建技能集
系统 SHALL 在技能集列表页提供"新建技能集"按钮，点击后展示创建表单。表单主字段为"技能集名称"（display_name，必填）和"描述"（description，可选）。`name`（kebab-case 标识）SHALL 藏在"高级选项"折叠区域内，默认不展开，未填写时由后端自动生成。

#### Scenario: 只填名称创建成功
- **WHEN** 用户只填写"技能集名称"和可选描述后提交
- **THEN** 系统 SHALL 调用 POST /api/v1/skills（display_name 必传，name 不传），成功后跳转到详情页

#### Scenario: 展开高级选项自定义标识
- **WHEN** 用户点击"高级选项"展开折叠区
- **THEN** 表单 SHALL 显示"标识 (kebab-case)"输入框，带格式校验提示

#### Scenario: name 格式校验
- **WHEN** 用户在高级选项中输入含大写字母或下划线的 name
- **THEN** 表单 SHALL 内联提示"标识须为 kebab-case（小写字母、数字、连字符）"

### Requirement: 技能集列表展示
技能集列表页 SHALL 以 `display_name` 作为卡片主标题。`name`（标识）作为辅助信息以小号 monospace 字体显示在标题下方。

#### Scenario: 卡片展示
- **WHEN** 技能集列表渲染卡片
- **THEN** 每张卡片 SHALL 主标题为 display_name，副标题为 name（monospace），以及节点数量、最新版本、is_stale 状态

### Requirement: 技能集详情页标题
技能集详情页标题 SHALL 以 `display_name` 为主标题，`name` 以 monospace 小字显示。

#### Scenario: 详情页标题
- **WHEN** 用户访问技能集详情页
- **THEN** 页面标题 SHALL 显示 display_name 为主标题，name 为副标题
