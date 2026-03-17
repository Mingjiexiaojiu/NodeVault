import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.deps import get_current_user
from backend.database.session import get_db
from backend.models.node import Node, NodeInvocationLog
from backend.models.user import User
from backend.schemas.response import ApiResponse

router = APIRouter(prefix="/nodes", tags=["Stats"])


@router.get(
    "/{node_id}/stats",
    summary="Node 调用统计",
    description="聚合该 Node 在指定天数内的调用日志，返回成功率、延迟分布等统计数据。",
    responses={
        404: {"description": "Node 不存在"},
        422: {"description": "days 参数超出范围"},
    },
)
async def get_node_stats(
    node_id: uuid.UUID,
    days: int = Query(30, ge=1, le=365, description="统计最近 N 天，最大 365"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify node exists
    node_result = await db.execute(select(Node).where(Node.id == node_id))
    node = node_result.scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    since = datetime.utcnow() - timedelta(days=days)

    # Fetch all relevant logs
    logs_result = await db.execute(
        select(NodeInvocationLog)
        .where(
            NodeInvocationLog.node_id == node_id,
            NodeInvocationLog.created_at >= since,
        )
        .order_by(NodeInvocationLog.created_at)
    )
    logs = list(logs_result.scalars().all())

    if not logs:
        return ApiResponse(data={
            "node_id": str(node_id),
            "period_days": days,
            "total_invocations": 0,
            "success_rate": None,
            "avg_latency_ms": None,
            "p95_latency_ms": None,
            "p99_latency_ms": None,
            "daily_trend": [],
            "top_callers": [],
        })

    total = len(logs)
    success_count = sum(1 for l in logs if l.status == "success")
    success_rate = round(success_count / total, 4) if total else None

    latencies = [l.latency_ms for l in logs if l.latency_ms is not None]
    avg_latency = round(sum(latencies) / len(latencies)) if latencies else None

    def percentile(data: list[int], p: float) -> int | None:
        if not data:
            return None
        sorted_data = sorted(data)
        index = int(len(sorted_data) * p / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)

    # Daily trend
    daily: dict[str, dict] = {}
    for log in logs:
        day = log.created_at.strftime("%Y-%m-%d")
        if day not in daily:
            daily[day] = {"date": day, "count": 0, "errors": 0}
        daily[day]["count"] += 1
        if log.status != "success":
            daily[day]["errors"] += 1
    daily_trend = list(daily.values())

    # Top callers
    caller_counts: dict[str, int] = {}
    for log in logs:
        if log.invoked_by:
            key = str(log.invoked_by)
            caller_counts[key] = caller_counts.get(key, 0) + 1
    top_callers = sorted(
        [{"user": k, "count": v} for k, v in caller_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    return ApiResponse(data={
        "node_id": str(node_id),
        "period_days": days,
        "total_invocations": total,
        "success_rate": success_rate,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "daily_trend": daily_trend,
        "top_callers": top_callers,
    })
