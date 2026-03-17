# Phase 0 — 基础与规范

> **周期：约 2 周**
> **目标：为整个项目奠定不可动摇的地基——标准、规范、骨架**

---

## 核心思想

> 一个系统如果地基不稳，越往上建越危险。

Phase 0 不写任何业务逻辑，只做三件事：

1. 制定 **Node Schema 标准**（整个系统的契约）
2. 搭建 **项目骨架**（目录结构、配置、依赖）
3. 确立 **开发规范**（代码风格、提交规范、测试策略）

---

## 一、Node Schema 标准设计

这是 NodeVault 最核心的设计决策，必须在第一步就确定好。

### 1.1 Node 是什么

Node（节点）是 NodeVault 中最基本的单元，代表**一个可复用的 AI 能力**。

每个 Node 包含：
- 它能做什么（描述、输入、输出）
- 它在哪里（运行时地址）
- 它是谁的（归属、版本、标签）

### 1.2 完整 Node Schema（YAML 格式）

```yaml
# ===== 基本信息 =====
name: detect_fund_pool          # 唯一标识符，snake_case，全局唯一
version: "1.0.0"                # 语义化版本 SemVer: MAJOR.MINOR.PATCH
display_name: "资金池检测"       # 人类可读的展示名
description: |
  基于图算法检测交易数据中的可疑资金归集行为。
  输入原始交易流水，输出可疑账户列表及风险评分。

# ===== 分类与检索 =====
type: analysis                  # 枚举: data_cleaning | analysis | risk | nlp | vision | tool | utility
tags:
  - finance
  - risk
  - graph-algorithm
category: "风控分析"
keywords:                       # 用于全文搜索
  - 资金池
  - 反洗钱
  - AML

# ===== 归属信息 =====
author: "张三"
team: "RiskTeam"
email: "zhangsan@company.com"
namespace: "finance"            # 命名空间，用于多租户隔离

# ===== 输入输出契约 =====
input_schema:
  type: object
  required:
    - transactions
  properties:
    transactions:
      type: array
      description: "原始交易流水列表"
      items:
        type: object
        properties:
          tx_id:
            type: string
            description: "交易ID"
          from_account:
            type: string
          to_account:
            type: string
          amount:
            type: number
          timestamp:
            type: string
            format: date-time
    threshold:
      type: number
      description: "风险阈值，0-1之间，默认0.7"
      default: 0.7

output_schema:
  type: object
  properties:
    suspicious_accounts:
      type: array
      description: "可疑账户列表"
      items:
        type: string
    risk_scores:
      type: object
      description: "账户风险评分 Map"
      additionalProperties:
        type: number
    summary:
      type: string
      description: "检测结果摘要"

# ===== 运行时配置 =====
runtime:
  type: http                    # 枚举: http | grpc | docker | python | mcp
  endpoint: "http://risk-service.internal/api/v1/fund_pool_detect"
  method: POST                  # HTTP 方法
  headers:                      # 固定请求头
    Content-Type: application/json
    X-Service-Version: "1"
  auth:                         # 服务认证（可选）
    type: bearer                # none | bearer | api_key | basic
    token_env: RISK_SERVICE_TOKEN  # 从环境变量读取，不明文存储

# ===== 执行策略 =====
timeout: 30s                    # 调用超时
retry:
  max_attempts: 3
  backoff: exponential          # fixed | exponential
  initial_delay: 1s
rate_limit:
  max_calls_per_minute: 100

# ===== 依赖声明 =====
dependencies:
  - name: clean_transaction_data
    version: ">=1.0.0"          # 依赖的其他 Node

# ===== 元数据 =====
status: active                  # draft | active | deprecated | archived
visibility: internal            # public | internal | private
license: MIT
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-03-01T00:00:00Z"
```

### 1.3 Node 类型枚举

| 类型 | 说明 | 典型示例 |
|------|------|---------|
| `data_cleaning` | 数据清洗与预处理 | 去重、格式化、缺失值处理 |
| `analysis` | 数据分析与计算 | 资金流向分析、统计聚合 |
| `risk` | 风险评估与控制 | 风险评分、欺诈检测 |
| `nlp` | 自然语言处理 | 分词、情感分析、实体识别 |
| `vision` | 图像与视觉处理 | OCR、图像分类 |
| `ml` | 机器学习推理 | 模型预测、特征工程 |
| `tool` | 工具类能力 | 发邮件、发通知、写文件 |
| `utility` | 通用工具 | 格式转换、加解密 |

### 1.4 Runtime 类型说明

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| `http` | RESTful HTTP 调用 | Phase 1 优先实现，覆盖 90% 场景 |
| `grpc` | gRPC 调用 | 高性能内部服务 |
| `docker` | 容器直接执行 | 隔离性要求高的任务 |
| `python` | 内联 Python 函数 | 简单工具类节点 |
| `mcp` | MCP 协议调用 | 接入现有 MCP 服务器 |

---

## 二、项目骨架搭建

### 2.1 目录结构（Phase 0 初始化）

```
backend/
├── api/
│   ├── __init__.py
│   └── v1/
│       └── __init__.py
├── core/
│   └── __init__.py
├── models/
│   └── __init__.py
├── schemas/
│   └── __init__.py
├── database/
│   ├── __init__.py
│   └── session.py
├── auth/
│   └── __init__.py
├── tests/
│   ├── __init__.py
│   └── conftest.py
├── deploy/
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
├── alembic.ini
└── main.py
```

### 2.2 依赖清单（pyproject.toml）

```toml
[project]
name = "nodevault"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Web Framework
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",

    # Database
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.29.0",            # PostgreSQL async driver
    "alembic>=1.13.0",            # Database migrations

    # Validation
    "pydantic>=2.6.0",
    "pydantic-settings>=2.2.0",

    # Authentication
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",

    # HTTP Client (for Node invocation)
    "httpx>=0.27.0",

    # Utilities
    "python-dotenv>=1.0.0",
    "structlog>=24.1.0",          # Structured logging
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "httpx>=0.27.0",              # Test client
    "ruff>=0.3.0",                # Linter + Formatter
    "mypy>=1.9.0",
]
```

### 2.3 环境变量配置（.env.example）

```bash
# === 应用配置 ===
APP_ENV=development              # development | staging | production
APP_SECRET_KEY=change-me-in-production
APP_DEBUG=true
APP_PORT=8000

# === 数据库 ===
DATABASE_URL=postgresql+asyncpg://nodevault:password@localhost:5432/nodevault_db

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === JWT ===
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === 日志 ===
LOG_LEVEL=INFO
LOG_FORMAT=json                  # json | console

# === 外部服务认证（节点调用时如需认证）===
# RISK_SERVICE_TOKEN=xxx
# DATA_SERVICE_API_KEY=xxx
```

### 2.4 应用配置（settings.py）

```python
# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: Environment = Environment.DEVELOPMENT
    app_secret_key: str
    app_debug: bool = False
    app_port: int = 8000

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

settings = Settings()
```

---

## 三、核心数据库模型草图（Phase 0 确定，Phase 1 实现）

需要在 Phase 0 就规划好所有表结构，避免后续大规模重构。

### 3.1 ER 图

```
users (用户)
  ├── id, email, hashed_password, role, namespace_id
  └── 1:N → nodes（创建）

namespaces（命名空间/租户）
  ├── id, name, description
  └── 1:N → nodes

nodes（节点主表）
  ├── id, name, namespace_id, owner_id
  ├── display_name, description, type, category
  ├── status, visibility
  └── 1:N → node_versions

node_versions（节点版本）
  ├── id, node_id, version
  ├── input_schema (JSONB)
  ├── output_schema (JSONB)
  ├── runtime_config (JSONB)
  ├── is_default, is_deprecated
  └── created_at

node_tags（节点标签 多对多）
  ├── node_id
  └── tag

node_invocation_logs（调用日志）
  ├── id, node_id, version
  ├── invoked_by（user_id）
  ├── input_data (JSONB)
  ├── output_data (JSONB)
  ├── status (success | failure | timeout)
  ├── latency_ms
  ├── error_message
  └── created_at

workflows（工作流）
  ├── id, name, namespace_id
  └── 1:N → workflow_versions

workflow_versions（工作流版本）
  ├── id, workflow_id, version
  ├── dag_definition (JSONB)   # Phase 4 填充
  └── created_at

workflow_run_logs（工作流执行日志）
  ├── id, workflow_id
  ├── status, started_at, ended_at
  └── node_results (JSONB)
```

### 3.2 索引策略

```sql
-- 高频查询索引
CREATE INDEX idx_nodes_namespace ON nodes(namespace_id);
CREATE INDEX idx_nodes_status ON nodes(status);
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_node_tags_tag ON node_tags(tag);
CREATE INDEX idx_invocation_logs_node ON node_invocation_logs(node_id, created_at DESC);

-- GIN 索引用于 JSONB 搜索
CREATE INDEX idx_node_versions_input_schema ON node_versions USING GIN (input_schema);
```

---

## 四、开发规范

### 4.1 分支策略

```
main          ← 生产分支，只接受 merge request
  └── develop ← 开发主分支
        ├── feature/phase1-node-registry
        ├── feature/phase2-sdk
        └── fix/node-invocation-timeout
```

### 4.2 提交消息规范（Conventional Commits）

```
<type>(<scope>): <description>

type:
  feat     - 新功能
  fix      - Bug 修复
  refactor - 代码重构
  docs     - 文档
  test     - 测试
  chore    - 构建/工具

示例:
  feat(registry): add node version management API
  fix(runtime): handle HTTP timeout correctly
  docs(schema): update Node Schema v1.1
```

### 4.3 代码规范

- **Formatter**: `ruff format`（替代 black）
- **Linter**: `ruff check`
- **Type Check**: `mypy --strict`
- **行宽**: 88 字符
- **命名**: 
  - 类名: `PascalCase`
  - 函数/变量: `snake_case`
  - 常量: `UPPER_SNAKE_CASE`
  - API 路径: `kebab-case`

### 4.4 测试策略

| 测试类型 | 工具 | 覆盖目标 |
|---------|------|---------|
| 单元测试 | pytest | 所有 core/ 业务逻辑 |
| 集成测试 | pytest + TestClient | 所有 API 端点 |
| E2E 测试 | pytest + Docker | 完整调用链路 |
| 目标覆盖率 | pytest-cov | ≥ 80% |

### 4.5 API 设计规范

```
# URL 规范
GET    /api/v1/nodes                    # 列表
POST   /api/v1/nodes                    # 创建
GET    /api/v1/nodes/{node_id}          # 详情
PUT    /api/v1/nodes/{node_id}          # 完整更新
PATCH  /api/v1/nodes/{node_id}          # 部分更新
DELETE /api/v1/nodes/{node_id}          # 删除（软删除）

# 版本资源
GET    /api/v1/nodes/{node_id}/versions
POST   /api/v1/nodes/{node_id}/versions
GET    /api/v1/nodes/{node_id}/versions/{version}

# 子资源
POST   /api/v1/nodes/{node_id}/invoke   # 调用执行
GET    /api/v1/nodes/{node_id}/logs     # 调用日志

# 统一响应格式
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "request_id": "uuid"
}

# 错误响应格式
{
  "success": false,
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "节点 detect_fund_pool 不存在",
    "details": { ... }
  },
  "request_id": "uuid"
}
```

---

## 五、Docker Compose 开发环境

```yaml
# deploy/docker-compose.dev.yml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nodevault
      POSTGRES_PASSWORD: password
      POSTGRES_DB: nodevault_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  meilisearch:
    image: getmeili/meilisearch:v1.7
    ports:
      - "7700:7700"
    environment:
      MEILI_MASTER_KEY: dev-master-key
    volumes:
      - meili_data:/meili_data

volumes:
  postgres_data:
  meili_data:
```

---

## 六、Phase 0 交付检查清单

```
□ Node Schema v1.0 文档定稿（本文档）
□ 数据库 ER 图确认
□ 项目 pyproject.toml 配置完成
□ .env.example 配置完成
□ docker-compose.dev.yml 可正常启动
□ 目录骨架创建完成
□ main.py 可以启动（返回 200 健康检查）
□ 开发规范文档输出
□ 初始 Alembic 迁移文件生成
□ 基础 CI 配置（GitHub Actions lint + test）
```

---

## 七、快速启动命令

```bash
# 1. 克隆并进入项目
git clone https://github.com/your-org/nodevault.git
cd nodevault

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -e ".[dev]"

# 4. 启动基础设施
docker compose -f deploy/docker-compose.dev.yml up -d

# 5. 复制环境变量
cp .env.example .env

# 6. 运行数据库迁移
alembic upgrade head

# 7. 启动服务
uvicorn main:app --reload --port 8000

# 8. 访问文档
# http://localhost:8000/docs
```

---

> **下一步 →** [Phase 1 - MVP 核心功能](./Phase1-MVP核心功能.md)
