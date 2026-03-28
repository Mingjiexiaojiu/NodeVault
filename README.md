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

NodeVault 是一个帮助团队**统一管理和共享 AI 能力**的平台。

企业里往往有很多 AI 服务和算法——风险评分、数据清洗、文本分析……它们散落在各个团队、各个系统里，互相不知道对方的存在，重复开发的情况时有发生。NodeVault 把这些能力统一汇聚到一个地方，让所有人都能轻松找到并使用。

```
你们团队的服务                       任何使用方

风控评分模型  ──┐                ┌── 业务系统
数据清洗服务  ──┤                ├── AI Agent
NLP 文本分析  ──┼── NodeVault ──▶──┼── ChatGPT 插件
OCR 识别服务  ──┘  统一注册入口   └── 自动化工作流
```

---

## 它能解决什么问题？

| 你遇到的问题 | NodeVault 的做法 |
|------------|----------------|
| 不知道公司内部有哪些 AI 服务可以用 | 提供统一的能力目录，支持搜索和筛选 |
| 同样的功能各团队各写一份 | 注册一次，全公司共享复用 |
| 接入一个内部服务要花好几天对接 | 统一调用接口，开箱即用 |
| 不清楚某个服务谁在用、用了多少次 | 完整的调用记录和使用统计 |
| AI Agent 想调用内部工具，不知道怎么接 | 自动生成 OpenAI / Claude 格式的工具定义 |

---

## 主要功能

- **🗂 能力注册** — 将你的服务或算法注册为一个标准化的「节点」，填写名称、描述、接口地址即可
- **🔍 能力发现** — 关键词搜索、标签筛选，快速找到你需要的服务
- **▶️ 统一调用** — 不管底层是什么语言、什么框架，用同一种方式调用
- **📊 使用统计** — 查看每个服务被调用了多少次、成功率如何、响应时间怎样
- **🤖 AI 接入** — 一键导出为 OpenAI Function Calling / Claude MCP / LangChain 工具格式
- **🔐 权限管理** — 按部门划分权限，谁能看、谁能调用、谁能管理，清晰可控
- **🔑 服务凭据** — 统一管理调用下游服务所需的账号密码和 Token，NodeVault 自动处理鉴权

---

## 谁适合用 NodeVault？

- **AI 产品团队** — 想把多个 AI 能力组合起来，构建复杂的处理流程
- **平台/基础设施团队** — 负责管理和治理企业内的 AI 服务资产
- **业务开发团队** — 想直接调用现有的 AI 能力，而不是从零开始
- **数据科学团队** — 想把训练好的模型对外提供服务，供其他系统使用

---

## 快速体验

### 方式一：使用网页界面（推荐新用户）

1. 打开浏览器，访问 `http://localhost:5173`（本地部署后）
2. 注册账号，选择或加入一个部门
3. 进入「节点」页面，浏览已有的服务能力
4. 点击「发现」，导入你自己的服务

→ 详细操作步骤请查看 **[用户使用手册](USAGE.md)**

### 方式二：本地启动

```bash
# 1. 启动数据库等基础设施
docker compose -f deploy/docker-compose.dev.yml up -d

# 2. 启动后端
python -m venv .venv && .venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
alembic upgrade head
uvicorn backend.main:app --reload --port 8000

# 3. 启动前端
cd frontend
pnpm install
pnpm dev
```

访问 `http://localhost:5173` 开始使用。

> 初始超级管理员账号请参考 `.env.example` 中的配置说明。

---

## 文档

| 文档 | 说明 |
|-----|------|
| [用户使用手册](USAGE.md) | 面向普通用户的完整操作指南，包含网页界面和 Python SDK 的使用说明 |
| [贡献指南](CONTRIBUTING.md) | 如何参与项目开发 |
| [API 文档](http://localhost:8000/docs) | 在线接口文档（启动服务后可访问） |

---

## 许可证

[Apache License 2.0](LICENSE)
