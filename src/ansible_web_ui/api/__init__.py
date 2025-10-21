"""
API模块

提供RESTful API端点。
"""

from fastapi import APIRouter
from .v1.router import router as v1_router

# 创建主API路由器
api_router = APIRouter()

# 包含v1版本的路由
api_router.include_router(v1_router, prefix="/v1")

# 根级别的健康检查端点
@api_router.get("/health", tags=["系统"])
async def api_health_check():
    """
    API健康检查端点
    
    用于检查API服务是否正常运行。
    """
    return {
        "status": "healthy",
        "message": "🚀 Ansible Web UI API 运行正常",
        "api_version": "1.0.0",
        "service": "ansible-web-ui"
    }


# 根级别的版本信息端点
@api_router.get("/version", tags=["系统"])
async def get_api_version():
    """
    获取API版本信息
    
    返回当前API的版本和支持的功能。
    """
    return {
        "api_version": "1.0.0",
        "supported_versions": ["v1"],
        "features": [
            "用户认证和授权",
            "用户管理",
            "基于角色的访问控制",
            "JWT令牌认证",
            "健康检查"
        ],
        "documentation": {
            "swagger_ui": "/api/docs",
            "redoc": "/api/redoc"
        }
    }