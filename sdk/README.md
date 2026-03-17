# nodevault-sdk

NodeVault 官方 Python SDK，用于在你的代码中直接调用 NodeVault 中注册的 AI 能力（Node）。

## 安装

```bash
pip install nodevault-sdk
# 或从本地源码安装
pip install -e ./sdk
```

## 快速开始

### 同步调用

```python
from nodevault_sdk import NodeVaultClient

client = NodeVaultClient(
    base_url="http://localhost:8000",
    api_key="your_api_key",
)

# 按节点名称调用
result = client.invoke(
    node_name="translate_text",
    input_data={"text": "Hello, world!", "target_language": "zh"},
)
print(result.output)  # -> "你好，世界！"
```

### 异步调用（FastAPI / asyncio 环境）

```python
from nodevault_sdk import AsyncNodeVaultClient

client = AsyncNodeVaultClient(
    base_url="http://localhost:8000",
    api_key="your_api_key",
)

async def main():
    result = await client.invoke(
        node_name="translate_text",
        input_data={"text": "Hello, world!", "target_language": "zh"},
    )
    print(result.output)
```

### 指定版本调用

```python
result = client.invoke(
    node_name="translate_text",
    input_data={"text": "Hello"},
    version="1.2.0",   # 不传则使用默认版本（is_default=True）
)
```

## API 参考

### `NodeVaultClient(base_url, api_key, timeout=30.0)`

同步客户端。

| 参数 | 类型 | 说明 |
|------|------|------|
| `base_url` | `str` | NodeVault 服务地址，例如 `http://localhost:8000` |
| `api_key` | `str` | Bearer Token，登录后从 NodeVault API 获取 |
| `timeout` | `float` | 请求超时时间（秒），默认 30 秒 |

#### `invoke(node_name, input_data, version=None) -> InvokeResponse`

调用指定节点并返回结果。

| 参数 | 类型 | 说明 |
|------|------|------|
| `node_name` | `str` | 节点的唯一标识名（`name` 字段） |
| `input_data` | `dict` | 符合节点 `input_schema` 的输入数据 |
| `version` | `str \| None` | 指定版本号，不传则使用默认版本 |

### `AsyncNodeVaultClient`

与 `NodeVaultClient` 接口完全相同，但 `invoke` 为 `async` 方法。

### `InvokeResponse`

| 字段 | 类型 | 说明 |
|------|------|------|
| `output` | `Any` | 节点执行的输出结果 |
| `node_name` | `str` | 节点名称 |
| `version` | `str` | 实际执行的版本号 |
| `latency_ms` | `float` | 执行耗时（毫秒） |

## 异常处理

```python
from nodevault_sdk import AuthError, NodeNotFoundError, NodeVaultError

try:
    result = client.invoke("my_node", {"input": "test"})
except AuthError:
    print("API Key 无效或已过期")
except NodeNotFoundError:
    print("节点不存在或没有活跃版本")
except NodeVaultError as e:
    print(f"调用失败: {e}")
```

| 异常 | 触发场景 |
|------|---------|
| `AuthError` | HTTP 401：Token 无效或过期 |
| `NodeNotFoundError` | HTTP 404：节点不存在或无活跃版本 |
| `NodeVaultError` | 其他 4xx/5xx 错误 |

## 环境变量方式配置

推荐在生产环境使用环境变量，避免硬编码密钥：

```python
import os
from nodevault_sdk import NodeVaultClient

client = NodeVaultClient(
    base_url=os.environ["NODEVAULT_URL"],
    api_key=os.environ["NODEVAULT_API_KEY"],
)
```

## 与 LangChain/Agent 集成

请参阅：
- [docs/langchain-integration.md](../docs/langchain-integration.md) — LangChain 集成指南
- [docs/agent-integration.md](../docs/agent-integration.md) — OpenAI Function Calling / MCP 集成指南

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest sdk/tests/
```

## 许可证

Apache-2.0
