## ADDED Requirements

### Requirement: Invoke node by name (for Agent layer)
The system SHALL provide an internal function `invoke_node_by_name(name: str, arguments: dict, user)` that looks up a Node by its `name` field (within `status=active` nodes), resolves its default version, and dispatches execution via `RuntimeDispatcher`.
This function SHALL be used by `POST /api/v1/agent/execute-tool` and the MCP Server `call_tool` handler.

#### Scenario: Successful invocation by name
- **WHEN** `invoke_node_by_name("detect_fund_pool", {...}, user)` is called and a matching active node exists with a default version
- **THEN** the function returns the execution output and latency_ms, and records an invocation log entry

#### Scenario: No active node with given name
- **WHEN** `invoke_node_by_name` is called with a name that matches no active node
- **THEN** the function raises `NodeNotFoundError` with message "No active node named '<name>'"

#### Scenario: Node exists but has no default version
- **WHEN** the node is active but has no version with `is_default=true`
- **THEN** the function raises `NodeVersionNotFoundError` with a descriptive message
