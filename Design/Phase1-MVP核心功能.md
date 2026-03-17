# Phase 1 — MVP 核心功能

> **周期：约 6 周**
> **目标：系统可以真正运行——节点能注册、能查询、能调用**

---

## 核心思想

> MVP 的意义不是"不完美"，而是"聚焦核心价值，尽快能用"。

Phase 1 交付的系统必须能做到：

```
开发者注册一个 Node → 另一个系统查询到它 → 发起调用 → 拿到结果
```

这条链路跑通，NodeVault 就有了存在价值。

---

## 一、数据库实现

### 1.1 SQLAlchemy ORM 模型

#### models/node.py

```python
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer,
    ForeignKey, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from database.base import Base
import enum


class NodeType(str, enum.Enum):
    DATA_CLEANING = "data_cleaning"
    ANALYSIS = "analysis"
    RISK = "risk"
    NLP = "nlp"
    VISION = "vision"
    ML = "ml"
    TOOL = "tool"
    UTILITY = "utility"


class NodeStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class NodeVisibility(str, enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PRIVATE = "private"


class Node(Base):
    __tablename__ = "nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(128), nullable=False, index=True)
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    display_name = Column(String(256))
    description = Column(Text)
    type = Column(SQLEnum(NodeType), nullable=False, index=True)
    category = Column(String(128), index=True)

    status = Column(SQLEnum(NodeStatus), default=NodeStatus.DRAFT, index=True)
    visibility = Column(SQLEnum(NodeVisibility), default=NodeVisibility.INTERNAL)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    versions = relationship("NodeVersion", back_populates="node", cascade="all, delete-orphan")
    tags = relationship("NodeTag", back_populates="node", cascade="all, delete-orphan")
    invocation_logs = relationship("NodeInvocationLog", back_populates="node")

    # 联合唯一约束: 同一命名空间下 name 唯一
    __table_args__ = (
        UniqueConstraint("name", "namespace_id", name="uq_node_name_namespace"),
    )


class NodeVersion(Base):
    __tablename__ = "node_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    version = Column(String(32), nullable=False)

    input_schema = Column(JSONB, nullable=False)
    output_schema = Column(JSONB, nullable=False)
    runtime_config = Column(JSONB, nullable=False)

    changelog = Column(Text)
    is_default = Column(Boolean, default=False)
    is_deprecated = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    node = relationship("Node", back_populates="versions")


class NodeTag(Base):
    __tablename__ = "node_tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    tag = Column(String(64), nullable=False, index=True)

    node = relationship("Node", back_populates="tags")


class NodeInvocationLog(Base):
    __tablename__ = "node_invocation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("nodes.id"), nullable=False)
    version = Column(String(32))

    invoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    input_data = Column(JSONB)
    output_data = Column(JSONB)

    status = Column(String(32), nullable=False)   # success | failure | timeout
    latency_ms = Column(Integer)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    node = relationship("Node", back_populates="invocation_logs")
```

---

### 1.2 数据库迁移

所有表通过 Alembic 管理，初始迁移在 Phase 0 创建骨架时生成：

```bash
alembic revision --autogenerate -m "Initial schema: nodes, versions, tags, logs"
alembic upgrade head
```

---

## 二、认证系统

### 2.1 JWT 认证流程

```
客户端                          NodeVault
  │                                │
  │  POST /api/v1/auth/login       │
  │  { email, password }    ──────▶│
  │                                │ 验证密码（bcrypt）
  │                                │ 生成 access_token（30min）
  │◀────── { access_token, ... }───│
  │                                │
  │  GET /api/v1/nodes             │
  │  Authorization: Bearer <token> │
  │                         ──────▶│ 验证 JWT
  │◀──────────── { nodes: [...] } ─│
```

### 2.2 认证 API

```
POST /api/v1/auth/register      注册
POST /api/v1/auth/login         登录，返回 JWT
POST /api/v1/auth/refresh       刷新 Token
GET  /api/v1/auth/me            获取当前用户信息
```

### 2.3 核心 auth 代码

```python
# auth/jwt.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {"sub": subject, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise ValueError("Invalid token")
```

---

## 三、Node Registry API

### 3.1 Pydantic Schema

```python
# schemas/node.py
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Any
from models.node import NodeType, NodeStatus, NodeVisibility


class RuntimeConfig(BaseModel):
    type: str                               # http | grpc | docker | python
    endpoint: str
    method: str = "POST"
    headers: dict[str, str] = {}
    auth: dict[str, Any] | None = None
    timeout: str = "30s"


class NodeCreate(BaseModel):
    name: str = Field(..., pattern=r'^[a-z][a-z0-9_]*$', max_length=128)
    display_name: str | None = None
    description: str | None = None
    type: NodeType
    category: str | None = None
    tags: list[str] = []
    version: str = "1.0.0"
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    runtime: RuntimeConfig
    visibility: NodeVisibility = NodeVisibility.INTERNAL
    changelog: str | None = None


class NodeResponse(BaseModel):
    id: UUID
    name: str
    display_name: str | None
    description: str | None
    type: NodeType
    category: str | None
    tags: list[str]
    status: NodeStatus
    visibility: NodeVisibility
    default_version: str | None
    namespace: str
    owner: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NodeVersionResponse(BaseModel):
    id: UUID
    node_id: UUID
    version: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    runtime_config: dict[str, Any]
    is_default: bool
    is_deprecated: bool
    created_at: datetime
```

### 3.2 Node Registry 路由

```python
# api/v1/nodes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from database.session import get_db
from auth.deps import get_current_user
from core.registry import NodeRegistry
from schemas.node import NodeCreate, NodeResponse, NodeVersionResponse

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.post("", response_model=NodeResponse, status_code=201)
async def register_node(
    payload: NodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """注册新的 Node"""
    registry = NodeRegistry(db)
    return await registry.create_node(payload, owner=current_user)


@router.get("", response_model=list[NodeResponse])
async def list_nodes(
    namespace: str | None = Query(None),
    type: str | None = Query(None),
    status: str | None = Query(None),
    tag: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """列出 Node，支持过滤"""
    registry = NodeRegistry(db)
    return await registry.list_nodes(
        namespace=namespace, type=type, status=status,
        tag=tag, page=page, page_size=page_size,
        user=current_user,
    )


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """获取 Node 详情"""
    registry = NodeRegistry(db)
    node = await registry.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.patch("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """更新 Node 元信息"""
    registry = NodeRegistry(db)
    return await registry.update_node(node_id, payload, user=current_user)


@router.delete("/{node_id}", status_code=204)
async def delete_node(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """软删除 Node（状态改为 archived）"""
    registry = NodeRegistry(db)
    await registry.archive_node(node_id, user=current_user)


# ===== 版本管理 =====

@router.get("/{node_id}/versions", response_model=list[NodeVersionResponse])
async def list_versions(
    node_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    registry = NodeRegistry(db)
    return await registry.list_versions(node_id)


@router.post("/{node_id}/versions", response_model=NodeVersionResponse, status_code=201)
async def create_version(
    node_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """为已有 Node 发布新版本"""
    registry = NodeRegistry(db)
    return await registry.create_version(node_id, payload, user=current_user)
```

---

## 四、Node Runtime（调用执行）

### 4.1 执行器架构

```
POST /api/v1/nodes/{node_id}/invoke
          │
          ▼
    InvokeService
          │
          ├── 1. 查找 Node 和默认版本
          ├── 2. 提取 runtime_config
          ├── 3. 选择执行器
          │         ├── HTTPExecutor     (type=http)
          │         ├── GrpcExecutor     (type=grpc, Phase 2)
          │         └── DockerExecutor   (type=docker, Phase 3)
          ├── 4. 执行调用
          ├── 5. 记录 InvocationLog
          └── 6. 返回结果
```

### 4.2 HTTP 执行器实现

```python
# core/runtime.py
import time
import httpx
from typing import Any
from models.node import NodeVersion, NodeInvocationLog

class HTTPExecutor:
    """HTTP 类型 Node 执行器（Phase 1 主要实现）"""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    async def execute(
        self,
        runtime_config: dict,
        input_data: dict[str, Any],
    ) -> tuple[dict[str, Any], int]:
        """
        执行 HTTP 节点调用
        返回: (output_data, latency_ms)
        """
        endpoint = runtime_config["endpoint"]
        method = runtime_config.get("method", "POST").upper()
        headers = runtime_config.get("headers", {})
        auth = runtime_config.get("auth")

        # 处理认证
        if auth:
            headers = self._apply_auth(headers, auth)

        start_time = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == "POST":
                    response = await client.post(endpoint, json=input_data, headers=headers)
                elif method == "GET":
                    response = await client.get(endpoint, params=input_data, headers=headers)
                else:
                    response = await client.request(method, endpoint, json=input_data, headers=headers)

                response.raise_for_status()
                latency_ms = int((time.monotonic() - start_time) * 1000)
                return response.json(), latency_ms

        except httpx.TimeoutException:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            raise RuntimeError(f"Node invocation timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            latency_ms = int((time.monotonic() - start_time) * 1000)
            raise RuntimeError(f"Node returned HTTP {e.response.status_code}: {e.response.text}")

    def _apply_auth(self, headers: dict, auth: dict) -> dict:
        headers = headers.copy()
        if auth.get("type") == "bearer":
            import os
            token = os.environ.get(auth.get("token_env", ""), auth.get("token", ""))
            headers["Authorization"] = f"Bearer {token}"
        elif auth.get("type") == "api_key":
            import os
            key = os.environ.get(auth.get("key_env", ""), auth.get("key", ""))
            headers[auth.get("header", "X-API-Key")] = key
        return headers


class RuntimeDispatcher:
    """根据 runtime_config.type 分发到对应执行器"""

    _executors = {
        "http": HTTPExecutor,
    }

    @classmethod
    def get_executor(cls, runtime_type: str):
        executor_class = cls._executors.get(runtime_type)
        if not executor_class:
            raise ValueError(f"Unsupported runtime type: {runtime_type}. Supported: {list(cls._executors.keys())}")
        return executor_class()
```

### 4.3 调用 API

```python
# api/v1/invoke.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Any
from database.session import get_db
from auth.deps import get_current_user
from core.runtime import RuntimeDispatcher
from core.registry import NodeRegistry

router = APIRouter(prefix="/nodes", tags=["Invoke"])


class InvokeRequest(BaseModel):
    input: dict[str, Any]
    version: str | None = None          # None 表示使用默认版本


class InvokeResponse(BaseModel):
    node_name: str
    version: str
    output: dict[str, Any]
    latency_ms: int
    invocation_id: str


@router.post("/{node_id}/invoke", response_model=InvokeResponse)
async def invoke_node(
    node_id: UUID,
    request: InvokeRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    调用指定 Node。
    - 自动选择默认版本（或指定版本）
    - 记录调用日志
    - 返回执行结果
    """
    registry = NodeRegistry(db)

    # 1. 获取 Node 信息
    node = await registry.get_node(node_id)
    if not node or node.status != "active":
        raise HTTPException(status_code=404, detail="Node not found or not active")

    # 2. 获取版本
    version = await registry.get_version(node_id, request.version)
    if not version:
        raise HTTPException(status_code=404, detail="Node version not found")

    # 3. 执行
    executor = RuntimeDispatcher.get_executor(version.runtime_config["type"])
    try:
        output, latency_ms = await executor.execute(version.runtime_config, request.input)
        status = "success"
        error_message = None
    except RuntimeError as e:
        output = {}
        latency_ms = 0
        status = "failure"
        error_message = str(e)
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        # 4. 记录日志（无论成功失败都记录）
        await registry.log_invocation(
            node_id=node_id,
            version=version.version,
            invoked_by=current_user.id,
            input_data=request.input,
            output_data=output,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
        )

    return InvokeResponse(
        node_name=node.name,
        version=version.version,
        output=output,
        latency_ms=latency_ms,
        invocation_id=str(log_id),
    )
```

---

## 五、Health Check 与基础监控

```python
# api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_db
from sqlalchemy import text

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """系统健康检查"""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
        },
        "version": "0.1.0",
    }
```

---

## 六、完整 API 列表（Phase 1）

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/auth/register` | 注册用户 |
| `POST` | `/api/v1/auth/login` | 登录获取 Token |
| `GET` | `/api/v1/auth/me` | 获取当前用户 |
| `POST` | `/api/v1/nodes` | 注册 Node |
| `GET` | `/api/v1/nodes` | 列出 Node（支持过滤） |
| `GET` | `/api/v1/nodes/{id}` | 获取 Node 详情 |
| `PATCH` | `/api/v1/nodes/{id}` | 更新 Node 元信息 |
| `DELETE` | `/api/v1/nodes/{id}` | 软删除 Node |
| `GET` | `/api/v1/nodes/{id}/versions` | 列出版本 |
| `POST` | `/api/v1/nodes/{id}/versions` | 发布新版本 |
| `POST` | `/api/v1/nodes/{id}/invoke` | 调用 Node |
| `GET` | `/api/v1/nodes/{id}/logs` | 查看调用日志 |
| `GET` | `/health` | 健康检查 |

---

## 七、前端 Web UI（轻量级，Phase 1 可选）

Phase 1 以 API 为主，但建议同步提供一个极简的管理页面：

```
NodeVault Dashboard (MVP)
├── Node 列表页（表格展示所有 Node，支持搜索/过滤）
├── Node 详情页（展示 Schema / 版本 / 调用日志）
├── Node 注册表单（填写 YAML 或表单）
└── 在线调用测试（输入 JSON，查看结果）
```

技术选型：**Vue 3 + Naive UI** 或直接使用 FastAPI 自带的 **Swagger UI**（零代价，快速可用）。

---

## 八、Phase 1 交付检查清单

```
□ 数据库表全部建好，Alembic 迁移可运行
□ 用户注册/登录 API 可用
□ Node CRUD API 全部实现
□ Node 版本管理 API 实现
□ HTTP 类型 Node 调用功能实现
□ 调用日志记录功能
□ 所有 API 都有 JWT 认证保护
□ /health 健康检查端点
□ 单元测试覆盖率 ≥ 70%
□ API 文档（Swagger）完整
□ docker-compose 一键启动
□ README Quick Start 可跑通
```

---

## 九、Phase 1 核心验证场景

以下场景必须全部跑通，才算 Phase 1 完成：

```bash
# 场景1: 注册用户
curl -X POST /api/v1/auth/register \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# 场景2: 登录获取 Token
TOKEN=$(curl -X POST /api/v1/auth/login \
  -d '{"email":"test@example.com","password":"Test1234!"}' | jq -r .access_token)

# 场景3: 注册一个 Node
curl -X POST /api/v1/nodes \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "clean_data",
    "type": "data_cleaning",
    "tags": ["data"],
    "version": "1.0.0",
    "input_schema": {"type":"object","properties":{"data":{"type":"array"}}},
    "output_schema": {"type":"object","properties":{"result":{"type":"array"}}},
    "runtime": {"type":"http","endpoint":"http://localhost:9000/clean"}
  }'

# 场景4: 查询 Node
curl -X GET /api/v1/nodes?tag=data \
  -H "Authorization: Bearer $TOKEN"

# 场景5: 调用 Node
curl -X POST /api/v1/nodes/{id}/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"input": {"data": [1,2,3]}}'

# 场景6: 查看调用日志
curl -X GET /api/v1/nodes/{id}/logs \
  -H "Authorization: Bearer $TOKEN"
```

---

> **上一步 ←** [Phase 0 - 基础与规范](./Phase0-基础与规范.md)
> **下一步 →** [Phase 2 - 能力发现与 SDK](./Phase2-能力发现与SDK.md)
