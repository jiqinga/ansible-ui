"""
认证中间件

提供全局认证和安全检查功能。
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ansible_web_ui.auth.security import verify_token, extract_token_from_header


class AuthMiddleware(BaseHTTPMiddleware):
    """
    认证中间件
    
    在请求处理前进行认证检查和安全验证。
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        """
        初始化认证中间件
        
        Args:
            app: FastAPI应用实例
            exclude_paths: 排除认证检查的路径列表
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/static"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个处理函数
            
        Returns:
            Response: HTTP响应
        """
        start_time = time.time()
        
        # 检查是否需要跳过认证
        if self._should_skip_auth(request):
            response = await call_next(request)
            self._add_process_time_header(response, start_time)
            return response
        
        # 提取和验证令牌
        token = self._extract_token(request)
        if not token:
            return self._create_auth_error_response("缺少认证令牌")
        
        payload = verify_token(token)
        if not payload:
            return self._create_auth_error_response("无效的认证令牌")
        
        # 检查令牌是否过期
        if self._is_token_expired(payload):
            return self._create_auth_error_response("认证令牌已过期")
        
        # 将用户信息添加到请求状态
        request.state.user_id = payload.get("sub")
        request.state.username = payload.get("username")
        request.state.user_role = payload.get("role")
        request.state.is_superuser = payload.get("is_superuser", False)
        
        # 继续处理请求
        try:
            response = await call_next(request)
            self._add_process_time_header(response, start_time)
            return response
        except Exception as e:
            return self._create_error_response(str(e), 500)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """
        检查是否应该跳过认证
        
        Args:
            request: HTTP请求
            
        Returns:
            bool: 是否跳过认证
        """
        path = request.url.path
        
        # 检查排除路径
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        # OPTIONS请求跳过认证（CORS预检）
        if request.method == "OPTIONS":
            return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        从请求中提取令牌
        
        Args:
            request: HTTP请求
            
        Returns:
            Optional[str]: 提取的令牌或None
        """
        # 从Authorization头提取
        authorization = request.headers.get("Authorization")
        if authorization:
            return extract_token_from_header(authorization)
        
        # 从Cookie提取（可选）
        token = request.cookies.get("access_token")
        if token:
            return token
        
        # 从查询参数提取（不推荐，仅用于特殊情况）
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    def _is_token_expired(self, payload: dict) -> bool:
        """
        检查令牌是否过期
        
        Args:
            payload: 令牌载荷
            
        Returns:
            bool: 是否过期
        """
        exp = payload.get("exp")
        if not exp:
            return True
        
        current_time = time.time()
        return current_time > exp
    
    def _create_auth_error_response(self, message: str) -> JSONResponse:
        """
        创建认证错误响应
        
        Args:
            message: 错误消息
            
        Returns:
            JSONResponse: 错误响应
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "AUTHENTICATION_FAILED",
                    "message": message,
                    "timestamp": time.time()
                }
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    def _create_error_response(self, message: str, status_code: int) -> JSONResponse:
        """
        创建通用错误响应
        
        Args:
            message: 错误消息
            status_code: HTTP状态码
            
        Returns:
            JSONResponse: 错误响应
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": message,
                    "timestamp": time.time()
                }
            }
        )
    
    def _add_process_time_header(self, response: Response, start_time: float) -> None:
        """
        添加处理时间头
        
        Args:
            response: HTTP响应
            start_time: 开始时间
        """
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    防止API滥用和暴力攻击。
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        """
        初始化速率限制中间件
        
        Args:
            app: FastAPI应用实例
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # 简单内存存储，生产环境应使用Redis
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求
        
        Args:
            request: HTTP请求
            call_next: 下一个处理函数
            
        Returns:
            Response: HTTP响应
        """
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # 清理过期记录
        self._cleanup_expired_records(current_time)
        
        # 检查速率限制
        if self._is_rate_limited(client_ip, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"请求过于频繁，请在 {self.window_seconds} 秒后重试",
                        "timestamp": current_time
                    }
                },
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Window": str(self.window_seconds)
                }
            )
        
        # 记录请求
        self._record_request(client_ip, current_time)
        
        # 继续处理请求
        response = await call_next(request)
        
        # 添加速率限制头
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window_seconds)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端IP地址
        
        Args:
            request: HTTP请求
            
        Returns:
            str: 客户端IP地址
        """
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """
        检查是否达到速率限制
        
        Args:
            client_ip: 客户端IP
            current_time: 当前时间
            
        Returns:
            bool: 是否达到限制
        """
        if client_ip not in self.request_counts:
            return False
        
        window_start = current_time - self.window_seconds
        recent_requests = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > window_start
        ]
        
        return len(recent_requests) >= self.max_requests
    
    def _record_request(self, client_ip: str, current_time: float) -> None:
        """
        记录请求
        
        Args:
            client_ip: 客户端IP
            current_time: 当前时间
        """
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip].append(current_time)
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """
        获取剩余请求数
        
        Args:
            client_ip: 客户端IP
            current_time: 当前时间
            
        Returns:
            int: 剩余请求数
        """
        if client_ip not in self.request_counts:
            return self.max_requests
        
        window_start = current_time - self.window_seconds
        recent_requests = [
            req_time for req_time in self.request_counts[client_ip]
            if req_time > window_start
        ]
        
        return max(0, self.max_requests - len(recent_requests))
    
    def _cleanup_expired_records(self, current_time: float) -> None:
        """
        清理过期记录
        
        Args:
            current_time: 当前时间
        """
        window_start = current_time - self.window_seconds
        
        for client_ip in list(self.request_counts.keys()):
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if req_time > window_start
            ]
            
            # 删除空记录
            if not self.request_counts[client_ip]:
                del self.request_counts[client_ip]