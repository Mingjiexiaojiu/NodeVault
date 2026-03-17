# Phase 2 — 能力发现与 SDK

> **周期：约 5 周**
> **目标：让开发者能轻松找到 Node，并用 SDK 优雅地接入**

---

## 核心思想

> Phase 1 让系统"能用"，Phase 2 让系统"好用"。

NodeVault 的价值不只是存 Node，更在于**让人快速找到并使用正确的 Node**。

Phase 2 两个核心能力：
1. **能力发现**：搜索、标签、语义推荐——让 Agent 和开发者快速定位所需能力
2. **Python SDK**：封装所有 API 交互，让接入 NodeVault 变成一行代码

---

## 一、全文搜索系统

### 1.1 搜索需求分析

| 搜索场景 | 示例 | 技术方案 |
|---------|------|---------|
| 精确名称 | `name=detect_fund_pool` | 数据库精确查询 |
| 标签过滤 | `tag=finance,risk` | 数据库 IN 查询 |
| 关键词搜索 | `q=资金池检测` | MeiliSearch 全文 |
| 语义搜索 | `q=分析交易是否有洗钱风险` | 向量检索（Phase 3+） |
| 类型过滤 | `type=analysis` | 数据库枚举查询 |
| 组合查询 | 上述任意组合 | 统一搜索接口 |

### 1.2 MeiliSearch 集成

选用 MeiliSearch 而非 Elasticsearch，原因：
- 零配置启动，开发友好
- 中文分词支持好
- 容错搜索（typo tolerance）
- 性能出色（Rust 实现）

```python
# core/search.py
import meilisearch
from core.config import settings


class NodeSearchIndex:
    """MeiliSearch 节点搜索索引管理"""

    INDEX_NAME = "nodes"

    def __init__(self):
        self.client = meilisearch.Client(
            settings.meilisearch_url,
            settings.meilisearch_api_key,
        )
        self.index = self.client.index(self.INDEX_NAME)

    async def setup_index(self):
        """初始化搜索索引配置"""
        # 可搜索字段
        await self.index.update_searchable_attributes([
            "name", "display_name", "description", "tags", "keywords", "category", "team"
        ])
        # 可过滤字段
        await self.index.update_filterable_attributes([
            "type", "status", "visibility", "namespace", "tags", "team"
        ])
        # 排序字段
        await self.index.update_sortable_attributes([
            "created_at", "updated_at", "invocation_count"
        ])
        # 自定义排名规则
        await self.index.update_ranking_rules([
            "words", "typo", "proximity", "attribute",
            "sort", "exactness", "invocation_count:desc"
        ])

    async def upsert_node(self, node_data: dict):
        """创建或更新 Node 索引"""
        await self.index.add_documents([node_data], primary_key="id")

    async def delete_node(self, node_id: str):
        """删除 Node 索引"""
        await self.index.delete_document(node_id)

    async def search(
        self,
        query: str = "",
        filters: dict | None = None,
        sort: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        全文搜索 Node

        filter 示例:
          "type = analysis AND status = active"
          "tags IN [finance, risk] AND namespace = default"
        """
        filter_str = self._build_filter(filters or {})

        result = await self.index.search(
            query,
            {
                "filter": filter_str,
                "sort": sort or ["invocation_count:desc"],
                "offset": (page - 1) * page_size,
                "limit": page_size,
                "attributesToHighlight": ["name", "description"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
            }
        )
        return result

    def _build_filter(self, filters: dict) -> str:
        parts = []
        if filters.get("type"):
            parts.append(f"type = {filters['type']}")
        if filters.get("status"):
            parts.append(f"status = {filters['status']}")
        if filters.get("namespace"):
            parts.append(f"namespace = {filters['namespace']}")
        if filters.get("tags"):
            tags = ", ".join(filters["tags"])
            parts.append(f"tags IN [{tags}]")
        return " AND ".join(parts) if parts else ""
```

### 1.3 搜索 API

```python
# api/v1/search.py
from fastapi import APIRouter, Query, Depends
from auth.deps import get_current_user
from core.search import NodeSearchIndex

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/nodes")
async def search_nodes(
    q: str = Query("", description="搜索关键词，支持中英文"),
    type: str | None = Query(None),
    tags: list[str] = Query([]),
    namespace: str | None = Query(None),
    status: str = Query("active"),
    sort: str = Query("relevance", enum=["relevance", "latest", "popular"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
):
    """
    搜索 Node 能力。

    - 支持关键词全文搜索（中英文）
    - 支持类型、标签、命名空间过滤
    - 支持相关性/最新/最热排序
    """
    search_index = NodeSearchIndex()
    filters = {
        "type": type,
        "tags": tags if tags else None,
        "namespace": namespace or current_user.namespace,
        "status": status,
    }
    sort_map = {
        "relevance": None,
        "latest": ["updated_at:desc"],
        "popular": ["invocation_count:desc"],
    }
    result = await search_index.search(
        query=q,
        filters={k: v for k, v in filters.items() if v},
        sort=sort_map[sort],
        page=page,
        page_size=page_size,
    )
    return {
        "total": result["estimatedTotalHits"],
        "page": page,
        "page_size": page_size,
        "results": result["hits"],
    }


@router.get("/suggest")
async def suggest_nodes(
    q: str = Query(..., min_length=1, description="搜索词前缀"),
    limit: int = Query(5, ge=1, le=10),
    current_user = Depends(get_current_user),
):
    """自动补全建议（用于搜索框）"""
    search_index = NodeSearchIndex()
    result = await search_index.search(query=q, page_size=limit)
    return [{"name": hit["name"], "display_name": hit.get("display_name")} for hit in result["hits"]]
```

---

## 二、版本管理系统

### 2.1 语义化版本策略

```
MAJOR.MINOR.PATCH

MAJOR: 不兼容的 API 变更（input/output schema 破坏性修改）
MINOR: 向后兼容的新功能（增加新字段，有默认值）
PATCH: Bug 修复或性能优化（不改变接口）

示例:
  1.0.0  → 首次发布
  1.1.0  → 新增可选参数 threshold
  1.1.1  → 修复某个边界条件
  2.0.0  → 重构输入 schema（破坏性变更）
```

### 2.2 版本兼容性检查器

```python
# core/versioning.py
from typing import Any


class VersionCompatibilityChecker:
    """检查新版本的 Schema 变更是否向后兼容"""

    def check_compatibility(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """
        检查 new_schema 是否与 old_schema 向后兼容。
        返回: (is_compatible, list_of_warnings)
        """
        warnings = []
        breaking_changes = []

        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))
        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})

        # 破坏性变更: 新增必填字段
        new_required_fields = new_required - old_required
        if new_required_fields:
            breaking_changes.append(
                f"新增了必填字段: {new_required_fields}。旧版本调用者将无法满足要求。"
            )

        # 破坏性变更: 删除已有字段
        removed_fields = set(old_props.keys()) - set(new_props.keys())
        if removed_fields:
            breaking_changes.append(
                f"删除了已有字段: {removed_fields}。可能导致旧版本调用者的输出处理失效。"
            )

        # 警告: 字段类型变更
        for field in set(old_props.keys()) & set(new_props.keys()):
            if old_props[field].get("type") != new_props[field].get("type"):
                warnings.append(
                    f"字段 '{field}' 类型从 {old_props[field].get('type')} "
                    f"变更为 {new_props[field].get('type')}"
                )

        is_compatible = len(breaking_changes) == 0
        return is_compatible, breaking_changes + warnings

    def suggest_version_bump(
        self,
        current_version: str,
        is_compatible: bool,
        has_new_features: bool,
    ) -> str:
        """建议版本号"""
        major, minor, patch = map(int, current_version.split("."))
        if not is_compatible:
            return f"{major + 1}.0.0"
        elif has_new_features:
            return f"{major}.{minor + 1}.0"
        else:
            return f"{major}.{minor}.{patch + 1}"
```

### 2.3 版本回滚 API

```
POST /api/v1/nodes/{node_id}/versions/{version}/set-default
  → 将指定版本设为默认版本（实际上是版本回滚）

POST /api/v1/nodes/{node_id}/versions/{version}/deprecate
  → 标记指定版本为已弃用
```

---

## 三、标签系统与分类体系

### 3.1 标签规范

NodeVault 建议使用三级标签体系：

```
domain:   finance | risk | data | nlp | vision | devops
function: analysis | cleaning | scoring | detection | extraction
tech:     python | java | ml | graph | rule-based
```

标签命名规范：
- 全小写
- 用连字符 `-` 分隔多词（如 `risk-scoring`）
- 禁止使用空格

### 3.2 标签推荐 API

```python
@router.get("/tags")
async def list_popular_tags(
    domain: str | None = Query(None),
    limit: int = Query(20),
    current_user = Depends(get_current_user),
):
    """获取热门标签"""
    # 从数据库统计各 Tag 关联的 Node 数量，返回 Top N
    ...


@router.get("/tags/{tag}/nodes")
async def nodes_by_tag(
    tag: str,
    current_user = Depends(get_current_user),
):
    """获取带有指定标签的所有 Node"""
    ...
```

---

## 四、Python SDK 设计

这是 Phase 2 最重要的交付物。SDK 让注册和使用 Node 变成简单的 Python 代码。

### 4.1 SDK 设计哲学

```
设计目标：让开发者感觉 NodeVault 是他们的代码，而不是外部服务

Bad:  requests.post("http://nodevault/api/v1/nodes", json={...})
Good: vault.register(name="...", description="...", ...)

Best: @vault.node(name="...", description="...")
      def my_capability(data: list) -> dict:
          ...
```

### 4.2 SDK 目录结构

```
nodevault-sdk/
├── backend/
│   ├── __init__.py          # 主入口
│   ├── client.py            # HTTP 客户端封装
│   ├── decorator.py         # @node 装饰器
│   ├── models.py            # Pydantic 数据模型
│   ├── exceptions.py        # 异常定义
│   └── utils.py             # 工具函数
├── tests/
│   └── test_client.py
├── pyproject.toml
└── README.md
```

### 4.3 核心客户端（client.py）

```python
# backend/client.py
import httpx
from typing import Any, Callable
from .models import NodeCreate, NodeResponse, InvokeResponse
from .exceptions import NodeVaultError, NodeNotFoundError, AuthError


class NodeVaultClient:
    """NodeVault Python SDK 客户端"""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        email: str | None = None,
        password: str | None = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

        if api_key:
            self._token = api_key
        elif email and password:
            self._login(email, password)

    def _login(self, email: str, password: str):
        with httpx.Client() as client:
            resp = client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            if resp.status_code == 401:
                raise AuthError("Invalid credentials")
            resp.raise_for_status()
            self._token = resp.json()["access_token"]

    @property
    def _headers(self) -> dict:
        if not self._token:
            raise AuthError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self._token}"}

    # ===== Node 管理 =====

    def register(
        self,
        name: str,
        type: str,
        input_schema: dict,
        output_schema: dict,
        endpoint: str,
        description: str = "",
        tags: list[str] | None = None,
        version: str = "1.0.0",
        **kwargs,
    ) -> NodeResponse:
        """注册一个新 Node"""
        payload = {
            "name": name,
            "type": type,
            "description": description,
            "tags": tags or [],
            "version": version,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "runtime": {"type": "http", "endpoint": endpoint},
            **kwargs,
        }
        with httpx.Client(headers=self._headers) as client:
            resp = client.post(f"{self.base_url}/api/v1/nodes", json=payload)
            self._raise_for_status(resp)
            return NodeResponse(**resp.json()["data"])

    def get(self, node_name: str) -> NodeResponse:
        """通过名称获取 Node"""
        with httpx.Client(headers=self._headers) as client:
            resp = client.get(f"{self.base_url}/api/v1/nodes?name={node_name}")
            resp.raise_for_status()
            nodes = resp.json()["data"]
            if not nodes:
                raise NodeNotFoundError(f"Node '{node_name}' not found")
            return NodeResponse(**nodes[0])

    def search(self, query: str, **filters) -> list[NodeResponse]:
        """搜索 Node"""
        params = {"q": query, **filters}
        with httpx.Client(headers=self._headers) as client:
            resp = client.get(f"{self.base_url}/api/v1/search/nodes", params=params)
            resp.raise_for_status()
            return [NodeResponse(**n) for n in resp.json()["results"]]

    def invoke(
        self,
        node_name: str,
        input_data: dict[str, Any],
        version: str | None = None,
    ) -> InvokeResponse:
        """调用 Node"""
        node = self.get(node_name)
        payload = {"input": input_data}
        if version:
            payload["version"] = version

        with httpx.Client(headers=self._headers) as client:
            resp = client.post(
                f"{self.base_url}/api/v1/nodes/{node.id}/invoke",
                json=payload,
            )
            self._raise_for_status(resp)
            return InvokeResponse(**resp.json()["data"])

    def list_nodes(self, **filters) -> list[NodeResponse]:
        """列出 Node"""
        with httpx.Client(headers=self._headers) as client:
            resp = client.get(f"{self.base_url}/api/v1/nodes", params=filters)
            resp.raise_for_status()
            return [NodeResponse(**n) for n in resp.json()["data"]]

    # ===== 装饰器支持 =====

    def node(
        self,
        name: str,
        type: str,
        description: str = "",
        tags: list[str] | None = None,
        endpoint: str | None = None,
        auto_register: bool = True,
    ):
        """
        @vault.node 装饰器

        用法:
            @vault.node(
                name="my_analysis",
                type="analysis",
                description="分析数据",
                tags=["data"],
                endpoint="http://my-service/api/analyze"
            )
            def my_analysis(data: list) -> dict:
                pass
        """
        import inspect
        import typing

        def decorator(func: Callable):
            # 从函数签名自动生成 input/output schema
            sig = inspect.signature(func)
            hints = typing.get_type_hints(func)

            input_schema = self._generate_schema_from_hints(
                {k: v for k, v in hints.items() if k != "return"},
                sig,
            )
            output_type = hints.get("return", dict)
            output_schema = self._type_to_schema(output_type)

            if auto_register:
                try:
                    self.register(
                        name=name,
                        type=type,
                        description=description,
                        tags=tags or [],
                        input_schema=input_schema,
                        output_schema=output_schema,
                        endpoint=endpoint or f"__local__/{name}",
                    )
                except Exception:
                    pass  # 已存在则跳过

            func._nodevault_name = name
            func._nodevault_registered = True
            return func

        return decorator

    def _generate_schema_from_hints(self, hints: dict, sig) -> dict:
        """从 Python 类型注解生成 JSON Schema"""
        properties = {}
        required = []
        for param_name, hint in hints.items():
            properties[param_name] = self._type_to_schema(hint)
            param = sig.parameters.get(param_name)
            if param and param.default is inspect.Parameter.empty:
                required.append(param_name)
        return {"type": "object", "properties": properties, "required": required}

    def _type_to_schema(self, python_type) -> dict:
        """Python 类型 → JSON Schema"""
        type_map = {
            int: {"type": "integer"},
            float: {"type": "number"},
            str: {"type": "string"},
            bool: {"type": "boolean"},
            list: {"type": "array"},
            dict: {"type": "object"},
        }
        return type_map.get(python_type, {"type": "object"})

    def _raise_for_status(self, resp: httpx.Response):
        if resp.status_code == 404:
            raise NodeNotFoundError(resp.json().get("error", {}).get("message", "Not found"))
        if resp.status_code == 401:
            raise AuthError("Unauthorized")
        if resp.status_code >= 400:
            raise NodeVaultError(f"API Error {resp.status_code}: {resp.text}")
```

### 4.4 SDK 使用示例

```python
from nodevault import NodeVaultClient

# 初始化客户端
vault = NodeVaultClient(
    base_url="http://nodevault.company.com",
    email="dev@company.com",
    password="your-password",
)

# ===== 方式一：直接注册 =====
node = vault.register(
    name="detect_fund_pool",
    type="analysis",
    description="检测资金池聚集行为",
    tags=["finance", "risk"],
    endpoint="http://risk-service/api/fund_pool",
    input_schema={
        "type": "object",
        "properties": {"transactions": {"type": "array"}},
        "required": ["transactions"],
    },
    output_schema={
        "type": "object",
        "properties": {"suspicious_accounts": {"type": "array"}},
    },
)
print(f"已注册 Node: {node.name} (id={node.id})")


# ===== 方式二：装饰器注册 =====
@vault.node(
    name="calculate_risk_score",
    type="risk",
    description="计算交易风险评分",
    tags=["risk", "ml"],
    endpoint="http://ml-service/api/risk-score",
)
def calculate_risk_score(account_id: str, transaction_count: int) -> dict:
    """这个函数本体主要用于文档目的，实际调用走 endpoint"""
    pass


# ===== 搜索 Node =====
results = vault.search("资金分析", type="analysis")
for node in results:
    print(f"{node.name}: {node.description}")


# ===== 调用 Node =====
result = vault.invoke(
    "detect_fund_pool",
    input_data={
        "transactions": [
            {"tx_id": "T001", "from_account": "A", "to_account": "B", "amount": 10000}
        ]
    }
)
print(f"结果: {result.output}")
print(f"耗时: {result.latency_ms}ms")
```

### 4.5 异步 SDK 支持

```python
# backend/async_client.py
import httpx
from .models import NodeResponse, InvokeResponse


class AsyncNodeVaultClient:
    """异步版本 SDK（适用于 FastAPI / asyncio 环境）"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self._headers = {"Authorization": f"Bearer {api_key}"}

    async def invoke(self, node_name: str, input_data: dict) -> InvokeResponse:
        async with httpx.AsyncClient(headers=self._headers) as client:
            node = await self._get_node(client, node_name)
            resp = await client.post(
                f"{self.base_url}/api/v1/nodes/{node.id}/invoke",
                json={"input": input_data},
            )
            resp.raise_for_status()
            return InvokeResponse(**resp.json()["data"])

    async def _get_node(self, client: httpx.AsyncClient, name: str) -> NodeResponse:
        resp = await client.get(f"{self.base_url}/api/v1/nodes?name={name}")
        resp.raise_for_status()
        return NodeResponse(**resp.json()["data"][0])
```

---

## 五、OpenAPI / GraphQL 文档

### 5.1 FastAPI 自动文档增强

```python
# main.py
from fastapi import FastAPI

app = FastAPI(
    title="NodeVault API",
    description="""
# NodeVault — Enterprise AI Capability Registry

NodeVault 是企业 AI 能力的统一注册中心。

## 功能
- 注册和管理 AI 能力节点（Node）
- 按名称、标签、类型搜索 Node
- 统一调用 Node（支持 HTTP/gRPC/Docker）
- 版本管理与回滚
- Skill 导出（OpenAI / LangChain / MCP）

## 认证
所有接口需要在请求头中携带 JWT Token：
```
Authorization: Bearer <your_token>
```
""",
    version="1.0.0",
    contact={"name": "NodeVault Team", "email": "support@nodevault.io"},
    license_info={"name": "Apache 2.0"},
)
```

### 5.2 接口注释示例

```python
@router.post(
    "",
    response_model=NodeResponse,
    status_code=201,
    summary="注册新的 Node",
    description="""
注册一个新的 AI 能力节点到 NodeVault。

Node 必须有唯一的 `name`（在同一命名空间内）。注册成功后，
其他系统可以通过搜索或直接名称查询到该 Node，并通过 `/invoke` 接口调用。

**注意**：Node 注册后默认为 `draft` 状态，需要手动将状态改为 `active` 才能被其他系统调用。
""",
    responses={
        201: {"description": "Node 注册成功"},
        400: {"description": "参数验证失败（如 name 格式不符）"},
        409: {"description": "同名 Node 已存在"},
    }
)
async def register_node(...):
    ...
```

---

## 六、调用统计 API

```python
# api/v1/stats.py

@router.get("/nodes/{node_id}/stats")
async def get_node_stats(
    node_id: UUID,
    days: int = Query(30, description="统计最近N天"),
    current_user = Depends(get_current_user),
):
    """获取 Node 调用统计"""
    return {
        "node_id": str(node_id),
        "period_days": days,
        "total_invocations": 1024,
        "success_rate": 0.987,
        "avg_latency_ms": 234,
        "p95_latency_ms": 890,
        "p99_latency_ms": 1200,
        "daily_trend": [
            {"date": "2026-03-01", "count": 45, "errors": 2},
            # ...
        ],
        "top_callers": [
            {"user": "agent-01", "count": 512},
        ],
    }
```

---

## 七、Phase 2 新增 API 列表

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/search/nodes` | 全文搜索 Node |
| `GET` | `/api/v1/search/suggest` | 搜索自动补全 |
| `GET` | `/api/v1/tags` | 获取热门标签 |
| `GET` | `/api/v1/tags/{tag}/nodes` | 按标签获取 Node |
| `GET` | `/api/v1/nodes/{id}/stats` | Node 调用统计 |
| `POST` | `/api/v1/nodes/{id}/versions/{v}/set-default` | 版本回滚 |
| `POST` | `/api/v1/nodes/{id}/versions/{v}/deprecate` | 弃用版本 |
| `GET` | `/api/v1/nodes/{id}/changelog` | 版本变更记录 |

---

## 八、Phase 2 交付检查清单

```
□ MeiliSearch 搜索服务集成并正常工作
□ Node 注册时自动同步到搜索索引
□ 全文搜索 API 实现（关键词 + 标签 + 类型过滤）
□ 搜索自动补全 API
□ 语义化版本号校验
□ 版本兼容性检查器实现
□ 版本回滚 API
□ 标签管理 API
□ Python SDK 同步版本完成
□ Python SDK 异步版本完成
□ @vault.node 装饰器实现
□ SDK 测试覆盖率 ≥ 80%
□ SDK 发布到 PyPI（或私有 registry）
□ API 文档完整（Swagger + 描述示例）
□ Node 调用统计 API
□ SDK 使用教程文档
```

---

> **上一步 ←** [Phase 1 - MVP 核心功能](./Phase1-MVP核心功能.md)
> **下一步 →** [Phase 3 - Skill 导出与 Agent 集成](./Phase3-Skill导出与Agent集成.md)
