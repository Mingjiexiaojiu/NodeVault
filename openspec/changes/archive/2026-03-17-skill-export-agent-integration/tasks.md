## 1. 基础架构：Exporter 模块

- [x] 1.1 创建 `backend/core/exporter/` 目录，添加 `__init__.py`
- [x] 1.2 实现 `backend/core/exporter/base.py`：`BaseExporter` 抽象类（`export_node`、`export_nodes`、`_clean_schema`）
- [x] 1.3 实现 `backend/core/exporter/openai_exporter.py`：`OpenAIExporter`（`_safe_name` 名称安全化、`_build_description` 描述截断 + tags 附加）
- [x] 1.4 实现 `backend/core/exporter/langchain_exporter.py`：`LangChainExporter`（Pydantic 模型代码生成、`_json_type_to_python` 类型映射、必填/可选字段区分）
- [x] 1.5 实现 `backend/core/exporter/skill_package_exporter.py`：`SkillPackageExporter`（生成 `skill.yaml`、`skill.py`、`README.md`、`tests/test_skill.py`，使用 `zipfile` 内存 ZIP 流）
- [x] 1.6 为三个 Exporter 编写单元测试（`backend/tests/test_exporters.py`），覆盖名称安全化、类型映射、ZIP 内容验证

## 2. 运行时：按名称调用 Node

- [x] 2.1 在 `backend/core/runtime.py`（或新建 `backend/core/invocation.py`）中实现 `invoke_node_by_name(name, arguments, user, db)` 函数
- [x] 2.2 函数中查询 `status=active` 的 Node by name，取其 `is_default=true` version，调用 `RuntimeDispatcher.get_executor(type).execute(config, args)`
- [x] 2.3 定义 `NodeNotFoundError` / `NodeVersionNotFoundError` 异常类
- [x] 2.4 为 `invoke_node_by_name` 编写单元测试（mock DB 查询和执行器）

## 3. REST 导出 API

- [x] 3.1 创建 `backend/api/v1/export.py` 路由文件
- [x] 3.2 实现 `GET /api/v1/nodes/{id}/export/openai`：调用 `OpenAIExporter.export_node`，返回 JSON
- [x] 3.3 实现 `GET /api/v1/nodes/{id}/export/langchain`：调用 `LangChainExporter.export_node`，返回 `text/plain` Python 代码
- [x] 3.4 实现 `GET /api/v1/nodes/{id}/export/mcp`：返回 MCP Tool 格式 JSON（`{name, description, inputSchema}`）
- [x] 3.5 实现 `GET /api/v1/nodes/{id}/export/skill`：调用 `SkillPackageExporter`，返回 `application/zip` 流响应（含正确 `Content-Disposition`）
- [x] 3.6 实现 `GET /api/v1/export/batch`：接收 `format` 和 `ids`（逗号分隔），批量导出；处理部分 ID 不存在的情况
- [x] 3.7 在 `backend/main.py` 中注册 export 路由器（通过 router.py）
- [x] 3.8 编写 `backend/tests/test_export_api.py` 集成测试（至少覆盖单节点和批量的 openai、langchain、skill 格式）

## 4. Agent API

- [x] 4.1 创建 `backend/api/v1/agent.py` 路由文件
- [x] 4.2 实现 `GET /api/v1/agent/discover`：接收 `intent`、`limit`（默认 5）、`format`（默认 `openai`）；调用 MeiliSearch 搜索，按 format 选择 Exporter 转发结果
- [x] 4.3 实现 `GET /api/v1/agent/tools`：接收 `tags`（repeated）、`type`、`namespace`，返回所有符合条件的 active Node 的 OpenAI Tools（上限 200，默认 100）
- [x] 4.4 实现 `POST /api/v1/agent/execute-tool`：接收 OpenAI `tool_call` 对象，`json.loads` 解析 `arguments`，调用 `invoke_node_by_name`，返回 `{tool_call_id, role: "tool", content}`；处理 404 / 422 错误
- [x] 4.5 在 `backend/main.py` 中注册 agent 路由器（通过 router.py）
- [x] 4.6 编写 `backend/tests/test_agent_api.py` 集成测试（discover / tools / execute-tool 的成功和失败路径）

## 5. MCP Server

- [x] 5.1 在 `pyproject.toml` 中添加 `mcp>=1.0,<2.0` 依赖并在 conda 环境中安装
- [x] 5.2 实现 `backend/core/exporter/mcp_server.py`：`NodeVaultMCPServer` 类，注册 `list_tools` 和 `call_tool` handler
- [x] 5.3 在 `backend/api/v1/` 新增 `mcp.py` 路由，挂载 MCP SSE transport 到 `GET /mcp`
- [x] 5.4 在 `backend/main.py` 中注册 MCP 路由，确保 JWT 认证可通过 Header 传入
- [x] 5.5 编写 `docs/mcp-integration.md`：Claude Desktop 配置示例、VS Code Copilot MCP 配置示例

## 6. 前端：导出面板

- [x] 6.1 在 `frontend/src/api/nodes.ts` 中添加导出 API 函数：`exportNodeOpenAI(id)`、`exportNodeLangChain(id)`、`exportNodeMCP(id)`、`downloadNodeSkillZip(id)`、`batchExport(ids, format)`
- [x] 6.2 创建 `frontend/src/components/NodeExportPanel.vue`：四个 tab（OpenAI / LangChain / MCP / Skill Package），文本 tab 含代码块 + 复制按钮，Skill Package tab 含下载按钮
- [x] 6.3 在 `NodeDetailView.vue` 的 action bar 中添加"导出"按钮，点击展开/折叠 `NodeExportPanel`
- [x] 6.4 在 `NodeExportPanel` 中实现复制到剪贴板功能（`navigator.clipboard.writeText`），复制后按钮短暂显示"已复制"
- [x] 6.5 实现无活跃版本时的禁用态提示"暂无活跃版本，无法导出"
- [ ] 6.6 测试：在本地开发环境验证 4 种导出格式均正常（后端服务可用时）

## 7. 文档与示例

- [x] 7.1 编写 `docs/agent-integration.md`：包含完整可运行的 OpenAI + NodeVault Agent 代码示例（参考 Phase 3 设计文档第六节）
- [x] 7.2 编写 `docs/langchain-integration.md`：LangChain Agent 集成示例
- [x] 7.3 更新 `sdk/nodevault_sdk/__init__.py` / `README`（如有必要），确保 `invoke()` 接口文档正确
