# NodeVault 整体规划总览

> **Enterprise AI Capability Registry — 企业级 AI 能力注册中心**

---

## 一、项目愿景

NodeVault 的终极目标是成为企业 AI 工程体系的**能力底座**——所有可复用的 AI 处理能力（数据清洗、分析算法、风险模型、NLP 服务……）都以标准化"节点 (Node)"的形式沉淀在这里，供任何 Agent、Workflow、业务系统按需发现、调用、组合。

一句话定位：

```
NodeVault = npm（能力仓库） + Airflow（编排引擎） + AI Tool Registry（Agent接入层）
```

区别于 Dify / LangChain 这类 **AI 应用平台**，NodeVault 专注于更底层的：

```
能力基础设施（Capability Infrastructure）
```

---

## 二、核心设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | NodeVault 只管理能力元数据与调度，不做业务计算 |
| **标准先行** | Node Schema 是整个系统的契约，设计需足够稳定 |
| **渐进演进** | 每个阶段都能独立交付价值，不依赖下一阶段 |
| **企业级优先** | 认证、权限、审计、多租户从一开始就纳入设计 |
| **开放生态** | 导出标准兼容 OpenAI / LangChain / MCP / Agno 等主流 Agent 框架 |

---

## 三、里程碑总览

```
Phase 0  ──▶  Phase 1  ──▶  Phase 2  ──▶  Phase 3  ──▶  Phase 4  ──▶  Phase 5  ──▶  Phase 6
 基础规范       MVP核心        发现&SDK       Skill导出      Workflow        企业治理        生态开源
  (2周)        (6周)          (5周)          (5周)          (8周)            (6周)           (持续)
```

| 阶段 | 名称 | 核心交付物 | 里程碑意义 |
|------|------|-----------|-----------|
| **Phase 0** | 基础与规范 | Node Schema 标准、项目骨架、开发规范 | 所有后续阶段的地基 |
| **Phase 1** | MVP 核心功能 | 节点注册/查询/调用 REST API、数据库、JWT 认证 | 系统可以真正运行 |
| **Phase 2** | 能力发现与 SDK | 全文搜索、版本管理、Python SDK、OpenAPI 文档 | 开发者可以方便接入 |
| **Phase 3** | Skill 导出与 Agent 集成 | OpenAI / LangChain / MCP Tool 导出、Agent 自动发现 | AI Agent 可以直接使用 NodeVault |
| **Phase 4** | Workflow 编排引擎 | DAG 定义、串/并行执行、Workflow 版本控制 | 多节点能力可以被编排组合 |
| **Phase 5** | 企业级治理 | RBAC、多租户、OpenTelemetry 可观测、限流计费 | 可真正上企业生产环境 |
| **Phase 6** | 生态建设与开源 | Marketplace、多语言 SDK、Helm Chart、文档站 | 社区级影响力 |

---

## 四、系统最终架构全景

```
┌─────────────────────────────────────────────────────────────────────┐
│                         外部接入层                                    │
│   AI Agent    │   Business App    │   Workflow Trigger   │   Dev    │
└───────┬───────┴─────────┬─────────┴──────────┬───────────┴────┬─────┘
        │                 │                    │                │
        ▼                 ▼                    ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                  │
│              认证 / 限流 / 路由 / 审计日志                            │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
        ┌─────────────────────────┼──────────────────────────┐
        ▼                         ▼                          ▼
┌──────────────┐        ┌──────────────────┐       ┌──────────────────┐
│ Node Registry│        │  Workflow Engine  │       │  Skill Exporter  │
│              │        │                  │       │                  │
│ 注册/查询/   │        │  DAG 定义/执行/  │       │ OpenAI Tool      │
│ 版本/标签    │        │  历史/版本控制   │       │ LangChain Tool   │
└──────┬───────┘        └────────┬─────────┘       │ MCP Tool         │
       │                         │                 │ Agent Skill      │
       ▼                         ▼                 └──────────────────┘
┌──────────────┐        ┌──────────────────┐
│ Node Runtime │        │  Task Scheduler  │
│              │        │  (Celery/Redis)  │
│ HTTP/gRPC/   │        └──────────────────┘
│ Docker       │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    外部能力服务                                     │
│  Python API  │  Java API  │  ML Service  │  数据清洗  │  风控模型  │
└──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────┐
│                    数据与可观测层                                   │
│  PostgreSQL  │  Redis  │  Elasticsearch  │  Prometheus  │  Grafana │
└──────────────────────────────────────────────────────────────────┘
```

---

## 五、技术栈选型总结

| 层级 | 技术 | 理由 |
|------|------|------|
| **Web 框架** | FastAPI (Python) | 异步高性能、AI 生态最成熟、OpenAPI 自动生成 |
| **主数据库** | PostgreSQL | 结构化元数据存储、JSONB 支持 Schema 字段、事务能力强 |
| **搜索引擎** | MeiliSearch（Phase 2）→ Elasticsearch（Phase 5+） | 前期轻量快速，后期全功能 |
| **缓存 / 消息** | Redis | 缓存热点 Node、Celery 任务队列 |
| **任务队列** | Celery | 异步 Node 调用、批量执行 |
| **认证授权** | FastAPI-Users + JWT | 标准 Bearer Token，后期对接 OAuth2 |
| **可观测性** | OpenTelemetry + Prometheus + Grafana | 工业标准追踪链路 |
| **容器化** | Docker + Docker Compose → Kubernetes | 本地开发简单，生产可 K8s 部署 |
| **Python SDK** | httpx + pydantic | 类型安全、异步支持 |
| **文档** | MkDocs Material | 好看的开源文档站 |

---

## 六、项目目录骨架（最终形态）

```
backend/
├── api/                    # FastAPI 路由层
│   ├── v1/
│   │   ├── nodes.py        # Node CRUD
│   │   ├── invoke.py       # 调用执行
│   │   ├── workflows.py    # Workflow 管理
│   │   ├── export.py       # Skill 导出
│   │   └── admin.py        # 治理接口
│   └── deps.py             # 依赖注入
│
├── core/                   # 核心业务逻辑
│   ├── registry.py         # 节点注册与发现
│   ├── runtime.py          # 节点执行引擎
│   ├── discovery.py        # 能力搜索
│   └── versioning.py       # 版本管理
│
├── workflow/               # 工作流引擎
│   ├── dag.py              # DAG 定义
│   ├── executor.py         # DAG 执行器
│   └── scheduler.py        # 调度器
│
├── exporter/               # Skill 导出
│   ├── openai.py
│   ├── langchain.py
│   ├── mcp.py
│   └── skill_package.py
│
├── sdk/                    # Python SDK（独立包）
│   ├── client.py
│   ├── decorator.py
│   └── models.py
│
├── models/                 # SQLAlchemy ORM 模型
│   ├── node.py
│   ├── workflow.py
│   ├── invocation.py
│   └── user.py
│
├── schemas/                # Pydantic 数据模型
│   ├── node.py
│   ├── workflow.py
│   └── user.py
│
├── database/               # 数据库配置
│   ├── session.py
│   └── migrations/         # Alembic 迁移文件
│
├── auth/                   # 认证授权
│   ├── jwt.py
│   └── rbac.py
│
├── observability/          # 可观测性
│   ├── tracing.py
│   └── metrics.py
│
├── tests/                  # 测试
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                   # 文档
├── deploy/                 # 部署配置
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── helm/
│
└── main.py                 # 应用入口
```

---

## 七、文档索引

| 文件 | 内容 |
|------|------|
| [Phase0-基础与规范.md](./Phase0-基础与规范.md) | Node Schema 标准、项目骨架搭建、开发规范 |
| [Phase1-MVP核心功能.md](./Phase1-MVP核心功能.md) | 节点注册/查询/调用 API、数据库设计、JWT 认证 |
| [Phase2-能力发现与SDK.md](./Phase2-能力发现与SDK.md) | 全文搜索、版本管理、标签系统、Python SDK |
| [Phase3-Skill导出与Agent集成.md](./Phase3-Skill导出与Agent集成.md) | OpenAI/LangChain/MCP 导出、Agent 自动发现 |
| [Phase4-Workflow编排引擎.md](./Phase4-Workflow编排引擎.md) | DAG 定义与执行、串并行、历史记录 |
| [Phase5-企业级治理.md](./Phase5-企业级治理.md) | RBAC、多租户、可观测性、限流计费 |
| [Phase6-生态建设与开源.md](./Phase6-生态建设与开源.md) | Marketplace、多语言 SDK、Helm、文档站 |
