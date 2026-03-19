## ADDED Requirements

### Requirement: 技能集列表页
系统 SHALL 在 `/skills` 路由提供技能集列表页，展示当前用户命名空间内的所有 active Skill，含节点数量、最新版本号和 is_stale 状态。

#### Scenario: 列出技能集
- **WHEN** 用户访问 /skills
- **THEN** 页面 SHALL 显示技能集卡片列表，每张卡片含 display_name、节点数量、最新版本、is_stale 警告标识（如有）和"查看详情"入口

#### Scenario: 空状态提示
- **WHEN** 用户没有任何 Skill
- **THEN** 页面 SHALL 显示引导提示"创建第一个技能集"和创建按钮

### Requirement: 创建技能集
系统 SHALL 在技能集列表页提供"新建技能集"按钮，点击后展示创建表单（name/display_name/description）。

#### Scenario: 创建成功跳转详情页
- **WHEN** 用户填写合法表单并提交
- **THEN** 系统 SHALL 调用 POST /api/v1/skills，成功后跳转到新建 Skill 的详情页

#### Scenario: name 格式校验
- **WHEN** 用户输入含大写字母或下划线的 name
- **THEN** 表单 SHALL 内联提示"名称须为 kebab-case（小写字母、数字、连字符）"

### Requirement: 技能集详情页
系统 SHALL 在 `/skills/{id}` 路由提供技能集详情页，展示所属节点列表、版本历史，以及生成/发布/下载操作区。

#### Scenario: is_stale 警告 banner
- **WHEN** Skill.is_stale 为 true
- **THEN** 页面 SHALL 在顶部显示警告 banner："节点已变更，建议重新生成 SKILL.md"

#### Scenario: 节点列表展示 usage_hint
- **WHEN** 查看 Skill 详情页的节点列表
- **THEN** 每个节点行 SHALL 展示 name、usage_hint（若为空则显示"未填写使用场景"警告）和节点状态

### Requirement: SKILL.md 生成与预览流程
系统 SHALL 在技能集详情页提供"生成 SKILL.md"按钮，点击后调用生成接口，结果展示在可编辑的代码块中，用户确认后填写版本号发布。

#### Scenario: 生成并预览
- **WHEN** 用户点击"生成 SKILL.md"
- **THEN** 系统 SHALL 显示加载状态，调用 POST /api/v1/skills/{id}/generate，成功后在页面内展示可编辑的 SKILL.md 文本和建议版本号

#### Scenario: 用户编辑生成内容
- **WHEN** 生成结果展示后，用户修改文本内容
- **THEN** 修改 SHALL 保留在前端状态，不自动触发接口调用

#### Scenario: 发布新版本
- **WHEN** 用户确认内容、填写版本号后点击"发布版本"
- **THEN** 系统 SHALL 调用 POST /api/v1/skills/{id}/versions，成功后版本历史列表更新，is_stale 警告消失

#### Scenario: 生成过程中按钮禁用
- **WHEN** 生成请求正在进行中
- **THEN** "生成 SKILL.md" 按钮 SHALL 显示 loading 状态且不可重复点击

### Requirement: 下载 ZIP
系统 SHALL 在技能集详情页提供"下载 ZIP"按钮，支持选择历史版本后下载。

#### Scenario: 下载最新版本
- **WHEN** 用户点击"下载 ZIP"
- **THEN** 浏览器 SHALL 触发文件下载，文件名为 `{skill_name}-{version}.zip`

#### Scenario: 选择历史版本下载
- **WHEN** 用户在版本历史列表中点击某历史版本的"下载"
- **THEN** 系统 SHALL 下载该版本对应的 ZIP
