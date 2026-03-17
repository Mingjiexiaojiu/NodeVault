# Phase 5 — 企业级治理

> **周期：约 6 周**
> **目标：让 NodeVault 具备在企业生产环境中安全、稳定、合规运行的能力**

---

## 核心思想

> 一个系统能"跑起来"和能"放心地跑"，是两个完全不同的标准。

Phase 5 不添加新的业务功能，而是让系统达到**企业级生产标准**：

```
安全：谁能做什么（RBAC）
隔离：不同业务线互不干扰（多租户）
可见：系统发生了什么（可观测性）
可控：防止滥用（限流计费）
合规：谁在什么时候做了什么（审计）
```

---

## 一、RBAC 权限系统

### 1.1 角色设计

NodeVault 采用**三级角色体系**：

```
系统级
  └── super_admin     系统管理员，管理所有命名空间和用户

命名空间级（每个租户内）
  ├── namespace_admin  命名空间管理员，管理本空间所有资源
  ├── developer        开发者，可注册/修改/调用 Node
  ├── viewer           只读用户，只能查看和调用
  └── service_account  服务账号，供 Agent/自动化使用（只有调用权限）
```

### 1.2 权限矩阵

| 操作 | super_admin | namespace_admin | developer | viewer | service_account |
|------|:-----------:|:---------------:|:---------:|:------:|:---------------:|
| 创建命名空间 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 管理用户 | ✅ | ✅（本空间） | ❌ | ❌ | ❌ |
| 注册 Node | ✅ | ✅ | ✅ | ❌ | ❌ |
| 修改 Node | ✅ | ✅ | ✅（自己的） | ❌ | ❌ |
| 删除 Node | ✅ | ✅ | ❌ | ❌ | ❌ |
| 调用 Node | ✅ | ✅ | ✅ | ✅ | ✅ |
| 查看 Node | ✅ | ✅ | ✅ | ✅ | ✅ |
| 创建 Workflow | ✅ | ✅ | ✅ | ❌ | ❌ |
| 执行 Workflow | ✅ | ✅ | ✅ | ❌ | ✅ |
| 查看审计日志 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 管理 API Key | ✅ | ✅ | ✅（自己的） | ❌ | ❌ |

### 1.3 RBAC 实现

```python
# auth/rbac.py
from enum import Enum
from functools import wraps
from fastapi import HTTPException, Depends
from auth.deps import get_current_user


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    NAMESPACE_ADMIN = "namespace_admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    SERVICE_ACCOUNT = "service_account"


class Permission(str, Enum):
    NODE_CREATE = "node:create"
    NODE_READ = "node:read"
    NODE_UPDATE = "node:update"
    NODE_DELETE = "node:delete"
    NODE_INVOKE = "node:invoke"
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_RUN = "workflow:run"
    WORKFLOW_READ = "workflow:read"
    AUDIT_READ = "audit:read"
    USER_MANAGE = "user:manage"
    NAMESPACE_MANAGE = "namespace:manage"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),   # 所有权限

    Role.NAMESPACE_ADMIN: {
        Permission.NODE_CREATE, Permission.NODE_READ,
        Permission.NODE_UPDATE, Permission.NODE_DELETE,
        Permission.NODE_INVOKE, Permission.WORKFLOW_CREATE,
        Permission.WORKFLOW_RUN, Permission.WORKFLOW_READ,
        Permission.AUDIT_READ, Permission.USER_MANAGE,
    },

    Role.DEVELOPER: {
        Permission.NODE_CREATE, Permission.NODE_READ,
        Permission.NODE_UPDATE, Permission.NODE_INVOKE,
        Permission.WORKFLOW_CREATE, Permission.WORKFLOW_RUN,
        Permission.WORKFLOW_READ,
    },

    Role.VIEWER: {
        Permission.NODE_READ, Permission.NODE_INVOKE,
        Permission.WORKFLOW_READ,
    },

    Role.SERVICE_ACCOUNT: {
        Permission.NODE_READ, Permission.NODE_INVOKE,
        Permission.WORKFLOW_RUN, Permission.WORKFLOW_READ,
    },
}


def require_permission(permission: Permission):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
            user_permissions = ROLE_PERMISSIONS.get(current_user.role, set())
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"权限不足：需要 '{permission}' 权限",
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# 使用示例：
# @router.delete("/{node_id}")
# @require_permission(Permission.NODE_DELETE)
# async def delete_node(node_id: UUID, current_user=...):
#     ...
```

### 1.4 资源级权限（细粒度）

对于 Node 的修改，不仅要检查角色，还要检查资源所有权：

```python
# auth/ownership.py

async def check_node_ownership(
    node_id: UUID,
    current_user,
    db: AsyncSession,
    allow_admin: bool = True,
) -> None:
    """检查当前用户是否有权修改指定 Node"""
    node = await get_node(db, node_id)
    if not node:
        raise HTTPException(404, "Node not found")

    is_owner = node.owner_id == current_user.id
    is_admin = current_user.role in (Role.NAMESPACE_ADMIN, Role.SUPER_ADMIN) and allow_admin

    if not (is_owner or is_admin):
        raise HTTPException(
            403,
            "只有 Node 创建者或管理员才能修改此 Node"
        )
```

---

## 二、多租户系统

### 2.1 命名空间隔离模型

```
NodeVault
└── Namespace: finance-dept        (金融部门)
    ├── Node: detect_fund_pool
    ├── Node: risk_score
    └── Workflow: risk_pipeline

└── Namespace: data-platform       (数据平台部门)
    ├── Node: clean_transaction
    └── Node: data_quality_check

└── Namespace: public              (公共能力，所有人可用)
    ├── Node: send_email
    └── Node: format_date
```

### 2.2 跨命名空间访问控制

```python
# core/namespace.py

class NamespaceAccessPolicy:
    """
    命名空间访问策略

    规则：
    1. 默认：只能访问本命名空间的 Node
    2. visibility=public 的 Node 任何人可见
    3. 管理员可显式授权跨命名空间访问
    4. super_admin 不受限制
    """

    async def can_access_node(
        self,
        node: Node,
        current_user,
        db: AsyncSession,
    ) -> bool:
        # super_admin 无限制
        if current_user.role == Role.SUPER_ADMIN:
            return True

        # 同命名空间
        if node.namespace_id == current_user.namespace_id:
            return True

        # public 节点
        if node.visibility == NodeVisibility.PUBLIC:
            return True

        # 检查显式授权
        grant = await self._get_cross_namespace_grant(
            db, node.namespace_id, current_user.namespace_id
        )
        return grant is not None

    async def _get_cross_namespace_grant(
        self, db, owner_namespace_id, requester_namespace_id
    ):
        """检查是否有跨命名空间授权记录"""
        ...
```

### 2.3 命名空间管理 API

```
POST   /api/v1/namespaces              # 创建命名空间（super_admin）
GET    /api/v1/namespaces              # 列出命名空间
GET    /api/v1/namespaces/{id}         # 详情
PATCH  /api/v1/namespaces/{id}         # 更新
DELETE /api/v1/namespaces/{id}         # 删除

POST   /api/v1/namespaces/{id}/users   # 添加用户到命名空间
DELETE /api/v1/namespaces/{id}/users/{user_id}  # 移除用户

GET    /api/v1/namespaces/{id}/stats   # 命名空间使用统计
```

---

## 三、审计日志系统

### 3.1 审计事件类型

| 事件类型 | 触发时机 |
|---------|---------|
| `node.created` | 注册新 Node |
| `node.updated` | 修改 Node 元信息 |
| `node.deleted` | 删除/归档 Node |
| `node.invoked` | 调用 Node（但高频调用可以只记录摘要） |
| `node.version_created` | 发布新版本 |
| `node.version_rollback` | 版本回滚 |
| `workflow.created` | 创建 Workflow |
| `workflow.run_triggered` | 触发 Workflow 执行 |
| `user.login` | 用户登录 |
| `user.permission_denied` | 权限拒绝 |
| `api_key.created` | 创建 API Key |
| `api_key.revoked` | 吊销 API Key |
| `namespace.access_granted` | 跨命名空间访问授权 |

### 3.2 审计日志模型

```python
# models/audit.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 操作者
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    actor_email = Column(String(256))       # 冗余存储，防止用户被删
    actor_ip = Column(String(64))
    actor_user_agent = Column(String(512))

    # 操作
    event_type = Column(String(128), nullable=False, index=True)
    resource_type = Column(String(64))       # node | workflow | user | namespace
    resource_id = Column(String(128))        # 资源 UUID
    resource_name = Column(String(256))      # 冗余方便查看

    # 操作详情
    action_detail = Column(JSONB)            # 操作前后的数据 diff
    request_id = Column(String(128))         # 对应的 HTTP 请求 ID

    # 结果
    result = Column(String(32))              # success | failure | denied
    error_message = Column(Text)

    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

### 3.3 审计日志中间件

```python
# observability/audit_middleware.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class AuditMiddleware(BaseHTTPMiddleware):
    """
    自动记录所有写操作的审计日志

    只审计 POST / PUT / PATCH / DELETE 请求
    GET 请求不记录（太多噪音）
    """

    AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    SKIP_PATHS = {"/health", "/metrics", "/api/v1/auth/login"}

    async def dispatch(self, request: Request, call_next):
        if (request.method not in self.AUDITED_METHODS
                or request.url.path in self.SKIP_PATHS):
            return await call_next(request)

        response = await call_next(request)

        # 异步写入审计日志（不阻塞响应）
        if hasattr(request.state, "current_user"):
            await self._log_audit(request, response)

        return response

    async def _log_audit(self, request: Request, response):
        logger.info(
            "audit_event",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            user_id=str(request.state.current_user.id),
            ip=request.client.host,
            request_id=request.state.request_id,
        )
```

---

## 四、API 限流系统

### 4.1 限流策略设计

| 维度 | 策略 | 默认配置 |
|------|------|---------|
| **全局** | 每 IP 每分钟请求数 | 600 请求/分钟 |
| **用户** | 每用户每分钟 API 调用 | 300 请求/分钟 |
| **Node 调用** | 每 Node 每分钟调用次数 | 由 Node 定义指定 |
| **命名空间** | 每命名空间每天调用总量 | 免费版 10,000 次/天 |

### 4.2 基于 Redis 的限流实现

```python
# core/rate_limiter.py
import redis.asyncio as redis
from fastapi import HTTPException, Request
import time


class TokenBucketLimiter:
    """令牌桶限流（Redis 实现）"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, dict]:
        """
        检查是否超出限制。
        返回 (is_allowed, headers)
        """
        now = time.time()
        window_start = now - window_seconds
        pipe = self.redis.pipeline()

        # 使用滑动窗口算法
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds)
        results = await pipe.execute()

        current_count = results[2]
        remaining = max(0, max_requests - current_count)
        reset_at = int(now) + window_seconds

        headers = {
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_at),
        }

        if current_count > max_requests:
            return False, headers
        return True, headers


# 在路由中使用
async def apply_rate_limit(request: Request, current_user):
    limiter = TokenBucketLimiter(get_redis())
    key = f"ratelimit:user:{current_user.id}:api"
    allowed, headers = await limiter.check_limit(key, max_requests=300, window_seconds=60)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="请求频率超出限制，请稍后再试",
            headers=headers,
        )
    return headers
```

---

## 五、OpenTelemetry 可观测性

### 5.1 三大支柱

| 支柱 | 工具 | 作用 |
|------|------|------|
| **Traces（链路追踪）** | OpenTelemetry → Jaeger | 追踪单次请求在各服务间的完整调用链 |
| **Metrics（指标）** | OpenTelemetry → Prometheus → Grafana | 监控系统健康状态和性能指标 |
| **Logs（日志）** | structlog → Loki / ELK | 结构化日志，便于查询和告警 |

### 5.2 关键监控指标

```python
# observability/metrics.py
from opentelemetry import metrics

meter = metrics.get_meter("nodevault")

# Node 调用计数器
node_invocation_counter = meter.create_counter(
    "backend.node.invocations.total",
    description="Total number of node invocations",
    unit="1",
)

# Node 调用延迟直方图
node_invocation_latency = meter.create_histogram(
    "backend.node.invocation.duration_ms",
    description="Node invocation latency in milliseconds",
    unit="ms",
)

# Node 调用错误率
node_error_counter = meter.create_counter(
    "backend.node.errors.total",
    description="Total number of node invocation errors",
)

# 活跃 Node 数量
active_nodes_gauge = meter.create_observable_gauge(
    "backend.nodes.active.count",
    callbacks=[lambda: active_node_count()],
    description="Number of active nodes",
)

# Workflow 执行计数
workflow_run_counter = meter.create_counter(
    "backend.workflow.runs.total",
    description="Total number of workflow runs",
)

# 使用：
def record_invocation(node_name: str, status: str, latency_ms: int, namespace: str):
    labels = {"node": node_name, "status": status, "namespace": namespace}
    node_invocation_counter.add(1, labels)
    node_invocation_latency.record(latency_ms, labels)
    if status == "failure":
        node_error_counter.add(1, labels)
```

### 5.3 Grafana Dashboard 核心面板

建议创建的 Grafana Dashboard：

```
NodeVault 总览 Dashboard
├── 今日调用总量（大数字）
├── 成功率折线图（近24小时）
├── P95/P99 延迟折线图
├── Top 10 最活跃 Node
├── Top 10 错误 Node
├── 各命名空间调用分布饼图
└── 系统资源使用（CPU/内存）

Node 详情 Dashboard（按 Node 过滤）
├── 调用量趋势
├── 延迟分布直方图
├── 错误日志（linked to Loki）
└── 调用者分布
```

### 5.4 链路追踪配置

```python
# observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def setup_tracing(app):
    """初始化 OpenTelemetry 追踪"""
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # 自动为 FastAPI / SQLAlchemy / httpx 注入追踪
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
```

---

## 六、API Key 管理

除 JWT 外，NodeVault 支持 **长期 API Key** 用于服务账号和自动化场景。

### 6.1 API Key 设计

```
格式：nvk_{32位随机字符串}
示例：nvk_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6

存储：数据库只存储 hash（sha256），明文只在创建时返回一次
```

### 6.2 API Key 模型

```python
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    namespace_id = Column(UUID(as_uuid=True), ForeignKey("namespaces.id"))

    name = Column(String(128))         # 给 key 起个名字，方便识别
    key_prefix = Column(String(8))     # 存储 "nvk_xxxx" 前8位（用于查询）
    key_hash = Column(String(64))      # sha256 hash
    role = Column(String(32))          # 这个 key 的角色

    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 七、告警系统

```yaml
# 告警规则（Prometheus AlertManager）

groups:
  - name: nodevault_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          rate(nodevault_node_errors_total[5m]) /
          rate(nodevault_node_invocations_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Node {{ $labels.node }} 错误率超过 10%"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(nodevault_node_invocation_duration_ms_bucket[5m])
          ) > 2000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Node {{ $labels.node }} P95 延迟超过 2s"

      - alert: NodeVaultServiceDown
        expr: up{job="nodevault"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "NodeVault 服务宕机"
```

---

## 八、生产部署架构

### 8.1 Docker Compose 生产版

```yaml
# deploy/docker-compose.prod.yml
version: '3.9'

services:
  nodevault-api:
    image: nodevault:latest
    replicas: 3
    environment:
      - APP_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nodevault-worker:
    image: nodevault:latest
    command: celery -A core.celery worker -c 4
    replicas: 2

  nginx:
    image: nginx:alpine
    # 负载均衡到多个 API 实例

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # 生产建议使用云数据库（RDS等）

  redis:
    image: redis:7
    command: redis-server --appendonly yes

  meilisearch:
    image: getmeili/meilisearch:latest

  prometheus:
    image: prom/prometheus

  grafana:
    image: grafana/grafana

  jaeger:
    image: jaegertracing/all-in-one
```

### 8.2 高可用架构图

```
Internet
    │
    ▼
[Nginx / CloudFlare]
    │
    ├── /api/v1/* → [NodeVault API × 3]
    │                      │
    │               ┌──────┼──────┐
    │               ▼      ▼      ▼
    │           [PostgreSQL Primary + Replica]
    │           [Redis Cluster]
    │           [MeiliSearch]
    │
    └── /metrics → [Prometheus] → [Grafana]
                → [Jaeger] (traces)
```

---

## 九、Phase 5 交付检查清单

```
□ RBAC 角色权限系统完整实现
□ 所有 API 端点添加权限检查
□ 多命名空间隔离实现
□ 跨命名空间访问授权机制
□ 审计日志模型和中间件
□ 审计日志查询 API
□ 基于 Redis 的限流中间件
□ 限流响应头（X-RateLimit-*）
□ API Key 管理（创建/列出/吊销）
□ OpenTelemetry 集成（Traces + Metrics）
□ Prometheus 指标接口 /metrics
□ Grafana Dashboard 配置文件
□ 告警规则配置（AlertManager）
□ 结构化日志（structlog）
□ 生产 Docker Compose 配置
□ 安全加固文档（HTTPS、密钥轮换等）
□ 数据库备份策略文档
```

---

> **上一步 ←** [Phase 4 - Workflow 编排引擎](./Phase4-Workflow编排引擎.md)
> **下一步 →** [Phase 6 - 生态建设与开源](./Phase6-生态建设与开源.md)
