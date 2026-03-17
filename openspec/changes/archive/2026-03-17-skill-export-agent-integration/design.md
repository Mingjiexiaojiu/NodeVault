## Context

NodeVault 现有的运行时调用（`/invoke`）和注册 API 已完整，但缺乏面向 AI Agent 的标准化接入层。主流框架（OpenAI SDK、LangChain、Anthropic MCP）各有不同的工具描述格式，如果逐框架手动适配成本极高。

当前约束：
- Node 数据存储于 PostgreSQL，`NodeVersion.input_schema` 是标准 JSON Schema
- 运行时分派器（`RuntimeDispatcher`）已封装执行逻辑，导出器只需调用 `RuntimeDispatcher.get_executor(type).execute(config, args)`
- 搜索层（MeiliSearch）已支持全文 + 标签过滤，复用即可实现 Agent 能力发现
- Python SDK 位于 `sdk/` 目录，导出的 Skill Package 代码将依赖它

## Goals / Non-Goals

**Goals:**
- 统一导出架构：一个 `BaseExporter` 抽象，三个具体导出器（OpenAI / LangChain / Skill Package）
- MCP Server 以独立进程或 FastAPI SSE 路由方式运行
- Agent Discover/Tools/Execute-Tool 三个接口复用现有搜索和运行时模块
- 前端 Node 详情页新增导出面板（在线预览 + 一键复制/下载）
- 全部实现均有单元测试覆盖导出结果的 Schema 正确性

**Non-Goals:**
- 向量语义搜索（Phase 4 引入 embedding）；本阶段 `/discover` 仍使用关键词搜索
- LangChain Agent 的端到端运行（只导出 Tool 代码，不内置 LangChain 运行时）
- 多租户资源隔离的 MCP Server（Phase 5 企业级治理）
- WebSocket 流式输出

## Decisions

### 决策 1：导出器放在 `backend/core/exporter/` 而非 `backend/api/`

**选择**: `core/exporter/` 层

**理由**: 导出逻辑是纯粹的数据转换，不涉及 HTTP，放在 core 层可以被 API 路由、MCP Server、CLI 工具复用。API 层只负责调用导出器并序列化响应。

**被否决方案**: 直接写在 `api/v1/export.py` 中 — 导致 MCP Server 无法复用同一逻辑，测试也更难独立编写。

---

### 决策 2：MCP Server 以 FastAPI SSE 路由方式集成（而非独立进程）

**选择**: FastAPI 路由 `GET /mcp`，使用 `mcp` 库的 SSE transport

**理由**: 开发阶段无需额外部署，与现有认证中间件统一。MCP SSE transport 支持 HTTP 方式调用，Claude Desktop 和 VS Code Copilot 均已支持。

**被否决方案**: stdio 独立进程 — 需要打包为独立 CLI 工具（`nodevault-mcp`），增加发布复杂度；本阶段优先集成便利性。

---

### 决策 3：`/agent/execute-tool` 接受 OpenAI `tool_call` 对象原样

**选择**: 接收标准 OpenAI `tool_call` 结构（`{id, type, function: {name, arguments}}`）

**理由**: GPT 生成的 tool_call 可以直接转发，无需客户端二次解析，降低接入成本。`arguments` 是 JSON string，服务端 `json.loads()` 解析。

**被否决方案**: 自定义请求格式 — 不能直接 pass-through，每个客户端都要写胶水代码。

---

### 决策 4：Skill Package ZIP 内容结构

ZIP 包含：`skill.yaml` + `skill.py` + `README.md` + `tests/test_skill.py`，使用 Python 标准库 `zipfile` 生成，在内存中构建后以流返回（不写临时文件）。

---

### 决策 5：按 Node 名称调用（`invoke_node_by_name`）

Agent 层只知道 Node 名称（来自 OpenAI function name 或 MCP tool name），需要 `node-invocation` 模块新增按名称查找并执行的路径。名称在 namespace 内唯一，查询时限定 `status=active`。

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| OpenAI 函数名仅允许 `[a-z0-9_]` 最长 64 字符，Node 名称可能超出 | `_safe_name()` 静默截断 + 替换，导出时在描述里注明原始名称 |
| MCP `mcp` Python 包版本不稳定（协议仍在演进） | 锁定 `mcp>=1.0,<2.0`，隔离 MCP 相关代码到 `core/exporter/mcp_server.py` |
| `execute-tool` 接口可被滥用（任意 Node 名称执行） | 沿用现有 JWT 认证；Node 必须 `status=active` 才可执行；后续 Phase 5 加细粒度权限 |
| LangChain 版本多（v0.1 / v0.2 / v0.3）导出代码不通用 | 生成的代码最低依赖 `langchain-core`，只用 `StructuredTool`；在注释中注明兼容版本 |
| 大量 Node 时 `/agent/tools` 响应体过大 | 默认返回前 100 个，强制要求 `limit <= 200`，建议客户端按 tag 过滤 |

## Open Questions

- MCP Server 的认证方式：当前 FastAPI SSE 路由沿用 JWT Bearer，Claude Desktop 能否传递 HTTP header？如不能，是否需要支持 URL query param 传 token？（待 MCP 客户端验证后决定）
- Skill Package ZIP 中的 `skill.py` 是否内联实现逻辑还是通过 SDK 代理调用？本阶段选择 SDK 代理（安全，Node 实现变更时无需重新下载），但粒度更细的离线运行需求留待后续。
