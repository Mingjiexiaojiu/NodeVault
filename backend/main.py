from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.v1.router import api_router
from backend.api.v1.mcp import get_mcp_app
from backend.core.search import NodeSearchIndex
from backend.database.session import engine
from backend.schemas.response import ErrorDetail, ErrorResponse, ErrorCode

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("backend_starting")
    try:
        NodeSearchIndex().setup_index()
        logger.info("meilisearch_index_ready")
    except Exception as exc:
        logger.warning("meilisearch_setup_failed", error=str(exc))
    yield
    await engine.dispose()
    logger.info("backend_shutdown")


app = FastAPI(
    title="NodeVault API",
    description="""
# NodeVault — Enterprise AI Capability Registry

NodeVault 是企业 AI 能力的统一注册中心，让团队轻松**发现、注册、调用**AI 能力节点（Node）。

## 主要功能

- **Node 管理**：注册、查询、更新、版本管理
- **全文搜索**：基于 MeiliSearch 对 Node 进行关键词 + 标签 + 类型联合搜索
- **Node 调用**：统一调用 HTTP/Docker 运行时的 Node，记录调用日志
- **版本管理**：语义化版本兼容性检查、版本回滚、版本弃用
- **调用统计**：成功率、平均延迟、P95/P99 延迟、每日调用趋势
- **标签体系**：热门标签查询、按标签浏览 Node

## 认证

所有接口（除 `/healthz`、`/api/v1/auth/register`、`/api/v1/auth/login`）均需在请求头中携带 JWT Token：

```
Authorization: Bearer <your_access_token>
```

通过 `POST /api/v1/auth/login` 获取 Token。
""",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# MCP Server（SSE transport） — 挂载为子应用，路径 /mcp
app.mount("/mcp", get_mcp_app())


# Also mount healthz at root level for convenience
@app.get("/healthz")
async def root_healthz():
    return {"status": "ok"}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NODE_NOT_FOUND,
        409: ErrorCode.NODE_ALREADY_EXISTS,
        502: ErrorCode.INVOKE_FAILED,
        503: ErrorCode.INTERNAL_ERROR,
    }
    error_code = code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=error_code,
                message=str(exc.detail),
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errs = exc.errors()
    fields = {
        str(e["loc"][-1]): e["msg"].replace("Value error, ", "")
        for e in errs
        if e.get("loc")
    }
    first_msg = next(iter(fields.values()), "请求参数有误")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message=first_msg,
                details={"fields": fields},
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
            )
        ).model_dump(),
    )


# Serve Vue SPA in production (only when dist/ exists)
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")

