"""FastAPI全局错误处理模块。

实现统一的错误响应格式、错误分类策略以及结构化日志记录。
"""

from __future__ import annotations

import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ansible_web_ui.core.logging import get_logger


logger = get_logger(__name__)


class ApplicationError(Exception):
    """应用自定义异常，用于携带统一的错误信息。"""

    def __init__(
        self,
        message: str,
        *,
        code: str = "APPLICATION_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


def register_exception_handlers(app) -> None:
    """为FastAPI应用注册全局异常处理器。"""

    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    error_code = exc.code or "APPLICATION_ERROR"
    _log_error(
        "warning",
        request,
        status_code=exc.status_code,
        error_code=error_code,
        message=exc.message,
        details=exc.details,
    )
    return _build_error_response(
        request,
        status_code=exc.status_code,
        message=exc.message,
        error_code=error_code,
        details=exc.details,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message, details, detail_code = _extract_http_detail(exc.detail)
    error_code = detail_code or _status_code_to_error_code(exc.status_code)

    log_level = "warning" if exc.status_code < 500 else "error"
    _log_error(
        log_level,
        request,
        status_code=exc.status_code,
        error_code=error_code,
        message=message,
        details=details,
    )

    return _build_error_response(
        request,
        status_code=exc.status_code,
        message=message,
        error_code=error_code,
        details=details,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    message = "请求参数验证失败"
    details = exc.errors()

    _log_error(
        "warning",
        request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message=message,
        details=details,
    )

    return _build_error_response(
        request,
        status_code=422,
        message=message,
        error_code="VALIDATION_ERROR",
        details=details,
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    message = "数据验证失败"
    details = exc.errors()

    _log_error(
        "warning",
        request,
        status_code=422,
        error_code="VALIDATION_ERROR",
        message=message,
        details=details,
    )

    return _build_error_response(
        request,
        status_code=422,
        message=message,
        error_code="VALIDATION_ERROR",
        details=details,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    message = "服务器内部错误"
    error_code = "INTERNAL_SERVER_ERROR"
    details = {"exception": type(exc).__name__}

    _log_error(
        "error",
        request,
        status_code=500,
        error_code=error_code,
        message=str(exc) or message,
        details={**details, "traceback": traceback.format_exc()},
    )

    return _build_error_response(
        request,
        status_code=500,
        message=message,
        error_code=error_code,
        details=details,
    )


def _extract_http_detail(detail: Any) -> Tuple[str, Optional[Any], Optional[str]]:
    if isinstance(detail, dict):
        message = detail.get("message") or detail.get("detail") or detail.get("error")
        error_code = detail.get("code")
        details = detail.get("details") or detail
        return message or "请求处理失败", details, error_code

    if isinstance(detail, list):
        return "请求处理失败", detail, None

    if detail is None:
        return "请求处理失败", None, None

    return str(detail), None, None


def _status_code_to_error_code(status_code: int) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "PERMISSION_DENIED",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT_ERROR",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
    }

    if status_code in mapping:
        return mapping[status_code]
    if status_code >= 500:
        return "SERVER_ERROR"
    return "APPLICATION_ERROR"


def _sanitize_for_json(obj: Any) -> Any:
    """清理对象使其可以被JSON序列化。
    
    处理bytes、datetime等不可序列化的类型。
    """
    if obj is None:
        return None
    
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            return f"<bytes: {len(obj)} bytes>"
    
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(item) for item in obj]
    
    if isinstance(obj, set):
        return [_sanitize_for_json(item) for item in obj]
    
    # 对于其他类型，尝试转换为字符串
    if not isinstance(obj, (str, int, float, bool)):
        try:
            return str(obj)
        except Exception:
            return f"<{type(obj).__name__}>"
    
    return obj


def _build_error_response(
    request: Request,
    *,
    status_code: int,
    message: str,
    error_code: str,
    details: Optional[Any] = None,
) -> JSONResponse:
    request_id = _get_request_id(request)
    
    # 清理details以确保可以JSON序列化
    sanitized_details = _sanitize_for_json(details) if details is not None else None
    
    payload: Dict[str, Any] = {
        "error": {
            "code": error_code,
            "message": message,
            "details": sanitized_details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
        }
    }

    response = JSONResponse(status_code=status_code, content=payload)
    response.headers["X-Request-ID"] = request_id
    return response


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid.uuid4())


def _log_error(
    level: str,
    request: Request,
    *,
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Any] = None,
) -> None:
    bound_logger = logger.bind(
        request_id=_get_request_id(request),
        method=request.method,
        path=str(request.url.path),
        status_code=status_code,
        error_code=error_code,
    )

    if details is not None:
        bound_logger = bound_logger.bind(details=details)

    if level == "warning":
        bound_logger.warning(message)
    elif level == "error":
        bound_logger.error(message)
    else:
        bound_logger.info(message)
