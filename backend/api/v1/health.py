from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.schemas.response import ApiResponse

router = APIRouter()


@router.get("/healthz", response_model=ApiResponse)
async def healthz(db: AsyncSession = Depends(get_db)) -> ApiResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    overall = "ok" if db_status == "healthy" else "degraded"
    return ApiResponse(
        data={"status": overall, "components": {"database": db_status}},
        message=overall,
    )
