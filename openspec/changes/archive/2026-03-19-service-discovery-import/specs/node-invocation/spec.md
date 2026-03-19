## MODIFIED Requirements

### Requirement: Invoke node by name (for Agent layer)
The system SHALL provide an internal function `invoke_node_by_name(name: str, arguments: dict, user)` that looks up a Node by its `name` field (within `status=active` nodes), resolves its default version, and dispatches execution via `RuntimeDispatcher`.
This function SHALL be used by `POST /api/v1/agent/execute-tool` and the MCP Server `call_tool` handler.

When the resolved Node's runtime_config contains a `credential_id`, the system SHALL:
1. Look up the corresponding `service_credential` record
2. Check `credential_token_cache` for a valid (non-expired, with 60s margin) token
3. If no valid cached token exists, decrypt the credential, authenticate with the target service, and cache the new token
4. Inject the obtained token into the outgoing HTTP request headers
5. If the target service returns 401, force-refresh the token once and retry

When `credential_id` is null or absent, the system SHALL use the existing auth behavior from runtime_config (unchanged).

The system SHALL construct the full request URL by combining the credential's `base_url` with the Node's relative `endpoint` when `credential_id` is present.

#### Scenario: Successful invocation by name
- **WHEN** `invoke_node_by_name("detect_fund_pool", {...}, user)` is called and a matching active node exists with a default version
- **THEN** the function returns the execution output and latency_ms, and records an invocation log entry

#### Scenario: No active node with given name
- **WHEN** `invoke_node_by_name` is called with a name that matches no active node
- **THEN** the function raises `NodeNotFoundError` with message "No active node named '<name>'"

#### Scenario: Node exists but has no default version
- **WHEN** the node is active but has no version with `is_default=true`
- **THEN** the function raises `NodeVersionNotFoundError` with a descriptive message

#### Scenario: Invoke with credential_id auto-fetches token
- **WHEN** a Node has `credential_id` pointing to a bearer_login credential, and the cached token is expired
- **THEN** the system SHALL decrypt credentials, POST to the login endpoint, cache the new token, and use it to invoke the target API

#### Scenario: Invoke without credential_id uses existing auth
- **WHEN** a Node has no `credential_id` and its runtime_config has `auth.type=bearer` with `token_env`
- **THEN** the system SHALL use the existing behavior (reading token from environment variable)

#### Scenario: Target returns 401, token force-refreshed
- **WHEN** the target service returns 401 despite a cached token
- **THEN** the system SHALL force-refresh the token once and retry; if still 401, return an authentication error
