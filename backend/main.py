from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.v1.router import api_router
from backend.api.v1.mcp import get_mcp_app_with_auth
from backend.core.search import NodeSearchIndex, sync_search_index
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

    # 启动时全量同步搜索索引，确保与数据库一致
    try:
        await sync_search_index()
        logger.info("meilisearch_sync_done")
    except Exception as exc:
        logger.warning("meilisearch_sync_failed", error=str(exc))

    yield
    await engine.dispose()
    logger.info("backend_shutdown")


# _sync_search_index 已迁移到 backend.core.search.sync_search_index


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

# MCP Server（SSE transport）— 挂载为子应用，路径 /mcp，需要 API Key 鉴权
app.mount("/mcp", get_mcp_app_with_auth())


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
        404: ErrorCode.NOT_FOUND,
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
    import traceback
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        traceback=traceback.format_exc(),
    )
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
    # 挂载 /assets 静态资源目录（JS/CSS/fonts 等）
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    # Catch-all：先尝试返回 dist 目录下的真实文件（favicon、logo 等），
    # 文件不存在时统一返回 index.html，从而支持 SPA 前端路由刷新
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(request: Request, full_path: str):
        static_file = _frontend_dist / full_path
        if full_path and static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        return FileResponse(str(_frontend_dist / "index.html"))

