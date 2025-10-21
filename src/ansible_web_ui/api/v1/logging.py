"""日志查询 API。"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool

from ansible_web_ui.auth.dependencies import get_admin_user
from ansible_web_ui.models.user import User
from ansible_web_ui.schemas.logging_schemas import LogQueryFilters, LogQueryResponse
from ansible_web_ui.services.logging_service import AuditLogService


router = APIRouter(prefix="/logs", tags=["日志"])


@router.get("/", response_model=LogQueryResponse, summary="查询审计日志")
async def query_audit_logs(
    levels: Optional[List[str]] = Query(
        default=None,
        description="需要匹配的日志级别，例如 level=info&level=error",
        alias="level",
    ),
    start_time: Optional[datetime] = Query(
        default=None,
        description="起始时间 (ISO 8601)",
    ),
    end_time: Optional[datetime] = Query(
        default=None,
        description="结束时间 (ISO 8601)",
    ),
    keyword: Optional[str] = Query(
        default=None,
        description="关键字匹配",
    ),
    logger: Optional[str] = Query(
        default=None,
        description="日志记录器名称",
    ),
    request_id: Optional[str] = Query(
        default=None,
        description="请求 ID",
    ),
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=20, ge=1, le=200, description="每页条数"),
    _user: User = Depends(get_admin_user),
) -> LogQueryResponse:
    """根据过滤条件查询审计日志。"""

    filters = LogQueryFilters(
        levels=levels,
        start_time=start_time,
        end_time=end_time,
        keyword=keyword,
        logger=logger,
        request_id=request_id,
        page=page,
        page_size=page_size,
    )

    service = AuditLogService()
    return await run_in_threadpool(service.query_logs, filters)
