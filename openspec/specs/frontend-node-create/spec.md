## ADDED Requirements

### Requirement: User can register a new node via form
The system SHALL provide a form page at /nodes/new for registering a new node via POST /api/v1/nodes. The form SHALL include a Skill selector（下拉选择已有 Skill）and a `usage_hint` textarea（使用场景描述，选填，最长 500 字符）。

#### Scenario: Successful node creation
- **WHEN** user fills in all required fields (name, version, type, runtime.endpoint, runtime.method, input_schema, output_schema) and clicks "注册节点"
- **THEN** API POST /api/v1/nodes is called, and on success user is redirected to the new node's detail page

#### Scenario: Validation prevents invalid node name
- **WHEN** user enters a name that doesn't match pattern `^[a-z][a-z0-9_]{2,63}$`
- **THEN** inline validation shows: "名称须为小写字母、数字、下划线，3-64位，以字母开头"

#### Scenario: Duplicate node name error
- **WHEN** API returns 409
- **THEN** page shows error: "该命名空间下已存在同名节点"

#### Scenario: Skill selector loads existing Skills
- **WHEN** user opens the Skill selector dropdown
- **THEN** 系统 SHALL 调用 GET /api/v1/skills 并展示 Skill 列表，含"不归属任何技能集"选项

#### Scenario: usage_hint 字符数提示
- **WHEN** 用户在 usage_hint 输入框中输入内容
- **THEN** 表单 SHALL 实时显示剩余可输入字符数（500 - 已输入字符数）

### Requirement: 节点编辑页支持更新 Skill 和 usage_hint
The system SHALL allow updating `skill_id` and `usage_hint` on the node edit page（`/nodes/{id}/edit` 或详情页内编辑）。

#### Scenario: 切换 Skill 成功
- **WHEN** 用户在编辑页将节点从 Skill A 改为 Skill B 并保存
- **THEN** 系统 SHALL 调用 PATCH /api/v1/nodes/{id}，返回成功后页面显示新的技能集名称

#### Scenario: usage_hint 为空的节点显示提醒
- **WHEN** 节点的 usage_hint 为空且已归属某个 Skill
- **THEN** 节点详情页 SHALL 显示提示：\"建议填写使用场景描述，以提升 SKILL.md 生成质量\"

### Requirement: Form provides runtime configuration fields
The system SHALL show conditional runtime fields based on selected type.

#### Scenario: HTTP runtime fields appear for type=http
- **WHEN** user selects runtime type "http"
- **THEN** fields for endpoint URL and method (GET/POST/PUT/DELETE) are shown

### Requirement: Form provides JSON schema editors for input/output
The system SHALL provide a textarea-based JSON editor for input_schema and output_schema.

#### Scenario: JSON syntax validation
- **WHEN** user types invalid JSON in the input_schema or output_schema field and attempts to submit
- **THEN** submission is blocked and the field is highlighted with "无效的 JSON 格式"

### Requirement: Form includes tag input
The system SHALL allow users to add multiple tags as comma-separated values.

#### Scenario: Tags are parsed and submitted
- **WHEN** user types "finance,risk,aml" in the tags field
- **THEN** these are sent as the `tags` array in the request body
