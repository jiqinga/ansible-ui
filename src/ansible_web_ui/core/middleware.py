"""中间件模块

提供FastAPI应用所需的通用中间件。
"""

from __future__ import annotations

import time
import uuid
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from ansible_web_ui.core.logging import get_logger


class RequestContextMiddleware(BaseHTTPMiddleware):
    """为每个请求注入上下文信息的中间件。

    当前主要负责生成/传播`request_id`并记录基本的请求时长。
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = get_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.time()

        response: Response | None = None
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.time() - request.state.start_time) * 1000
            self._logger.bind(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                duration_ms=round(duration_ms, 2),
            ).exception("request.failed")
            raise
        else:
            duration_ms = (time.time() - request.state.start_time) * 1000
            self._logger.bind(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            ).info("request.completed")

        if response is not None:
            response.headers["X-Request-ID"] = request_id
        return response
