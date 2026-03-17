# Agent 集成指南

本文档介绍如何将 NodeVault 中注册的 AI 能力（Node）直接暴露给 LLM Agent，实现自动工具调用。

---

## 概览

NodeVault 提供两种 Agent 集成路径：

| 方式 | 协议 | 适用场景 |
|------|------|----------|
| REST Agency API | HTTP / JSON | OpenAI、自定义 Agent |
| MCP Server | SSE (MCP 1.0) | Claude Desktop、VS Code Copilot |

---

## 一、使用 OpenAI Function Calling

### 1.1 获取工具列表

```python
import httpx

NODEVAULT_URL = "http://localhost:8000"
API_KEY = "your_api_key"

headers = {"Authorization": f"Bearer {API_KEY}"}

# 获取所有活跃节点的 OpenAI 格式工具定义
resp = httpx.get(f"{NODEVAULT_URL}/api/v1/agent/tools", headers=headers)
tools = resp.json()["data"]
# tools 格式：[{"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}, ...]
```

### 1.2 完整 Agent 循环

```python
import json
import httpx
from openai import OpenAI

NODEVAULT_URL = "http://localhost:8000"
API_KEY = "your_api_key"
openai_client = OpenAI()
nv_headers = {"Authorization": f"Bearer {API_KEY}"}


def get_nodevault_tools() -> list[dict]:
    """从 NodeVault 获取最新工具列表"""
    resp = httpx.get(f"{NODEVAULT_URL}/api/v1/agent/tools", headers=nv_headers)
    resp.raise_for_status()
    return resp.json()["data"]


def execute_tool_call(tool_call) -> str:
    """通过 NodeVault 执行 LLM 返回的 tool_call"""
    payload = {
        "id": tool_call.id,
        "type": tool_call.type,
        "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
        },
    }
    resp = httpx.post(
        f"{NODEVAULT_URL}/api/v1/agent/execute-tool",
        json=payload,
        headers=nv_headers,
    )
    resp.raise_for_status()
    result = resp.json()["data"]
    return result["content"]


def run_agent(user_message: str) -> str:
    tools = get_nodevault_tools()
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # 没有工具调用，直接返回最终回答
        if not msg.tool_calls:
            return msg.content

        # 执行所有工具调用
        messages.append(msg)
        for tool_call in msg.tool_calls:
            content = execute_tool_call(tool_call)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": content,
            })


# 示例
answer = run_agent("帮我把文本 'hello world' 翻译成中文")
print(answer)
```

### 1.3 按意图动态发现工具

```python
# 根据自然语言意图搜索最相关的工具（适合工具数量庞大的场景）
resp = httpx.get(
    f"{NODEVAULT_URL}/api/v1/agent/discover",
    params={"intent": "翻译文本", "limit": 5, "format": "openai"},
    headers=nv_headers,
)
relevant_tools = resp.json()["data"]
```

### 1.4 按标签/类型过滤工具

```python
# 只获取 NLP 类型的工具
resp = httpx.get(
    f"{NODEVAULT_URL}/api/v1/agent/tools",
    params={"type": "llm", "tags": "translation,nlp"},
    headers=nv_headers,
)
```

---

## 二、使用 MCP Server（Claude / VS Code Copilot）

NodeVault 内置了兼容 MCP 1.0 规范的 SSE Server，任何支持 MCP 协议的客户端都可以直接连接。

### 2.1 Claude Desktop 配置

编辑 `~/.claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "nodevault": {
      "transport": {
        "type": "sse",
        "url": "http://localhost:8000/mcp/sse"
      },
      "env": {
        "NODEVAULT_API_KEY": "your_api_key"
      }
    }
  }
}
```

### 2.2 VS Code Copilot 配置

在 `.vscode/settings.json` 中添加：

```json
{
  "github.copilot.advanced": {
    "mcpServers": {
      "nodevault": {
        "url": "http://localhost:8000/mcp/sse",
        "headers": {
          "Authorization": "Bearer your_api_key"
        }
      }
    }
  }
}
```

### 2.3 MCP 暴露的工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `list_nodevault_nodes` | 列出可用节点 | `tags?: string`, `type?: string` |
| `invoke_nodevault_node` | 按名称调用节点 | `name: string`, `arguments_json: string` |

---

## 三、Node 到工具的映射规则

NodeVault 的 `input_schema` 字段直接用作 OpenAI Function Calling 的 `parameters`，无需额外转换：

| NodeVault 字段 | OpenAI Function Calling 字段 |
|---------------|------------------------------|
| `node.name` | `function.name`（小写+下划线，最长 64 字符）|
| `node.description` + `node.tags` | `function.description`（最长 1024 字符）|
| `node.input_schema` | `function.parameters` |

---

## 四、鉴权说明

所有 Agent API 端点均需要 Bearer Token：

```bash
# 获取 API Token（登录后保存）
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "your_password"}'

# 在 Agent 中使用
export NODEVAULT_API_KEY="<token>"
```

---

## 五、错误处理

```python
try:
    content = execute_tool_call(tool_call)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 404:
        # 节点名不存在或无活跃版本
        content = f"Error: Node not found - {e.response.json().get('detail')}"
    elif e.response.status_code == 422:
        # 参数校验失败
        content = f"Error: Invalid arguments - {e.response.json().get('detail')}"
    else:
        content = f"Error: {e}"
```
