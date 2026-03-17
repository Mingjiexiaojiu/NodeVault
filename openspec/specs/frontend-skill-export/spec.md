## ADDED Requirements

### Requirement: Node detail page export panel
The frontend Node detail page SHALL display an export panel with tabs for each supported export format: OpenAI, LangChain, MCP, Skill Package.

For text-based formats (OpenAI, LangChain, MCP), the panel SHALL render a read-only code block with syntax highlighting and a "复制" (copy) button.
For Skill Package, the panel SHALL show a "下载 ZIP" button that triggers a file download.

#### Scenario: View OpenAI export format
- **WHEN** user clicks the "OpenAI" tab in the export panel on a node detail page
- **THEN** the panel loads and displays the JSON tool descriptor with syntax highlighting and a copy button

#### Scenario: Copy export content
- **WHEN** user clicks "复制" in any text-format tab
- **THEN** the content is copied to clipboard and the button briefly shows "已复制"

#### Scenario: Download skill package
- **WHEN** user clicks "下载 ZIP" in the Skill Package tab
- **THEN** browser downloads `<node_name>.zip` containing the skill package

#### Scenario: Export panel on node with no active version
- **WHEN** user opens the export panel on a node that has no active version
- **THEN** all tabs show a message "暂无活跃版本，无法导出" and action buttons are disabled
