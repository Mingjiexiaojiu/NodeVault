## Why

NodeVault 的核心价值在于让注册的能力被 AI Agent 自动发现和调用，而不仅仅是一个人工查询的目录。目前所有 Node 只能通过 REST API 手动调用，缺乏面向主流 AI 框架（OpenAI、LangChain、MCP）的标准化导出机制，Agent 无法自动"看见"这些能力。Phase 3 补齐这一关键缺口，让 NodeVault 真正成为 AI 基础设施。

## What Changes

- **新增** OpenAI Function Calling 格式导出：将单个或批量 Node 导出为 `{type: "function", function: {...}}` 格式
- **新增** LangChain Tool 代码导出：生成可直接使用的 Python `StructuredTool` 代码
- **新增** MCP Server 支持：内置 Model Context Protocol Server，Claude Desktop / VS Code Copilot 等客户端可直接接入
- **新增** Skill Package 下载：将 Node 打包为含 `skill.yaml` + `skill.py` + 测试的 ZIP 文件
- **新增** Agent 能力发现接口 `GET /api/v1/agent/discover`：自然语言意图 → 匹配 Node 列表
- **新增** Agent 工具批量拉取接口 `GET /api/v1/agent/tools`：启动时一次获取所有 OpenAI Tools
- **新增** OpenAI tool_call 代理执行接口 `POST /api/v1/agent/execute-tool`：接收 GPT 的 tool_call，自动路由执行
- **扩展** 前端 Node 详情页：增加导出入口（复制 JSON / 下载代码 / 下载 ZIP）

## Capabilities

### New Capabilities

- `skill-openai-export`: 将 Node 导出为 OpenAI Function Calling 格式（单个 + 批量），包含名称安全化、描述截断等规范处理
- `skill-langchain-export`: 将 Node 导出为 LangChain StructuredTool Python 代码，含 Pydantic input schema 生成
- `skill-mcp-server`: 内置 MCP Server（stdio 模式），`list_tools` 返回所有 active Node，`call_tool` 路由到运行时执行器
- `skill-package-export`: 将 Node 打包为 Skill Package ZIP（`skill.yaml` + `skill.py` + `README.md` + 测试文件）
- `agent-discovery-api`: Agent 能力发现与工具获取接口（`/agent/discover`、`/agent/tools`、`/agent/execute-tool`）
- `frontend-skill-export`: 前端 Node 详情页导出面板，支持在线预览各格式、一键复制或下载

### Modified Capabilities

- `node-invocation`: 新增按 Node **名称**（而非 ID）调用的路径，供 Agent 执行层使用（`invoke_node_by_name`）

## Impact

- **后端新增**：`backend/core/exporter/` 目录（`base.py`、`openai_exporter.py`、`langchain_exporter.py`、`mcp_server.py`、`skill_package_exporter.py`）；`backend/api/v1/export.py`；`backend/api/v1/agent.py`
- **后端修改**：`backend/core/runtime.py` 补充按名称查询并执行 Node 的方法；`backend/main.py` 注册新路由
- **前端新增**：Node 详情页导出面板组件 `NodeExportPanel.vue`
- **依赖新增**：`mcp` Python 包（`mcp>=1.0`）；ZIP 生成使用标准库 `zipfile`
- **无 Breaking Change**：所有新增接口，不修改现有 REST API 契约
