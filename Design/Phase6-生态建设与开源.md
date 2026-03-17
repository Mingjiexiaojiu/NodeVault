# Phase 6 — 生态建设与开源

> **周期：持续进行（无固定截止）**
> **目标：让 NodeVault 成为一个有社区、有影响力的开源项目，构建 AI 能力生态**

---

## 核心思想

> 一个好的开源项目，不只是好代码，更是一个让人愿意参与的生态。

Phase 6 不是软件开发的终点，而是一个新旅程的起点。这个阶段的目标是：

```
让世界上任何人都能用 NodeVault
让任何人都能为 NodeVault 贡献能力
让 NodeVault 成为 AI 能力基础设施的事实标准
```

---

## 一、Capability Marketplace（能力市场）

这是 Phase 6 最核心的功能：让用户可以分享、发现、安装来自社区的 Node。

### 1.1 Marketplace 架构

```
NodeVault Marketplace（公共）
       │
  ┌────┴──────────────────────────────┐
  │  分类浏览  │  搜索  │  评分  │ 安装 │
  └────┬──────────────────────────────┘
       │
       ▼
  Node Package（可安装的能力包）
       │
       ├── 官方包（NodeVault 团队维护）
       ├── 认证包（社区贡献，经过审核）
       └── 社区包（任何人发布，未经审核）

       ▼ 安装
 用户的私有 NodeVault 实例
```

### 1.2 Node Package 格式

一个可发布到 Marketplace 的 Node Package：

```
detect-fund-pool-1.0.0.nvpkg
├── manifest.json         # 包声明
├── node.yaml             # Node 定义
├── README.md             # 使用说明
├── CHANGELOG.md          # 版本历史
├── LICENSE
└── examples/
    ├── example_input.json
    └── example_output.json
```

```json
// manifest.json
{
  "package_id": "risk-team.detect-fund-pool",
  "package_name": "detect-fund-pool",
  "version": "1.0.0",
  "author": "risk-team",
  "license": "MIT",
  "homepage": "https://github.com/risk-team/nodevault-detect-fund-pool",
  "keywords": ["finance", "risk", "aml"],
  "nodevault_version": ">=1.0.0",
  "node_name": "detect_fund_pool",
  "requires_runtime_endpoint": true,
  "rating": null    // 由 Marketplace 填充
}
```

### 1.3 Marketplace API

```
# 发布
POST   /marketplace/publish            # 发布 Node Package
POST   /marketplace/publish/{id}/versions  # 发布新版本

# 浏览
GET    /marketplace/packages           # 浏览所有包（支持分类/搜索/排序）
GET    /marketplace/packages/{id}      # 包详情（含安装量、评分、README）
GET    /marketplace/categories         # 分类列表
GET    /marketplace/featured           # 精选推荐

# 安装
POST   /marketplace/install/{package_id}  # 一键安装到当前私有实例
POST   /marketplace/install/{package_id}/versions/{version}

# 社区
POST   /marketplace/packages/{id}/rate   # 评分（1-5）
POST   /marketplace/packages/{id}/review # 评论

# 我的发布
GET    /marketplace/my-packages        # 我发布的所有包
```

### 1.4 Marketplace 前端 UI

```
NodeVault Marketplace

┌────────────────────────────────────────────────────┐
│  🔍 搜索能力...               [分类 ▾] [排序 ▾]   │
├────────────────────────────────────────────────────┤
│  🏷️ 热门标签: finance  risk  nlp  data  vision    │
├────────────────────────────────────────────────────┤
│                                                    │
│  🌟 精选能力                                       │
│  ┌───────────────┐ ┌───────────────┐              │
│  │detect-fund-   │ │risk-score     │              │
│  │pool           │ │               │              │
│  │⭐4.8  ↓1.2k  │ │⭐4.6  ↓ 890  │              │
│  │[安装]         │ │[安装]         │              │
│  └───────────────┘ └───────────────┘              │
│                                                    │
│  📦 全部能力（128个）                               │
│  ...                                              │
└────────────────────────────────────────────────────┘
```

---

## 二、多语言 SDK

为了让更多开发者能方便接入 NodeVault，Phase 6 提供多语言 SDK。

### 2.1 SDK 路线图

| 语言 | 优先级 | 状态 |
|------|--------|------|
| Python | P0（Phase 2 已完成） | ✅ 已有 |
| TypeScript/JavaScript | P0 | Phase 6 优先 |
| Java | P1 | Phase 6 |
| Go | P2 | Phase 6 |
| Rust | P3 | 社区贡献 |

### 2.2 TypeScript SDK 设计

```typescript
// nodevault-sdk/index.ts

export interface NodeResponse {
  id: string;
  name: string;
  description?: string;
  type: string;
  tags: string[];
  status: string;
  defaultVersion?: string;
}

export interface InvokeResponse {
  nodeName: string;
  version: string;
  output: Record<string, unknown>;
  latencyMs: number;
  invocationId: string;
}

export class NodeVaultClient {
  private baseUrl: string;
  private token: string;

  constructor(options: { baseUrl: string; apiKey?: string; token?: string }) {
    this.baseUrl = options.baseUrl.replace(/\/$/, "");
    this.token = options.apiKey || options.token || "";
  }

  private get headers(): Record<string, string> {
    return {
      "Authorization": `Bearer ${this.token}`,
      "Content-Type": "application/json",
    };
  }

  async register(node: {
    name: string;
    type: string;
    description?: string;
    tags?: string[];
    version?: string;
    inputSchema: Record<string, unknown>;
    outputSchema: Record<string, unknown>;
    endpoint: string;
  }): Promise<NodeResponse> {
    const resp = await fetch(`${this.baseUrl}/api/v1/nodes`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({
        name: node.name,
        type: node.type,
        description: node.description,
        tags: node.tags ?? [],
        version: node.version ?? "1.0.0",
        input_schema: node.inputSchema,
        output_schema: node.outputSchema,
        runtime: { type: "http", endpoint: node.endpoint },
      }),
    });
    const data = await resp.json();
    return data.data;
  }

  async invoke(
    nodeName: string,
    input: Record<string, unknown>,
    version?: string,
  ): Promise<InvokeResponse> {
    const node = await this.get(nodeName);
    const resp = await fetch(`${this.baseUrl}/api/v1/nodes/${node.id}/invoke`, {
      method: "POST",
      headers: this.headers,
      body: JSON.stringify({ input, version }),
    });
    const data = await resp.json();
    return data.data;
  }

  async get(nodeName: string): Promise<NodeResponse> {
    const resp = await fetch(
      `${this.baseUrl}/api/v1/nodes?name=${encodeURIComponent(nodeName)}`,
      { headers: this.headers },
    );
    const data = await resp.json();
    if (!data.data?.length) throw new Error(`Node '${nodeName}' not found`);
    return data.data[0];
  }

  async search(query: string, filters?: {
    type?: string;
    tags?: string[];
  }): Promise<NodeResponse[]> {
    const params = new URLSearchParams({ q: query });
    if (filters?.type) params.set("type", filters.type);
    filters?.tags?.forEach(tag => params.append("tags", tag));

    const resp = await fetch(
      `${this.baseUrl}/api/v1/search/nodes?${params}`,
      { headers: this.headers },
    );
    const data = await resp.json();
    return data.results;
  }
}
```

### 2.3 Java SDK 设计

```java
// NodeVaultClient.java
public class NodeVaultClient {
    private final String baseUrl;
    private final String token;
    private final OkHttpClient httpClient;

    public NodeVaultClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl.replaceAll("/$", "");
        this.token = apiKey;
        this.httpClient = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .build();
    }

    public InvokeResponse invoke(String nodeName, Map<String, Object> input)
            throws IOException {
        // 1. 找到 Node
        NodeResponse node = get(nodeName);

        // 2. 构建请求
        Map<String, Object> payload = Map.of("input", input);
        String jsonBody = new ObjectMapper().writeValueAsString(payload);

        Request request = new Request.Builder()
            .url(baseUrl + "/api/v1/nodes/" + node.getId() + "/invoke")
            .addHeader("Authorization", "Bearer " + token)
            .post(RequestBody.create(jsonBody, MediaType.get("application/json")))
            .build();

        // 3. 执行请求
        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new NodeVaultException("Invoke failed: " + response.code());
            }
            return parseInvokeResponse(response.body().string());
        }
    }

    // ... 其他方法
}
```

---

## 三、Helm Chart（Kubernetes 部署）

Phase 6 提供官方 Helm Chart，让企业可以一键部署到 Kubernetes。

### 3.1 Chart 结构

```
helm/nodevault/
├── Chart.yaml
├── values.yaml              # 默认配置
├── values.production.yaml   # 生产推荐配置
├── templates/
│   ├── _helpers.tpl
│   ├── deployment-api.yaml
│   ├── deployment-worker.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml             # 水平自动扩缩容
│   ├── pdb.yaml             # Pod Disruption Budget
│   └── NOTES.txt
└── charts/                  # 子 Chart 依赖
    ├── postgresql/
    ├── redis/
    └── meilisearch/
```

### 3.2 一键部署命令

```bash
# 添加 NodeVault Helm 仓库
helm repo add nodevault https://charts.nodevault.io
helm repo update

# 安装（开发模式）
helm install nodevault backend/nodevault \
  --namespace nodevault \
  --create-namespace

# 安装（生产模式）
helm install nodevault backend/nodevault \
  --namespace nodevault \
  --create-namespace \
  --values values.production.yaml \
  --set postgresql.auth.password="your-pg-password" \
  --set auth.jwtSecret="your-jwt-secret"

# 升级
helm upgrade nodevault backend/nodevault --values values.production.yaml
```

---

## 四、文档站建设

高质量文档是开源项目成功的关键。

### 4.1 文档结构

```
docs.nodevault.io

├── 快速开始（15分钟跑通）
│   ├── 安装
│   ├── 注册第一个 Node
│   ├── 调用 Node
│   └── 导出为 OpenAI Tool

├── 核心概念
│   ├── Node 是什么
│   ├── Workflow 是什么
│   ├── 命名空间
│   └── 版本管理

├── 指南（How-to）
│   ├── 与 OpenAI 集成
│   ├── 与 LangChain 集成
│   ├── 与 Claude Desktop 集成（MCP）
│   ├── 构建 Agent
│   └── 企业部署

├── API 参考
│   ├── REST API（OpenAPI）
│   └── SDK 参考（Python / TypeScript / Java）

├── 示例与教程
│   ├── 资金风险分析管道
│   ├── 文档处理 Agent
│   └── 数据质量检查流水线

└── 社区
    ├── 贡献指南
    ├── 路线图
    └── 更新日志
```

### 4.2 文档技术栈

```
框架：MkDocs Material（GitHub Pages 免费托管）
API 文档：ReDoc（从 OpenAPI spec 自动生成）
SDK 文档：Python: pdoc | TypeScript: TypeDoc
交互式示例：通过 RunKit 或 CodeSandbox
```

---

## 五、开源社区运营

### 5.1 GitHub 仓库规范

```
backend/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
│   └── workflows/
│       ├── ci.yml         # 每次 PR 自动测试
│       ├── release.yml    # 自动发版
│       └── docs.yml       # 自动部署文档
├── LICENSE                # Apache 2.0
└── SECURITY.md            # 安全漏洞上报流程
```

### 5.2 CI/CD 流水线

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy .
      - run: pytest --cov=nodevault --cov-report=xml
      - uses: codecov/codecov-action@v4

  build-docker:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          push: ${{ github.ref == 'refs/heads/main' }}
          tags: ghcr.io/nodevault/nodevault:latest
```

### 5.3 发版流程（自动化）

```yaml
# .github/workflows/release.yml
# 当推送 tag v* 时自动：
# 1. 构建 Docker 镜像并推送到 GHCR
# 2. 发布 Python SDK 到 PyPI
# 3. 发布 TypeScript SDK 到 npm
# 4. 创建 GitHub Release（附带 CHANGELOG）
```

---

## 六、向量搜索增强（Phase 6 高级特性）

在 Phase 2 的关键词搜索基础上，Phase 6 引入**语义向量搜索**，让 Agent 能真正理解意图。

```
用户查询: "我需要识别可疑的反洗钱交易"
         ↓ 语义理解
向量搜索: 找到与这个意图最相似的 Node
         ↓ 不需要关键词完全匹配
结果: detect_fund_pool (0.92), aml_check (0.88), transaction_risk (0.84)
```

### 6.1 向量化方案

```python
# core/semantic_search.py
from sentence_transformers import SentenceTransformer
from pgvector.asyncpg import register_vector
import numpy as np


class SemanticSearchEngine:
    """
    基于向量嵌入的语义搜索引擎

    使用 PostgreSQL + pgvector 存储和检索向量
    嵌入模型: text2vec-base-chinese（针对中文优化）
    """

    def __init__(self):
        # 推荐使用支持中文的模型
        self.model = SentenceTransformer("shibing624/text2vec-base-chinese")

    def embed(self, text: str) -> list[float]:
        """将文本转换为向量"""
        return self.model.encode(text).tolist()

    async def search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.6,
        db_session = None,
    ) -> list[dict]:
        """语义相似度搜索"""
        query_vector = self.embed(query)

        # 使用 pgvector 的余弦相似度查询
        results = await db_session.execute("""
            SELECT
                n.id, n.name, n.description,
                1 - (nv.embedding <=> $1::vector) AS similarity
            FROM nodes n
            JOIN node_embeddings nv ON n.id = nv.node_id
            WHERE n.status = 'active'
              AND 1 - (nv.embedding <=> $1::vector) > $2
            ORDER BY similarity DESC
            LIMIT $3
        """, query_vector, threshold, top_k)

        return [dict(row) for row in results]
```

### 6.2 Node Embedding 表

```sql
CREATE TABLE node_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_id UUID REFERENCES nodes(id),
    embedding vector(768),        -- text2vec-base-chinese 维度
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON node_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 七、里程碑成就体系

NodeVault 达到这些指标，意味着真正成为有影响力的开源项目：

| 里程碑 | 指标 | 意义 |
|--------|------|------|
| 🌱 起步 | 100 GitHub Stars | 有人关注 |
| 🚀 起飞 | 1,000 Stars + 10 贡献者 | 社区形成 |
| 🏆 成熟 | 5,000 Stars + 100 已注册 Node 包 | 生态建立 |
| 🌍 标准 | 50+ 企业在用 | 事实标准 |

---

## 八、与主流生态的集成路线图

| 集成目标 | 类型 | 优先级 |
|---------|------|--------|
| Claude Desktop | MCP Server | P0（Phase 3 已完成） |
| OpenAI GPT | Function Calling | P0（Phase 3 已完成） |
| LangChain | Tool | P0（Phase 3 已完成） |
| LlamaIndex | Tool | P1 |
| Dify | 外部工具 | P1 |
| Flowise | 自定义节点 | P2 |
| AutoGen | 工具注册 | P2 |
| CrewAI | Tool | P2 |
| n8n | 自定义节点 | P3 |

---

## 九、商业化路线（可选）

如果 NodeVault 开源成功，可以考虑以下商业化方式（不影响开源版本）：

```
开源版 (Community)
├── 完整功能（自托管）
├── 无限 Node 数量
└── 社区支持

企业云版 (Cloud)
├── 托管服务（zero ops）
├── 高级安全（SSO、SAML）
├── SLA 保证
├── 私有 Marketplace
└── 优先支持

企业本地版 (Enterprise On-Premise)
├── 本地部署许可
├── 合规审计功能
├── 定制集成
└── 专属客户成功
```

---

## 十、Phase 6 交付检查清单

```
□ Node Package 格式规范定稿
□ Marketplace 后端 API 实现
□ Marketplace 前端 UI 实现
□ TypeScript SDK 实现并发布到 npm
□ Java SDK 实现并发布到 Maven Central
□ Helm Chart 发布到 ArtifactHub
□ 文档站搭建并上线（docs.nodevault.io）
□ 快速开始教程（15分钟可跑通）
□ 3+ 完整集成示例
□ GitHub Actions CI/CD 完整配置
□ 自动发版流程
□ CONTRIBUTING.md 贡献指南
□ 向量语义搜索实现（可选高级特性）
□ Discord 或 Slack 社区建立
□ 项目 Blog/公众号建立
```

---

## 最后：NodeVault 的长期愿景

```
今天的 NodeVault：
  企业内部 AI 能力仓库

明天的 NodeVault：
  AI 能力的 npm + Docker Hub

未来的 NodeVault：
  当你说"我需要分析财务风险"，
  NodeVault 告诉你世界上有多少种方式可以做到，
  并直接帮你的 Agent 调用最合适的那一个。
```

这才是里程碑意义的项目。

---

> **上一步 ←** [Phase 5 - 企业级治理](./Phase5-企业级治理.md)
> **返回总览 →** [README - 整体规划总览](./README-整体规划总览.md)
