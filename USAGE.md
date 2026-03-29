# NodeVault 用户使用手册

本手册面向所有 NodeVault 使用者，包含网页界面的操作说明和 Python SDK 的使用方法。

---

## 目录

1. [基本概念](#基本概念)
2. [网页界面使用](#网页界面使用)
   - [注册与登录](#注册与登录)
   - [部门管理](#部门管理)
   - [注册节点](#注册节点)
   - [搜索与发现节点](#搜索与发现节点)
   - [管理服务凭据](#管理服务凭据)
   - [查看技能与导出](#查看技能与导出)
3. [Python SDK 使用](#python-sdk-使用)
   - [安装与认证](#安装与认证)
   - [注册节点](#注册节点-sdk)
   - [搜索与发现](#搜索与发现)
   - [调用节点](#调用节点)
   - [异步使用](#异步使用)
   - [异常处理](#异常处理)
4. [常见场景示例](#常见场景示例)

---

## 基本概念

在开始使用前，了解几个核心概念会让你事半功倍：

| 概念 | 通俗解释 |
|-----|---------|
| **节点 (Node)** | 你注册进来的一个 AI 服务或算法，例如「风险评分」「OCR 识别」。每个节点对应一个可调用的接口 |
| **部门 (Department)** | 团队/业务线的分组，用于隔离权限。你的节点属于某个部门，其他部门的人按权限访问 |
| **技能 (Skill)** | 节点自动生成的调用描述，可以直接提供给 AI（如 ChatGPT、Claude）当作工具使用 |
| **服务凭据 (Credential)** | 调用下游服务时需要的账号、密码或 Token。NodeVault 统一存储，自动处理鉴权，不需要你手动传 |
| **服务发现 (Discovery)** | NodeVault 以 MCP 协议对外暴露你注册的节点，让 AI 框架可以自动「发现」可用工具 |

---

## 网页界面使用

### 注册与登录

1. 打开 NodeVault 网址，在浏览器访问：
   - **Docker / 服务器部署**：`http://your-server:8000`
   - **本地开发模式**：`http://localhost:5173`
2. 点击右上角「注册」，填写用户名、邮箱和密码完成注册
3. 注册后自动登录，进入主页

> 如果你的公司已有 NodeVault 实例，请联系管理员获取访问地址并邀请你加入部门。

---

### 部门管理

部门是 NodeVault 中权限隔离的基本单位。注册后你需要加入一个部门，才能查看和管理该部门的节点。

**查看部门列表**

- 点击顶部导航的「部门」，可以看到所有可见的部门
- 点击某个部门可以进入详情，查看该部门下的节点和成员

**申请加入部门**

- 在部门列表页点击你想加入的部门
- 点击「申请加入」，等待管理员审批

**创建部门（需要管理员权限）**

- 进入「管理控制台」→「部门管理」
- 点击「新建部门」，填写名称和描述

---

### 注册节点

节点是对你已有服务的一个「标签」，告诉 NodeVault 这个服务叫什么、接收什么参数、返回什么结果。

**第一步：进入节点页面**

点击顶部导航的「节点」，进入节点列表页。

**第二步：新建节点**

点击右上角「新建节点」，填写以下信息：

| 字段 | 说明 |
|-----|------|
| 节点名称 | 唯一标识，只能用英文字母、数字和下划线，例如 `risk_score` |
| 显示名称 | 给人看的名字，例如「风险评分」 |
| 描述 | 简要说明这个节点能做什么，AI 会根据描述来理解和调用它 |
| 类型 | 选择 `tool`（工具）、`analysis`（分析）等类型 |
| 标签 | 关键词，方便搜索和分类 |
| 接口地址 | 你的服务实际对外暴露的 HTTP 接口 URL |
| 输入/输出格式 | 用 JSON Schema 描述参数和返回值的结构 |

**第三步（可选）：绑定服务凭据**

如果你的服务接口需要鉴权（如 Bearer Token、账号密码登录），可以在「服务凭据」下拉框中选择一个已有的凭据绑定到节点。NodeVault 会在调用时自动处理认证，无需你手动传 Token。

点击「保存」完成注册。

---

### 搜索与发现节点

**关键词搜索**

- 点击顶部导航的「搜索」
- 在搜索框输入关键词，如「风险」「文本分析」
- 可以用标签、类型进一步筛选结果
- 点击节点卡片查看详情，包括接口说明和使用方法

**服务发现（给 AI 框架用）**

- 点击顶部导航的「发现」
- 这里展示了 NodeVault 以 MCP 协议提供的接口地址
- 将这个地址配置到 Claude Desktop、OpenAI 等工具中，AI 就能自动发现和使用你注册的节点

---

### 管理服务凭据

服务凭据用于存储访问下游服务所需的认证信息，NodeVault 会加密保存，并在调用节点时自动使用。

**查看凭据列表**

- 点击右上角头像菜单，选择「服务凭据」
- 可以看到你创建的所有凭据

**新建凭据**

点击「新建凭据」，填写：

| 字段 | 说明 |
|-----|------|
| 名称 | 给这个凭据起一个方便识别的名字 |
| 目标地址前缀 | 填写服务的 URL 前缀，例如 `http://risk-service`。当节点没有手动绑定凭据时，NodeVault 会自动匹配最合适的凭据 |
| 认证类型 | 选择合适的认证方式（见下方说明） |

**支持的认证类型：**

| 认证类型 | 适用场景 |
|---------|---------|
| `bearer_login` | 服务需要先用账号密码登录换取 Token，NodeVault 自动登录并缓存 Token |
| `static_token` | 服务使用固定不变的 Bearer Token |
| `api_key` | 服务使用 API Key 认证 |
| `basic_auth` | 服务使用 HTTP Basic Authentication（用户名+密码） |
| `none` | 服务不需要认证 |

**测试凭据**

创建凭据后，点击「测试连接」，NodeVault 会用这个凭据向目标服务发送一次测试请求，确认凭据是否有效。

**凭据的自动匹配机制**

如果你的节点没有手动绑定凭据，NodeVault 会根据节点接口地址（`endpoint`）的前缀，自动查找最匹配的凭据。例如：

- 你有一个凭据的「目标地址前缀」是 `http://risk-service`
- 你的节点接口地址是 `http://risk-service/api/v1/score`
- NodeVault 会自动使用这个凭据进行鉴权，无需手动绑定

---

### 查看技能与导出

NodeVault 会自动将你注册的节点生成为各种 AI 框架可以直接使用的「技能」格式。

- 点击顶部导航的「技能」
- 选择一个节点，可以看到它生成的 OpenAI Function Calling / LangChain / MCP 格式定义
- 复制这些定义，直接粘贴到你的 AI 应用中使用

---

## Python SDK 使用

如果你习惯用代码来操作，NodeVault 提供了一个易用的 Python SDK。

### 安装与认证

**安装**

```bash
pip install nodevault-sdk
```

**连接方式一：API Key（推荐生产环境）**

```python
from nodevault_sdk import NodeVaultClient

vault = NodeVaultClient(
    base_url="http://nodevault.yourcompany.com",
    api_key="your-api-key",
)
```

**连接方式二：邮箱 + 密码（自动登录）**

```python
vault = NodeVaultClient(
    base_url="http://localhost:8000",
    email="user@example.com",
    password="your-password",
)
# SDK 会自动完成登录并管理 Token
```

---

### 注册节点（SDK）

```python
node = vault.register(
    name="risk_score",                    # 节点唯一标识
    display_name="风险评分",               # 显示名称
    description="根据账户行为计算风险评分",  # 描述（AI 理解用途的关键）
    type="analysis",                      # 类型
    tags=["finance", "risk"],             # 标签
    endpoint="http://ml-service/api/score",  # 服务接口地址
    input_schema={
        "type": "object",
        "properties": {
            "account_id": {"type": "string", "description": "账户ID"}
        },
        "required": ["account_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "score": {"type": "number", "description": "风险分值 0-1"}
        },
    },
)
print("注册成功，节点 ID:", node.id)
```

**装饰器注册（更简洁的写法）**

```python
@vault.node(
    name="detect_anomaly",
    type="analysis",
    description="检测账户中的异常交易行为",
    tags=["fraud", "risk"],
    endpoint="http://fraud-service/api/detect",
)
def detect_anomaly(transactions: list) -> dict:
    """函数的类型注解会自动转换为 JSON Schema"""
    pass
```

---

### 搜索与发现

```python
# 关键词搜索
results = vault.search("资金风险", type="analysis")
for node in results:
    print(f"{node.display_name} — {node.description}")

# 列出所有节点
all_nodes = vault.list_nodes()

# 按类型筛选
tools = vault.list_nodes(type="tool")
```

---

### 调用节点

```python
# 基本调用
response = vault.invoke("risk_score", input_data={"account_id": "ACC_001"})

print(response.output)      # {"score": 0.87}
print(response.latency_ms)  # 120（毫秒）
print(response.node_name)   # "risk_score"
```

**调用流程说明：** NodeVault 会自动处理认证（如果节点绑定了凭据）、重试逻辑，以及请求转发。你只需要关心输入和输出。

---

### 异步使用

如果你的项目使用了 FastAPI 或 asyncio，推荐使用异步客户端：

```python
import asyncio
from nodevault_sdk import AsyncNodeVaultClient

async def main():
    vault = AsyncNodeVaultClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
    )

    # 异步搜索
    results = await vault.search("文本分析")

    # 异步调用
    response = await vault.invoke("risk_score", input_data={"account_id": "ACC_001"})
    print(response.output)

asyncio.run(main())
```

---

### 异常处理

```python
from nodevault_sdk.exceptions import AuthError, NodeNotFoundError, NodeVaultError

try:
    result = vault.invoke("risk_score", input_data={"account_id": "ACC_001"})
except NodeNotFoundError:
    print("节点不存在，请检查节点名称是否正确")
except AuthError:
    print("认证失败，请检查 API Key 或账号密码")
except NodeVaultError as e:
    print(f"调用出错: {e}")
```

---

## 常见场景示例

### 场景一：接入一个需要登录的内部服务

1. 进入「服务凭据」，新建凭据，类型选 `bearer_login`
2. 填写登录接口地址、账号和密码
3. 点击「测试连接」确认凭据有效
4. 新建节点时，在「服务凭据」下拉框选择刚才创建的凭据
5. 之后调用这个节点，NodeVault 会自动登录、缓存 Token、处理过期重登，你无需关心

---

### 场景二：让 ChatGPT/Claude 使用你的内部服务

1. 在 NodeVault 中注册你的服务为节点，填写清晰的描述和参数说明
2. 进入「技能」页面，找到你的节点，复制其 OpenAI Function Calling 定义（JSON 格式）
3. 将该 JSON 粘贴到你调用 OpenAI API 的 `tools` 参数中
4. 当用户向 GPT 提问时，GPT 会判断是否需要调用你的服务，并自动构造请求参数

---

### 场景三：自动化脚本批量调用

```python
from nodevault_sdk import NodeVaultClient

vault = NodeVaultClient(base_url="http://nodevault.company.com", api_key="xxx")

# 批量处理一组账户
account_ids = ["ACC_001", "ACC_002", "ACC_003"]
for account_id in account_ids:
    result = vault.invoke("risk_score", input_data={"account_id": account_id})
    print(f"{account_id}: 风险分 = {result.output['score']}")
```

---

### 场景四：在同一个部门内共享服务能力

1. 让负责某个服务的团队成员将该服务注册为节点，并分配到你们共同的部门
2. 其他部门成员可以在「节点」页面看到这个节点，直接使用，无需重复开发
3. 管理员可以在「管理控制台」查看调用统计，了解哪些服务最常被使用

---

如有问题，请联系系统管理员或提交 Issue。
