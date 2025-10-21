"""
认证模块

提供JWT认证、权限检查和安全相关功能。
"""

# 延迟导入避免循环依赖
from .middleware import AuthMiddleware
from .decorators import require_permission, require_role
from .security import create_access_token, verify_token

__all__ = [
    "AuthMiddleware",
    "require_permission",
    "require_role",
    "create_access_token",
    "verify_token"
]