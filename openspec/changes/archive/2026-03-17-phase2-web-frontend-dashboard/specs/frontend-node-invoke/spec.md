## ADDED Requirements

### Requirement: User can invoke a node from the browser
The system SHALL provide an invoke page at /nodes/:id/invoke that calls POST /api/v1/nodes/:id/invoke.

#### Scenario: Successful invocation
- **WHEN** user enters valid JSON in the input field and clicks "发起调用"
- **THEN** API is called, response output is displayed with syntax highlighting, latency_ms is shown

#### Scenario: Input JSON validation before submission
- **WHEN** user enters invalid JSON and clicks "发起调用"
- **THEN** submission is blocked and an error "输入参数必须是有效的 JSON 对象" is shown

#### Scenario: Invocation error displayed
- **WHEN** the API returns 502 (timeout or upstream error)
- **THEN** error message from the API detail field is displayed in a red alert box

### Requirement: Invoke page shows selected version
The system SHALL allow users to optionally specify a version.

#### Scenario: Default version pre-selected
- **WHEN** invoke page loads
- **THEN** the version selector defaults to "默认版本" (passes null for version field)

#### Scenario: Specific version selected
- **WHEN** user selects a specific version from the dropdown
- **THEN** that version string is included in the request body as `"version": "<ver>"`

### Requirement: Invocation result includes metadata
The system SHALL display full InvokeResponse fields after a call.

#### Scenario: Result panel shows metadata
- **WHEN** invocation succeeds
- **THEN** result panel shows: output (JSON highlighted), latency_ms, version, invocation_id

### Requirement: Loading state shown during invocation
The system SHALL show a loading indicator while the invocation is in progress.

#### Scenario: Loading spinner during call
- **WHEN** user clicks "发起调用" and the request is pending
- **THEN** the button shows a spinner and is disabled to prevent duplicate submissions
