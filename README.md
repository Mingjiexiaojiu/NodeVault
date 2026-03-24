<div align="center">

<img src="docs/assets/NodeVault.png" alt="NodeVault" width="480" />

**Enterprise AI Capability Registry**

企业级 AI 能力注册中心 — 注册一次，处处调用

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)

</div>

---

## 这是什么？

NodeVault 是一个**AI 能力基础设施平台**——把企业中散落在各处的 AI 处理能力（数据清洗、资金分析、风险评分、NLP 服务……）统一注册为标准化的**节点 (Node)**，让任何 AI Agent、Workflow、业务系统都能按需发现、调用、组合这些能力。

```
你的 AI 能力                         任何 AI 框架
                                   
数据清洗服务 ──┐                   ┌── OpenAI GPT (Function Calling)
资金分析算法 ──┤                   ├── LangChain Agent
风控评分模型 ──┼──▶ NodeVault ──▶──┼── Claude (MCP Protocol)
NLP 实体识别 ──┤    注册·发现·调用  ├── 自研 Agent
OCR 识别服务 ──┘                   └── Workflow 编排
```

**一句话定位：**

> NodeVault = npm（能力仓库）+ Airflow（编排引擎）+ AI Tool Registry（Agent 接入层）

## 为什么需要 NodeVault？

在企业 AI 工程实践中，你一定遇到过这些问题：

| 痛点 | NodeVault 的解法 |
|------|-----------------|
| 每个团队重复造轮子，数据清洗写了 5 遍 | **能力注册** — 写一次，注册到 NodeVault，所有人复用 |
| Agent 想调用内部服务，得写一堆胶水代码 | **Skill 导出** — 自动生成 OpenAI / LangChain / MCP 工具定义 |
| 不知道公司内部有哪些可用的 AI 能力 | **能力发现** — 全文搜索 + 语义搜索，按标签/类型精准定位 |
| 分析流水线在每个项目里手动串联 | **Workflow 编排** — DAG 定义，串/并行自动执行 |
| 生产环境谁调了什么、调了多少次，完全黑盒 | **企业治理** — RBAC、调用审计、限流计费、全链路追踪 |

## 与 Dify / LangChain 的区别

NodeVault 不是另一个 AI 应用构建平台：

```
Dify / LangChain = AI App Builder（构建 AI 应用）
NodeVault        = AI Capability Infrastructure（管理 AI 能力）
```

它们是互补关系——Dify 负责搭建 AI 应用，NodeVault 负责提供和管理应用背后的原子能力。

## 核心特性

### 📦 Node 注册与管理

以标准化的 YAML Schema 定义 AI 能力，支持版本管理、标签分类、命名空间隔离：

```yaml
name: detect_fund_pool
version: "1.0.0"
display_name: "资金池检测"
description: 基于图算法检测交易数据中的可疑资金归集行为
type: analysis
tags: [finance, risk, graph-algorithm]

input_schema:
  type: object
  properties:
    transactions: { type: array, description: "交易流水列表" }
  required: [transactions]

output_schema:
  type: object
  properties:
    suspicious_accounts: { type: array }
    risk_scores: { type: object }

runtime:
  type: http
  endpoint: http://risk-service/api/v1/fund_pool_detect
```

### 🔍 能力发现

全文搜索 + 标签过滤 + 语义搜索，让 Agent 和开发者快速定位所需能力：

```bash
# 关键词搜索
GET /api/v1/search/nodes?q=资金风险分析&type=analysis&tags=finance

# Agent 自然语言发现
GET /api/v1/agent/discover?intent=我需要检测交易中的洗钱行为&format=openai
```

### 🤖 多框架 Skill 导出

注册一次 Node，自动导出为所有主流 AI 框架的工具格式：

```
NodeVault
  ├── → OpenAI Function Calling JSON
  ├── → LangChain StructuredTool
  ├── → MCP Server（Claude Desktop 直接使用）
  └── → Skill Package（可安装的能力包）
```

### ⚡ 统一调用

不管底层服务是 Python、Java 还是 ML 模型，统一通过 NodeVault 调用：

```python
from nodevault import NodeVaultClient

vault = NodeVaultClient(base_url="http://nodevault.company.com", api_key="your-key")

# 直接调用
result = vault.invoke("detect_fund_pool", {
    "transactions": [{"from": "A", "to": "B", "amount": 50000}]
})

# 装饰器注册
@vault.node(name="risk_score", type="risk", endpoint="http://ml-service/score")
def calculate_risk(account_id: str) -> dict:
    pass
```

### 🔀 Workflow 编排

通过 DAG 编排多个 Node，构建复杂的 AI 处理流水线：

```
数据清洗 ──→ 资金流向分析 ──→ 风险评分 ──→ 报告生成
                  │
                  └──→ 资金池检测 ──┘
```

### 🏢 企业级治理

RBAC 权限控制、多租户命名空间隔离、操作审计日志、API 限流、OpenTelemetry 全链路追踪。

## 技术栈

| 层级 | 技术 |
|------|------|
| Web 框架 | FastAPI (Python) |
| 数据库 | PostgreSQL + SQLAlchemy |
| 搜索引擎 | MeiliSearch → Elasticsearch |
| 缓存/队列 | Redis + Celery |
| 认证 | JWT / API Key |
| 可观测性 | OpenTelemetry + Prometheus + Grafana |
| 容器化 | Docker Compose → Kubernetes (Helm) |

## 项目结构

```
nodevault/
├── api/v1/           # FastAPI 路由（Node/Workflow/Export/Auth）
├── core/             # 核心业务逻辑（注册/搜索/执行/版本管理）
├── workflow/          # Workflow DAG 引擎
├── exporter/          # Skill 导出（OpenAI/LangChain/MCP）
├── sdk/              # Python SDK
├── models/           # SQLAlchemy ORM 数据模型
├── schemas/          # Pydantic 请求/响应模型
├── auth/             # 认证授权（JWT/RBAC）
├── database/         # 数据库连接与 Alembic 迁移
├── observability/    # 追踪/指标/审计
├── tests/            # 单元/集成/E2E 测试
├── deploy/           # Docker Compose + Helm Chart
└── main.py           # 应用入口
```

## 快速开始

### 后端

```bash
# 克隆项目
git clone https://github.com/your-org/nodevault.git
cd nodevault

# 启动基础设施
docker compose -f deploy/docker-compose.dev.yml up -d

# 安装依赖
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"

# 运行数据库迁移
copy .env.example .env
alembic upgrade head

# 启动服务
uvicorn backend.main:app --reload --port 8000

# 访问 API 文档
# http://localhost:8000/docs

超级管理员权限 MJXJadmin/Admin123 
```

### 前端（开发模式）

```bash
cd frontend

# 安装依赖（需要 Node.js 18+ 与 pnpm）
pnpm install

# 启动开发服务器（代理 /api → http://localhost:8000）
pnpm dev
# 访问 http://localhost:5173
```

### 前端（生产构建）

```bash
cd frontend
pnpm build
# 产出物在 frontend/dist/
# 启动后端后访问 http://localhost:8000/ 即可加载前端 SPA
```

## Python SDK 快速上手

`nodevault-sdk` 提供同步与异步两种客户端，通过 pip 安装：

```bash
pip install nodevault-sdk
```

### 认证

```python
from nodevault_sdk import NodeVaultClient

# 方式一：使用 API Key（推荐生产环境）
vault = NodeVaultClient(base_url="http://localhost:8000", api_key="your-api-key")

# 方式二：邮箱 + 密码（自动登录获取 token）
vault = NodeVaultClient(
    base_url="http://localhost:8000",
    email="user@example.com",
    password="your-password",
)
```

### 注册 Node

```python
node = vault.register(
    name="risk_score",
    type="analysis",
    description="计算账户风险评分",
    tags=["finance", "risk"],
    endpoint="http://ml-service/api/score",
    input_schema={
        "type": "object",
        "properties": {"account_id": {"type": "string"}},
        "required": ["account_id"],
    },
    output_schema={
        "type": "object",
        "properties": {"score": {"type": "number"}},
    },
    display_name="风险评分",
    category="finance",
)
print(node.id)  # uuid of the registered node
```

### 搜索与发现

```python
# 全文搜索
results = vault.search("资金风险", type="analysis")
for node in results:
    print(node.name, node.description)

# 列出所有 Node
nodes = vault.list_nodes(type="tool")
```

### 调用 Node

```python
response = vault.invoke("risk_score", input_data={"account_id": "ACC_001"})
print(response.output)       # {"score": 0.87}
print(response.latency_ms)   # 120
```

### 装饰器注册（推荐）

```python
@vault.node(
    name="detect_anomaly",
    type="analysis",
    description="检测异常交易",
    tags=["fraud"],
    endpoint="http://fraud-service/api/detect",
)
def detect_anomaly(transactions: list) -> dict:
    """函数类型注解自动生成 JSON Schema 并注册 Node"""
    pass
```

### 异步客户端（FastAPI / asyncio）

```python
import asyncio
from nodevault_sdk import AsyncNodeVaultClient

async def main():
    vault = AsyncNodeVaultClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
    )
    result = await vault.invoke("risk_score", input_data={"account_id": "ACC_001"})
    print(result.output)

asyncio.run(main())
```

### 异常处理

```python
from nodevault_sdk.exceptions import AuthError, NodeNotFoundError, NodeVaultError

try:
    result = vault.invoke("nonexistent_node", input_data={})
except NodeNotFoundError:
    print("Node 不存在")
except AuthError:
    print("认证失败，请检查 API Key")
except NodeVaultError as e:
    print(f"API 错误: {e}")
```

## 许可证

[Apache License 2.0](LICENSE)