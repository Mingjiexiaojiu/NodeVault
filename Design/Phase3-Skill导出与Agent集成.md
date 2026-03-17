# Phase 3 — Skill 导出与 Agent 集成

> **周期：约 5 周**
> **目标：让 AI Agent 可以直接"看见"和使用 NodeVault 中的所有能力**

---

## 核心思想

> NodeVault 最强大的特性，是让所有注册的能力自动变成 AI Agent 可直接调用的工具。

Phase 3 是 NodeVault 跨越"工具型项目"和"AI 基础设施"的关键一跃：

```
注册一次 Node → 自动兼容所有主流 AI 框架
```

这意味着：
- OpenAI GPT 可以直接调用
- LangChain Agent 可以装载
- MCP Server 协议兼容
- 任何自定义 Agent 都可以通过 REST 接入

---

## 一、Skill 导出系统架构

```
NodeVault Registry
       │
       │ 导出请求
       ▼
 ExportService
       │
  ┌────┴────────────────────────────────┐
  ▼            ▼             ▼          ▼
OpenAI     LangChain       MCP      Skill Package
Exporter   Exporter      Exporter   Exporter
  │            │             │          │
  ▼            ▼             ▼          ▼
{tool JSON} Tool object  MCP schema  skills/目录
```

### 1.1 统一导出接口

```python
# core/exporter/base.py
from abc import ABC, abstractmethod
from typing import Any
from models.node import NodeVersion


class BaseExporter(ABC):
    """所有 Skill 导出器的基类"""

    @abstractmethod
    def export_node(self, node: dict, version: NodeVersion) -> Any:
        """将单个 Node 导出为目标格式"""
        pass

    @abstractmethod
    def export_nodes(self, nodes: list[dict]) -> Any:
        """将多个 Node 批量导出"""
        pass

    def _clean_schema(self, schema: dict) -> dict:
        """清理 schema，移除 NodeVault 内部字段"""
        cleaned = schema.copy()
        cleaned.pop("$schema", None)
        cleaned.pop("$id", None)
        return cleaned
```

---

## 二、OpenAI Tool 导出器

### 2.1 导出格式

```json
{
  "type": "function",
  "function": {
    "name": "detect_fund_pool",
    "description": "基于图算法检测交易数据中的可疑资金归集行为。输入原始交易流水，输出可疑账户列表及风险评分。",
    "parameters": {
      "type": "object",
      "properties": {
        "transactions": {
          "type": "array",
          "description": "原始交易流水列表",
          "items": {
            "type": "object",
            "properties": {
              "tx_id": {"type": "string"},
              "from_account": {"type": "string"},
              "to_account": {"type": "string"},
              "amount": {"type": "number"}
            }
          }
        },
        "threshold": {
          "type": "number",
          "description": "风险阈值，0-1之间，默认0.7",
          "default": 0.7
        }
      },
      "required": ["transactions"]
    }
  }
}
```

### 2.2 OpenAI 导出器实现

```python
# exporter/openai_exporter.py
from .base import BaseExporter
from typing import Any


class OpenAIExporter(BaseExporter):
    """将 Node 导出为 OpenAI Function Calling 格式"""

    def export_node(self, node: dict, version_data: dict) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self._safe_name(node["name"]),
                "description": self._build_description(node),
                "parameters": self._clean_schema(version_data["input_schema"]),
            }
        }

    def export_nodes(self, nodes: list) -> list[dict]:
        return [self.export_node(n["node"], n["version"]) for n in nodes]

    def _safe_name(self, name: str) -> str:
        """确保函数名符合 OpenAI 规范（a-z, 0-9, _, 最长64字符）"""
        import re
        safe = re.sub(r'[^a-z0-9_]', '_', name.lower())
        return safe[:64]

    def _build_description(self, node: dict) -> str:
        desc = node.get("description", "")
        if node.get("tags"):
            desc += f" [标签: {', '.join(node['tags'])}]"
        return desc[:1024]  # OpenAI 描述长度限制
```

### 2.3 OpenAI Proxy 集成

NodeVault 还可以扮演 OpenAI Tool 的**代理执行层**：

```python
# api/v1/openai_compat.py
"""
OpenAI 兼容层 - 让 NodeVault 无缝接入 OpenAI function_call 流程

流程：
1. 用户把 NodeVault 导出的 tools 传给 GPT
2. GPT 决定调用哪个 tool，并生成参数
3. 用户把 GPT 的 tool_call 发给 NodeVault /execute-tool
4. NodeVault 代理执行并返回结果
"""

@router.post("/execute-tool")
async def execute_openai_tool(
    tool_call: dict,      # OpenAI 的 tool_call 对象
    current_user = Depends(get_current_user),
):
    """
    接收 OpenAI tool_call，自动路由到对应的 Node 执行

    tool_call 格式:
    {
        "id": "call_abc123",
        "type": "function",
        "function": {
            "name": "detect_fund_pool",
            "arguments": "{\"transactions\": [...]}"
        }
    }
    """
    import json
    func_name = tool_call["function"]["name"]
    arguments = json.loads(tool_call["function"]["arguments"])

    # 找到对应的 Node 并调用
    result = await invoke_node_by_name(func_name, arguments, current_user)

    # 返回 OpenAI tool_result 格式
    return {
        "tool_call_id": tool_call["id"],
        "role": "tool",
        "content": json.dumps(result.output, ensure_ascii=False),
    }
```

---

## 三、LangChain Tool 导出器

### 3.1 导出格式

```python
# 导出为 LangChain Tool 对象
from langchain_core.tools import StructuredTool

detect_fund_pool = StructuredTool(
    name="detect_fund_pool",
    description="基于图算法检测交易数据中的可疑资金归集行为",
    args_schema=DetectFundPoolInput,   # Pydantic BaseModel
    func=lambda **kwargs: vault.invoke("detect_fund_pool", kwargs),
)
```

### 3.2 LangChain 导出器实现

```python
# exporter/langchain_exporter.py
from .base import BaseExporter
from typing import Any


class LangChainExporter(BaseExporter):
    """将 Node 导出为 LangChain Tool 代码"""

    def export_node(self, node: dict, version_data: dict) -> str:
        """生成 LangChain Tool Python 代码"""
        name = node["name"]
        description = node.get("description", "")
        input_schema = version_data["input_schema"]

        pydantic_model = self._generate_pydantic_model(name, input_schema)

        code = f'''
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from nodevault import NodeVaultClient

vault = NodeVaultClient(base_url="{{NODEVAULT_URL}}", api_key="{{NODEVAULT_API_KEY}}")

{pydantic_model}

def _invoke_{name}(**kwargs):
    result = vault.invoke("{name}", kwargs)
    return result.output

{name}_tool = StructuredTool(
    name="{name}",
    description="""{description}""",
    args_schema={self._model_class_name(name)},
    func=_invoke_{name},
)
'''
        return code

    def export_nodes(self, nodes: list) -> str:
        """生成包含所有 Node 的 tools 列表代码"""
        individual_exports = [
            self.export_node(n["node"], n["version"]) for n in nodes
        ]
        tool_names = [f"{n['node']['name']}_tool" for n in nodes]
        tools_list = f"\ntools = [{', '.join(tool_names)}]\n"
        return "\n".join(individual_exports) + tools_list

    def _model_class_name(self, node_name: str) -> str:
        return "".join(w.capitalize() for w in node_name.split("_")) + "Input"

    def _generate_pydantic_model(self, name: str, schema: dict) -> str:
        class_name = self._model_class_name(name)
        props = schema.get("properties", {})
        required = schema.get("required", [])

        fields = []
        for field_name, field_info in props.items():
            field_type = self._json_type_to_python(field_info.get("type", "any"))
            field_desc = field_info.get("description", "")
            is_required = field_name in required
            if is_required:
                fields.append(f'    {field_name}: {field_type} = Field(..., description="{field_desc}")')
            else:
                default = field_info.get("default", "None")
                fields.append(f'    {field_name}: {field_type} | None = Field({default!r}, description="{field_desc}")')

        fields_str = "\n".join(fields) if fields else "    pass"
        return f"class {class_name}(BaseModel):\n{fields_str}"

    def _json_type_to_python(self, json_type: str) -> str:
        mapping = {
            "string": "str", "integer": "int", "number": "float",
            "boolean": "bool", "array": "list", "object": "dict",
        }
        return mapping.get(json_type, "Any")
```

---

## 四、MCP Server 导出器

Model Context Protocol (MCP) 是 Anthropic 发布的 AI 工具标准协议。NodeVault 内置 MCP Server，让任何支持 MCP 的 LLM 客户端都能直接访问所有注册的 Node。

### 4.1 MCP 架构

```
LLM Client（支持MCP）
       │  MCP Protocol
       ▼
NodeVault MCP Server
       │
       ├── list_tools() → 返回所有 active Node 的 Tool 描述
       ├── call_tool(name, args) → 路由到对应 Node 执行
       └── 认证通过 MCP meta 传递
```

### 4.2 MCP Server 实现

```python
# exporter/mcp_server.py
"""
NodeVault 内置 MCP Server

启动后，任何支持 MCP 的客户端（如 Claude Desktop、VS Code Copilot）
都可以将 NodeVault 作为 MCP 工具服务器添加，
自动获得所有注册的 Node 能力。
"""
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, CallToolResult
import mcp.server.stdio as stdio
from core.registry import NodeRegistry
from core.runtime import RuntimeDispatcher


class NodeVaultMCPServer:
    def __init__(self, registry: NodeRegistry):
        self.server = Server("nodevault")
        self.registry = registry
        self._setup_handlers()

    def _setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """从 NodeVault 获取所有 active Node，转换为 MCP Tool 格式"""
            nodes = await self.registry.list_nodes(status="active")
            tools = []
            for node in nodes:
                version = await self.registry.get_default_version(node.id)
                if version:
                    tools.append(Tool(
                        name=node.name,
                        description=node.description or f"Node: {node.name}",
                        inputSchema=version.input_schema,
                    ))
            return tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """执行指定 Node"""
            import json

            node = await self.registry.get_node_by_name(name)
            if not node:
                return [TextContent(type="text", text=f"Error: Node '{name}' not found")]

            version = await self.registry.get_default_version(node.id)
            if not version:
                return [TextContent(type="text", text=f"Error: No active version for '{name}'")]

            try:
                executor = RuntimeDispatcher.get_executor(version.runtime_config["type"])
                output, latency_ms = await executor.execute(version.runtime_config, arguments)
                result_text = json.dumps(output, ensure_ascii=False, indent=2)
                return [TextContent(type="text", text=result_text)]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def run_stdio(self):
        """以 stdio 模式运行（适用于 Claude Desktop 集成）"""
        async with stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="nodevault",
                    server_version="1.0.0",
                ),
            )
```

### 4.3 Claude Desktop 配置示例

用户只需修改 Claude Desktop 配置文件：

```json
{
  "mcpServers": {
    "nodevault": {
      "command": "nodevault-mcp",
      "args": [],
      "env": {
        "NODEVAULT_URL": "http://nodevault.company.com",
        "NODEVAULT_API_KEY": "your-api-key"
      }
    }
  }
}
```

之后 Claude 就能自动看到并调用所有注册在 NodeVault 的能力。

---

## 五、Skill Package 导出器

Skill Package 是一种将 Node 打包为**可安装的代码目录**的格式，主要用于 Agent 框架（如 Agno/OpenClaw）的技能系统集成。

### 5.1 输出目录结构

```
skills/
└── detect_fund_pool/
    ├── skill.yaml          # 技能元数据
    ├── skill.py            # 执行逻辑
    ├── README.md           # 使用说明
    └── tests/
        └── test_skill.py   # 测试用例
```

### 5.2 skill.yaml 格式

```yaml
name: detect_fund_pool
version: "1.0.0"
description: "基于图算法检测交易数据中的可疑资金归集行为"
author: "RiskTeam"

# 能力分类
category: risk-analysis
tags: [finance, risk, aml]

# 入口函数
entrypoint: skill.execute

# 输入输出规范
input:
  transactions:
    type: array
    required: true
    description: "交易流水列表"

output:
  suspicious_accounts:
    type: array
    description: "可疑账户列表"

# 依赖（其他 Skill）
requires: []
```

### 5.3 skill.py 格式

```python
# skills/detect_fund_pool/skill.py
"""
NodeVault Skill: detect_fund_pool
自动生成 by NodeVault v1.0.0
"""
import os
from nodevault import NodeVaultClient

_vault = None

def _get_vault():
    global _vault
    if _vault is None:
        _vault = NodeVaultClient(
            base_url=os.environ["NODEVAULT_URL"],
            api_key=os.environ["NODEVAULT_API_KEY"],
        )
    return _vault


def execute(transactions: list, threshold: float = 0.7) -> dict:
    """
    检测资金池聚集行为

    Args:
        transactions: 交易流水列表
        threshold: 风险阈值，0-1之间

    Returns:
        包含可疑账户列表和风险评分的字典
    """
    result = _get_vault().invoke(
        "detect_fund_pool",
        input_data={"transactions": transactions, "threshold": threshold}
    )
    return result.output
```

---

## 六、Agent 自动发现系统

这是 Phase 3 最前沿的功能：Agent 无需预先知道 NodeVault 中有哪些能力，可以在运行时动态**发现并调用**合适的 Node。

### 6.1 自动发现 API

```python
# api/v1/agent.py
"""
Agent 自动发现接口

专为 AI Agent 设计的接口，支持：
1. 语义能力查询（用自然语言描述需求）
2. 按意图自动匹配 Node
3. 批量获取 OpenAI tools 格式
4. 追踪 Agent 调用来源
"""

@router.get("/discover")
async def discover_capabilities(
    intent: str = Query(..., description="用自然语言描述你的需求，如'我需要分析交易数据的风险'"),
    limit: int = Query(5, ge=1, le=20),
    format: str = Query("openai", enum=["openai", "langchain", "mcp", "raw"]),
    current_user = Depends(get_current_user),
):
    """
    Agent 能力发现接口。

    输入自然语言意图，返回最匹配的 Node 列表（带调用信息）。

    这是 NodeVault 最核心的 Agent 接入点。
    """
    # 第一步：关键词提取 + 语义搜索（Phase 3 先用关键词，Phase 4+ 引入向量搜索）
    search_service = NodeSearchIndex()
    raw_results = await search_service.search(query=intent, page_size=limit * 2)

    # 第二步：根据格式导出
    nodes_with_versions = await _enrich_with_versions(raw_results["hits"])

    if format == "openai":
        exporter = OpenAIExporter()
        return {"tools": exporter.export_nodes(nodes_with_versions)}
    elif format == "langchain":
        exporter = LangChainExporter()
        return {"code": exporter.export_nodes(nodes_with_versions)}
    elif format == "mcp":
        exporter = MCPExporter()
        return {"tools": exporter.export_nodes(nodes_with_versions)}
    else:
        return {"nodes": nodes_with_versions[:limit]}


@router.get("/tools")
async def get_all_tools_as_openai_format(
    tags: list[str] = Query([]),
    type: str | None = Query(None),
    namespace: str | None = Query(None),
    current_user = Depends(get_current_user),
):
    """
    获取指定范围内所有可用 Node 的 OpenAI Tool 格式。

    典型用法：Agent 启动时一次性拉取所有可用工具列表。
    """
    registry = NodeRegistry(db=...)
    nodes = await registry.list_nodes(
        status="active", tags=tags, type=type, namespace=namespace
    )
    nodes_with_versions = await _enrich_with_versions(nodes)
    exporter = OpenAIExporter()
    return {"tools": exporter.export_nodes(nodes_with_versions)}
```

### 6.2 Agent 使用 NodeVault 的完整流程

```python
# 示例：用 OpenAI SDK + NodeVault 构建完整 Agent

import openai
import httpx
import json

NODEVAULT_URL = "http://nodevault.company.com"
API_KEY = "your-api-key"

def build_agent():
    # 1. 从 NodeVault 获取所有工具
    resp = httpx.get(
        f"{NODEVAULT_URL}/api/v1/agent/tools",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"tags": ["finance", "risk"]},
    )
    tools = resp.json()["tools"]
    print(f"已加载 {len(tools)} 个 NodeVault 工具")

    client = openai.OpenAI()

    def run(user_input: str) -> str:
        messages = [{"role": "user", "content": user_input}]

        while True:
            # 2. 调用 GPT，传入 tools
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            messages.append(msg)

            # 3. 如果 GPT 没有调用工具，直接返回答案
            if not msg.tool_calls:
                return msg.content

            # 4. 执行工具调用（通过 NodeVault 代理）
            for tool_call in msg.tool_calls:
                tool_result_resp = httpx.post(
                    f"{NODEVAULT_URL}/api/v1/agent/execute-tool",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=tool_call.model_dump(),
                )
                tool_result = tool_result_resp.json()
                messages.append(tool_result)

    return run


agent = build_agent()
answer = agent("帮我分析这批交易数据中是否存在资金池风险")
print(answer)
```

---

## 七、导出 API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/nodes/{id}/export/openai` | 导出单个 Node 为 OpenAI Tool |
| `GET` | `/api/v1/nodes/{id}/export/langchain` | 导出单个 Node 为 LangChain Tool 代码 |
| `GET` | `/api/v1/nodes/{id}/export/mcp` | 导出单个 Node 为 MCP Schema |
| `GET` | `/api/v1/nodes/{id}/export/skill` | 下载 Skill Package（ZIP） |
| `GET` | `/api/v1/export/batch` | 批量导出多个 Node |
| `GET` | `/api/v1/agent/discover` | Agent 能力发现（自然语言） |
| `GET` | `/api/v1/agent/tools` | 获取所有 OpenAI Tools（按条件过滤） |
| `POST` | `/api/v1/agent/execute-tool` | 代理执行 OpenAI tool_call |
| `GET` | `/mcp` | MCP Server 入口（stdio/SSE） |

---

## 八、Phase 3 交付检查清单

```
□ OpenAI Function Calling 格式导出实现
□ LangChain Tool 代码导出实现
□ MCP Server 实现（stdio 模式）
□ Skill Package 下载（ZIP 文件）
□ 批量导出 API
□ Agent 能力发现接口（/discover）
□ Agent 工具批量获取接口（/tools）
□ OpenAI tool_call 代理执行接口
□ Claude Desktop MCP 配置示例文档
□ Agent 集成示例代码（完整可运行）
□ LangChain Agent 集成示例
□ 所有导出格式的单元测试
□ 导出结果的 Schema 验证
```

---

> **上一步 ←** [Phase 2 - 能力发现与 SDK](./Phase2-能力发现与SDK.md)
> **下一步 →** [Phase 4 - Workflow 编排引擎](./Phase4-Workflow编排引擎.md)
