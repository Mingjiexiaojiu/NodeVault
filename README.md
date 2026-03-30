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

NodeVault 是一个帮助企业 **把分散的 AI 能力整理起来，并安全提供给人和 Agent 使用** 的平台。

很多公司并不缺 AI 能力，真正缺的是：

- 不知道公司里已经有哪些能力可以用
- 知道有服务，但不知道谁维护、怎么接入
- 每接一个服务都要重新处理认证、调用和适配
- Agent 想调用内部工具时，没有统一的入口

NodeVault 就是为了解决这些问题而存在。

它不去替代已有服务，而是把现有的模型接口、算法服务、内部工具 API 统一登记成一个个可管理的能力项，也就是 **Node**。这样无论是人、业务系统，还是 AI Agent，都可以通过同一个平台去发现和使用这些能力。

可以把它理解成企业内部 AI 能力的“总入口”：

- 对外，提供统一目录、统一调用入口、统一权限和统一导出方式
- 对内，连接真实服务，负责请求转发、认证处理、调用记录和结果追踪

一句话说，NodeVault 解决的不是“怎么做模型”，而是“怎么让已经存在的 AI 能力真正被全公司复用起来”。

```
你们团队的服务                       任何使用方

风控评分模型  ──┐                ┌── 业务系统
数据清洗服务  ──┤                ├── AI Agent
NLP 文本分析  ──┼── NodeVault ──▶──┼── ChatGPT 插件
OCR 识别服务  ──┘  统一注册入口   └── 自动化工作流
```

---

## 它能解决什么问题？

如果把企业里的 AI 能力看成一批“已经建好的机器”，那大多数公司的问题不是没有机器，而是这些机器：

- 散落在不同团队，彼此不知道对方存在
- 使用方式各不相同，新人很难快速接手
- 认证方式复杂，调用经常卡在 token、账号、权限上
- 对人来说能勉强看文档接入，对 Agent 来说几乎不可直接使用

NodeVault 主要解决下面几类问题：

| 常见问题 | NodeVault 怎么处理 |
|----------|-------------------|
| 公司内部有哪些 AI 服务可以用，没人说得清 | 提供统一的能力目录，集中展示所有已注册 Node |
| 同类能力被重复开发 | 把能力沉淀为可复用资产，注册一次，重复使用 |
| 新接一个服务成本很高 | 提供统一调用入口，尽量屏蔽底层差异 |
| 下游 token 容易过期，调用经常失败 | 平台统一管理凭据，并在需要时自动刷新认证 |
| 有服务文档，但很难快速转成可用能力 | 可探测接口描述并转换成候选 Node |
| 想让 Claude、Copilot、MCP 客户端直接使用内部能力 | 可把节点组合成 Skill 并导出为 Agent 可消费的能力包 |
| 无法统计某个能力是否稳定、谁在使用 | 记录调用日志、状态、耗时与结果 |

对不懂底层实现的使用者来说，可以把 NodeVault 理解成一层“能力翻译器 + 调度中心”：

- 它把分散的服务整理成统一清单
- 它把复杂的调用方式收敛成统一入口
- 它把原本只适合工程师阅读的接口，变成 Agent 也能使用的工具能力

---

## 它是怎么工作的？

从访客视角看，NodeVault 的工作方式其实很直观，可以概括成四步：

### 1. 找到现有服务

企业里已经存在很多服务，只是平时分散在不同系统中。NodeVault 可以帮助团队发现这些服务，并读取它们的接口描述。

### 2. 挑出真正值得复用的能力

不是所有接口都值得暴露出去。NodeVault 会把探测到的接口整理成候选项，团队可以从中挑选真正有业务价值的部分，注册成 Node。

你可以把 Node 理解成一个“已经整理好、可被复用的能力入口”。

### 3. 由平台代为调用真实服务

使用方不必直接对接底层系统，而是先请求 NodeVault，再由 NodeVault 去调用真正的服务。

```text
使用方 / Agent
  -> 请求 NodeVault
  -> NodeVault 找到对应能力
  -> NodeVault 代为连接真实服务
  -> 返回结果并记录过程
```

这样做的好处是，调用方面对的是统一入口，而不是一堆风格不同、认证方式不同的内部接口。

### 4. 进一步整理成可被 Agent 使用的 Skill

当平台里已经有多个 Node 时，可以把其中一组相关能力组合成一个 Skill，再导出给 Claude、Copilot、MCP 客户端或其他 Agent 框架使用。

这一步的意义是：让企业内部能力不只是“可调用”，而是进一步变成“可被 Agent 理解和使用”。

---

## 为什么它对 Agent 场景特别有价值？

人接系统时，碰到认证复杂、文档零散、接口风格不统一，通常还能慢慢排查；但 Agent 不适合处理这些碎片化细节。

NodeVault 的价值就在这里：它把 Agent 最不擅长的那部分工作收走了。

比如一个 Agent 想调用企业内部服务时，常见流程往往是：

- 先找到接口
- 再确认参数格式
- 处理 API Key 或 token
- token 过期后重新登录
- 失败后重新请求

如果这些都交给 Agent 自己处理，稳定性会很差。

而在 NodeVault 里，外部看到的会更简单：

- Agent 只需要向 NodeVault 发请求
- NodeVault 负责找到正确的节点服务
- NodeVault 负责携带凭据和认证信息
- 如果下游 token 失效，NodeVault 会自动重新获取并再次发送请求

对访客来说，可以直接把它理解成：

**NodeVault 让企业内部服务更像“随取随用的工具”，而不是一堆难以直接接入的内部接口。**

---

## Skills 相关能力

NodeVault 的 Skill 不是给单个接口换个名字，而是把一组相关能力整理成一个更适合 Agent 使用的“能力包”。

### Skill 的价值

- 把多个相关 Node 归并到一个任务场景里
- 让 Agent 更容易理解“这组能力是拿来做什么的”
- 支持版本化管理，减少后续变更对使用方的影响
- 可以导出到 Claude、Copilot、MCP 等常见 Agent 生态

### Skill 的形成方式

1. 先通过手工注册或服务探针发现接口
2. 将探测出的接口按需转换成 Node
3. 从现有 Node 中挑选一部分加入某个 Skill
4. 为 Skill 生成版本快照和 `SKILL.md`
5. 导出为 skill 能力包，供外部 Agent 集成

如果用更容易理解的话来说，这条链路就是：

```text
原始服务
  -> 整理成可复用节点
  -> 组合成 Skill
  -> 导出给 Agent 使用
```

这也是 NodeVault 和普通 API 管理工具的区别之一：它不只是记录接口，而是把企业内部能力进一步整理成 **可被 Agent 直接消费的工具资产**。

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

## 谁适合用 NodeVault？

- **AI 平台团队**：希望把企业内部 AI 能力统一沉淀下来
- **Agent / Workflow 团队**：希望让 Agent 稳定调用内部工具，而不是自己处理一堆接入细节
- **业务开发团队**：希望快速复用现有能力，减少重复造轮子
- **数据科学 / 算法团队**：希望把已有模型和算法服务更容易地提供给其他团队使用
- **治理与架构团队**：希望对 AI 能力资产做统一管理、审计和授权

---

## 一个典型使用场景

假设一家公司已经有三个现成服务：

- 风控评分服务
- OCR 识别服务
- 文本摘要服务

传统做法通常是每个调用方分别：

- 找人要接口文档
- 自己处理 token
- 自己写请求封装
- 自己维护失败重试和字段适配

在 NodeVault 中，可以这样做：

1. 通过探针发现这些服务的 OpenAPI
2. 从接口列表中选出真正有价值的操作，注册成 Node
3. 为这些服务配置凭据和鉴权方式
4. Agent 统一向 NodeVault 发起调用
5. NodeVault 自动将请求转发到对应节点，必要时自动换 token
6. 再从这些 Node 中选择一部分，打包成一个风险审核或文档处理 Skill
7. 导出给 Claude、Copilot 或 MCP 客户端直接使用

最终得到的，不再是一堆零散接口，而是一套：

- 找得到
- 接得上
- 调得通
- 管得住
- 能给 Agent 直接使用

的企业 AI 能力资产。

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
