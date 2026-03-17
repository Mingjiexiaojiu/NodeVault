## ADDED Requirements

### Requirement: Agent capability discovery by natural language intent
The system SHALL expose `GET /api/v1/agent/discover?intent=<text>&limit=<n>&format=<fmt>` that accepts a natural language description and returns matching Nodes.
The `format` parameter SHALL accept `openai` (default), `langchain`, `mcp`, or `raw`.
The endpoint SHALL reuse MeiliSearch keyword search with `limit * 2` candidates, then return top `limit` results in the requested format.

#### Scenario: Discover nodes by intent in OpenAI format
- **WHEN** `GET /api/v1/agent/discover?intent=我需要分析交易数据的风险&format=openai` is called
- **THEN** response contains `{"tools": [...]}` with nodes semantically related to the intent serialized as OpenAI Function Calling format

#### Scenario: Discover nodes in raw format
- **WHEN** `format=raw` is specified
- **THEN** response contains `{"nodes": [...]}` with full node data up to `limit` entries

### Requirement: Agent bulk tool fetching
The system SHALL expose `GET /api/v1/agent/tools` that returns all active Nodes as OpenAI Function Calling format.
Optional query parameters: `tags` (repeated), `type`, `namespace`.
Response SHALL include at most 200 tools; default limit is 100.

#### Scenario: Get all tools for agent startup
- **WHEN** `GET /api/v1/agent/tools` is called with a valid JWT
- **THEN** response contains `{"tools": [...]}` with all active nodes serialized as OpenAI tools

#### Scenario: Filter tools by tags
- **WHEN** `GET /api/v1/agent/tools?tags=finance&tags=risk` is called
- **THEN** only nodes tagged with both `finance` AND `risk` are included in the response

### Requirement: Proxy execution of OpenAI tool_call
The system SHALL expose `POST /api/v1/agent/execute-tool` that accepts an OpenAI `tool_call` object and executes the corresponding Node.

Request body:
```json
{"id": "call_abc", "type": "function", "function": {"name": "node_name", "arguments": "{...}"}}
```

Response SHALL conform to OpenAI tool result format: `{"tool_call_id": "...", "role": "tool", "content": "<json_output_string>"}`.

#### Scenario: Successful proxy execution
- **WHEN** `POST /api/v1/agent/execute-tool` is called with a valid tool_call for an active node
- **THEN** the node is invoked via `RuntimeDispatcher`, output is JSON-serialized, and response has `role: "tool"` with `tool_call_id` matching the request

#### Scenario: Node not found
- **WHEN** `function.name` does not match any active node
- **THEN** HTTP 404 is returned with an error message

#### Scenario: Invalid arguments JSON string
- **WHEN** `function.arguments` is malformed JSON
- **THEN** HTTP 422 is returned with a descriptive validation error
