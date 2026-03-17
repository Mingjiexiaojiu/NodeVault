## ADDED Requirements

### Requirement: Export Node as LangChain StructuredTool Python code
The system SHALL generate valid Python source code for a LangChain `StructuredTool` when `GET /api/v1/nodes/{id}/export/langchain` is called.
Generated code SHALL include: a Pydantic `BaseModel` subclass derived from the node's `input_schema`, a `StructuredTool` instance referencing the NodeVault SDK `invoke()` call, and placeholder `{NODEVAULT_URL}` / `{NODEVAULT_API_KEY}` to be substituted by the user.

#### Scenario: Export node with typed fields
- **WHEN** `GET /api/v1/nodes/{id}/export/langchain` is called for an active node
- **THEN** response body is Python source code containing a Pydantic model class with fields matching `input_schema.properties` and correct Python type annotations

#### Scenario: Required vs optional fields in Pydantic model
- **WHEN** a field is listed in `input_schema.required`
- **THEN** generated Pydantic field uses `Field(...)` (required)

- **WHEN** a field is NOT listed in `input_schema.required`
- **THEN** generated Pydantic field uses `Field(<default>, ...)` with `| None` type annotation

#### Scenario: Batch LangChain export
- **WHEN** `GET /api/v1/export/batch?format=langchain&ids=id1,id2` is called
- **THEN** response contains concatenated Python code for all requested nodes plus a `tools = [...]` list at the end
