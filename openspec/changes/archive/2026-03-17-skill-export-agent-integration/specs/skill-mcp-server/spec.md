## ADDED Requirements

### Requirement: Built-in MCP Server via FastAPI SSE route
The system SHALL expose a Model Context Protocol (MCP) Server at `GET /mcp` using SSE transport mode.
The MCP Server SHALL implement `list_tools` and `call_tool` handlers.
`list_tools` SHALL return all Nodes with `status=active` serialized as MCP `Tool` objects using the node's active version `input_schema`.
`call_tool` SHALL route execution to the existing `RuntimeDispatcher` and return results as `TextContent`.

#### Scenario: MCP client lists available tools
- **WHEN** an MCP-compatible client connects to `/mcp` and calls `list_tools`
- **THEN** the response contains one MCP Tool entry per active Node with correct `name`, `description`, and `inputSchema`

#### Scenario: MCP client calls a tool
- **WHEN** an MCP client calls `call_tool` with a valid node name and valid arguments
- **THEN** the system executes the node via `RuntimeDispatcher`, returns the output as `TextContent(type="text", text=<json_output>)`

#### Scenario: MCP client calls unknown tool
- **WHEN** an MCP client calls `call_tool` with a name that does not match any active node
- **THEN** the system returns `TextContent(type="text", text="Error: Node '<name>' not found")`

#### Scenario: Claude Desktop configuration
- **WHEN** the Claude Desktop config file includes the NodeVault MCP server entry with `NODEVAULT_URL` and `NODEVAULT_API_KEY`
- **THEN** Claude can call all active NodeVault Nodes as tools without additional setup
