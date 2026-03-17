# LangChain 集成指南

本文档介绍如何将 NodeVault 中的 AI 能力（Node）集成到 LangChain Agent，通过导出 Python 工具代码或直接使用 REST API 两种方式实现。

---

## 方式一：导出 LangChain 工具代码（推荐）

NodeVault 可以将一个或多个 Node 直接导出为开箱即用的 LangChain `BaseTool` 子类代码。

### 1.1 从 UI 导出

在节点详情页点击 **📤 导出** → 选择 **LangChain** 标签 → 复制生成的 Python 代码。

### 1.2 从 API 导出

```bash
# 单节点导出
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/v1/nodes/{node_id}/export/langchain

# 批量导出（多个节点的工具定义合并到一个文件）
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/v1/export/batch?format=langchain&ids=id1,id2,id3"
```

### 1.3 使用导出的代码

导出的代码格式类似：

```python
# 由 NodeVault 自动生成 — 不要手动修改
import os
from langchain.tools import BaseTool
from nodevault_sdk import NodeVaultClient

_client = NodeVaultClient(
    base_url=os.environ["NODEVAULT_URL"],
    api_key=os.environ["NODEVAULT_API_KEY"],
)


class TranslateTextInput(BaseModel):
    text: str = Field(..., description="待翻译的文本")
    target_language: str = Field(..., description="目标语言，如 zh/en/ja")


class TranslateTextTool(BaseTool):
    name: str = "translate_text"
    description: str = "将文本翻译为指定语言。适用场景：多语言内容生成、用户输入本地化。"
    args_schema = TranslateTextInput

    def _run(self, **kwargs) -> str:
        result = _client.invoke("translate_text", kwargs)
        return str(result.output)


tools = [TranslateTextTool()]
```

将此代码保存为 `nodevault_tools.py`，然后在 Agent 中使用：

```python
from nodevault_tools import tools
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手，可以使用工具完成任务。"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "把 'Hello World' 翻译成中文和日语"})
print(result["output"])
```

---

## 方式二：运行时动态绑定工具

如果不想在代码中硬编码工具，可以在运行时从 NodeVault 动态获取工具列表。

### 2.1 将 NodeVault 端点包装为 LangChain Tool

```python
import os
import json
import httpx
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI

NODEVAULT_URL = os.environ["NODEVAULT_URL"]
API_KEY = os.environ["NODEVAULT_API_KEY"]
_headers = {"Authorization": f"Bearer {API_KEY}"}


def _build_langchain_tools() -> list:
    """从 NodeVault 获取工具列表并动态创建 @tool 函数"""
    resp = httpx.get(f"{NODEVAULT_URL}/api/v1/agent/tools", headers=_headers)
    resp.raise_for_status()
    openai_tools = resp.json()["data"]

    langchain_tools = []
    for t in openai_tools:
        fn_def = t["function"]
        fn_name = fn_def["name"]
        fn_desc = fn_def["description"]

        # 闭包捕获 fn_name
        def make_tool(name: str, description: str):
            @tool(name, description=description)
            def dynamic_tool(arguments: str) -> str:
                """执行 NodeVault 工具，arguments 为 JSON 字符串"""
                payload = {
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
                r = httpx.post(
                    f"{NODEVAULT_URL}/api/v1/agent/execute-tool",
                    json=payload,
                    headers=_headers,
                )
                r.raise_for_status()
                return r.json()["data"]["content"]
            return dynamic_tool

        langchain_tools.append(make_tool(fn_name, fn_desc))

    return langchain_tools


tools = _build_langchain_tools()
# 之后像普通 LangChain tools 一样使用
```

---

## 方式三：通过 Skill Package 安装独立工具

对于需要离线或生产可靠性的场景，可以下载完整的 Skill Package。

### 3.1 下载 Skill Package

```bash
# 从 UI 下载或通过 API
curl -O -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/v1/nodes/{node_id}/export/skill
# 下载 translate_text_skill.zip
```

### 3.2 解压并安装

```bash
unzip translate_text_skill.zip -d translate_text_skill/
pip install -e translate_text_skill/
```

Skill Package 内部结构：

```
translate_text_skill/
├── skill.yaml          # 元数据：name, version, input_schema
├── skill.py            # 使用 nodevault-sdk 的入口函数
├── README.md           # 使用说明
└── tests/
    └── test_skill.py   # 单元测试
```

### 3.3 在 LangChain 中使用

```python
from skill import invoke  # skill.py 暴露的 invoke 函数
from langchain.tools import tool

@tool("translate_text")
def translate_tool(text: str, target_language: str = "zh") -> str:
    """将文本翻译为指定语言"""
    result = invoke({"text": text, "target_language": target_language})
    return result["output"]
```

---

## 环境变量

所有集成方式都依赖以下环境变量：

```bash
export NODEVAULT_URL="http://localhost:8000"
export NODEVAULT_API_KEY="<your_api_token>"
```

---

## 依赖安装

```bash
# 基础 LangChain + OpenAI
pip install langchain langchain-openai

# NodeVault Python SDK
pip install nodevault-sdk
# 或从本地安装
pip install -e ./sdk
```

---

## 完整示例：多工具 Agent

```python
import os
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 假设已将导出的工具代码保存到 nodevault_tools.py
from nodevault_tools import tools  # type: ignore

llm = ChatOpenAI(model="gpt-4o", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个多语言内容助手。使用可用工具完成用户请求。"),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=5)

# 运行
response = executor.invoke({"input": "请用工具帮我把以下英文翻译成中文并做情感分析：I love this product!"})
print(response["output"])
```
