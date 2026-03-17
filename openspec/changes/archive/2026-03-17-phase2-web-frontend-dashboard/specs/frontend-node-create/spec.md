## ADDED Requirements

### Requirement: User can register a new node via form
The system SHALL provide a form page at /nodes/new for registering a new node via POST /api/v1/nodes.

#### Scenario: Successful node creation
- **WHEN** user fills in all required fields (name, version, type, runtime.endpoint, runtime.method, input_schema, output_schema) and clicks "注册节点"
- **THEN** API POST /api/v1/nodes is called, and on success user is redirected to the new node's detail page

#### Scenario: Validation prevents invalid node name
- **WHEN** user enters a name that doesn't match pattern `^[a-z][a-z0-9_]{2,63}$`
- **THEN** inline validation shows: "名称须为小写字母、数字、下划线，3-64位，以字母开头"

#### Scenario: Duplicate node name error
- **WHEN** API returns 409
- **THEN** page shows error: "该命名空间下已存在同名节点"

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
