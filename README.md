<div align="center">

<img src="docs/assets/NodeVault.png" alt="NodeVault" width="480" />

**企业级 AI 能力注册中心**

注册一次，处处调用

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com)

</div>

---

## NodeVault 是什么？

NodeVault 是企业内部 AI 能力的**统一注册中心**——把分散的模型接口、算法服务、内部工具 API 登记为可管理的能力项（**Node**），让人、业务系统和 AI Agent 通过同一个平台发现和使用。

它解决的不是"怎么做模型"，而是**怎么让已有的 AI 能力真正被全公司复用起来**。

```
你们团队的服务                       任何使用方

风控评分模型  ──┐                ┌── 业务系统
数据清洗服务  ──┤                ├── AI Agent
NLP 文本分析  ──┼── NodeVault ──▶──┼── ChatGPT 插件
OCR 识别服务  ──┘  统一注册入口   └── 自动化工作流
```

---

## 它能解决什么问题？

| 常见痛点 | NodeVault 怎么处理 |
|----------|-------------------|
| 内部有哪些 AI 服务可用，没人说得清 | 统一能力目录，集中展示所有已注册 Node |
| 同类能力被重复开发 | 注册一次，重复使用 |
| 新接一个服务成本很高 | 统一调用入口，屏蔽底层差异 |
| Token 过期、认证复杂 | 平台统一管理凭据，自动刷新认证 |
| 有 API 文档但难以快速转成可用能力 | 探测接口描述，转换为候选 Node |
| Agent 无法直接使用内部能力 | Node 组合成 Skill，导出为 Agent 可消费的能力包 |
| 不知道能力是否稳定、谁在使用 | 记录调用日志、状态、耗时与结果 |

---

## 它是怎么工作的？

### 1. 发现服务

通过服务探针或手工注册，发现企业内已有的 API 并读取接口描述。

### 2. 注册为 Node

从探测到的接口中挑选有业务价值的部分，注册成 **Node**——一个整理好的、可被复用的能力入口。

### 3. 统一代理调用

使用方只需请求 NodeVault，平台负责路由到真实服务、携带凭据、处理认证，并记录调用过程。

```text
使用方 / Agent → NodeVault → 真实服务 → 返回结果
```

这对 Agent 尤其重要：接口寻址、参数适配、token 管理、失败重试全部由平台代管，Agent 只需发请求、拿结果。

### 4. 组合为 Skill，导出给 Agent

将多个相关 Node 组合成面向任务的 **Skill**，支持版本化管理，可导出给 Claude、Copilot、MCP 客户端等 Agent 框架直接使用。

```text
原始服务 → Node → Skill → Agent 消费
```

这也是 NodeVault 和普通 API 管理工具的区别：它不只记录接口，而是把能力整理成 **Agent 可直接消费的工具资产**。

---

## 主要功能

- **🗂 能力登记**：把零散服务整理成统一的 Node 目录
- **🔎 能力发现**：通过搜索、筛选和探针找到可复用能力
- **▶️ 统一调用**：对外提供一致的调用入口
- **🔑 认证代管**：统一处理 API Key、Token 和登录换 token 等流程
- **📊 调用追踪**：记录谁在用、是否成功、耗时如何
- **🤖 Agent 集成**：导出为 OpenAI Function Calling、LangChain、MCP 等格式
- **📦 Skill 打包**：把多个 Node 组合成面向任务的能力包
- **🔐 权限治理**：按角色、部门和可见性控制访问范围

---

## 谁适合用？

- **AI 平台团队**：统一沉淀企业 AI 能力
- **Agent / Workflow 团队**：让 Agent 稳定调用内部工具，无需自行处理接入细节
- **业务开发团队**：快速复用现有能力，减少重复造轮子
- **算法团队**：让模型和算法服务更容易被其他团队使用
- **治理与架构团队**：对 AI 能力资产做统一管理、审计和授权

---

## 典型场景

公司已有风控评分、OCR 识别、文本摘要三个服务，传统做法是每个调用方各自找文档、处理 token、写请求封装。

用 NodeVault：

1. 探针发现服务 OpenAPI，注册为 Node
2. 配置凭据和鉴权方式
3. 使用方统一通过 NodeVault 调用，平台自动转发和换 token
4. 选择部分 Node 打包成 Skill，导出给 Claude / Copilot / MCP 客户端

最终：**找得到、接得上、调得通、管得住、Agent 能直接用。**

---

## 快速体验

### 方式一：Docker 部署（推荐生产 / 服务器）

确保服务器上已有 PostgreSQL、Redis、MeiliSearch。

**第一步：在本地构建前端**

```bash
cd frontend && npm install && npm run build && cd ..
```

**第二步：将以下文件打包后上传到服务器**

```
NodeVault/
├── deploy/
│   └── Dockerfile          # 镜像构建文件
├── backend/                # 后端源码（整个目录）
├── frontend/
│   └── dist/               # 前端构建产物（只需 dist，不需要 src）
├── docker-compose.yml      # 编排文件
├── pyproject.toml          # Python 依赖清单
├── alembic.ini             # 数据库迁移配置
└── .env.example            # 环境变量模板（上传后改名为 .env 并填写）
```

> `frontend/src`、`frontend/node_modules`、`.git`、`__pycache__`、`.venv` **不需要**上传。

打包命令参考：

```bash
zip -r nodevault.zip \
  deploy/ backend/ frontend/dist/ \
  docker-compose.yml pyproject.toml alembic.ini .env.example
```

**第三步：在服务器上配置并启动**

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env，填写数据库连接地址和各项密钥

# 构建依赖镜像（首次或 pyproject.toml 变更后执行）
docker compose build

# 启动
docker compose up -d

# 初始化数据库（首次执行一次）
docker compose exec app alembic upgrade head
```

访问 `http://your-server:8000` 开始使用。

> 详细说明请查看 **[用户使用手册](USAGE.md)**

---

### 方式二：本地开发启动

需要本地已运行 PostgreSQL、Redis、MeiliSearch，并在 `.env` 中配置好连接地址。

```bash
# 1. 安装后端依赖并启动
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env   # 填写本地服务连接地址
alembic upgrade head
uvicorn backend.main:app --reload --port 8000

# 2. 启动前端开发服务器（另开终端）
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 开始使用（前端开发服务器）。

> 初始超级管理员账号请参考 `.env.example` 中的配置说明。

---

## 文档

| 文档 | 说明 |
|-----|------|
| [用户使用手册](USAGE.md) | 面向普通用户的完整操作指南，包含网页界面和 Python SDK 的使用说明 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目开发 |
| [API 文档](http://localhost:8000/docs) | 在线接口文档（启动服务后可访问） |

### 部署相关文件

| 文件 | 说明 |
|-----|------|
| `docker-compose.yml` | Docker 编排文件，一条命令启动应用 |
| `deploy/Dockerfile` | 应用镜像构建文件（预装所有 Python 依赖，代码运行时挂载） |
| `.env.example` | 环境变量模板，复制为 `.env` 后填写即可 |

---

## 许可证

[Apache License 2.0](LICENSE)
