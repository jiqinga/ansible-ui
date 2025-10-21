"""
主应用程序入口点

这个模块包含FastAPI应用程序的主要配置和启动逻辑。
"""

import socket
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ansible_web_ui.core.config import settings
from ansible_web_ui.core.error_handlers import register_exception_handlers
from ansible_web_ui.core.logging import setup_logging
from ansible_web_ui.core.middleware import RequestContextMiddleware
from ansible_web_ui.websocket import get_websocket_event_listener


def get_local_ip() -> str:
    """
    获取本机IP地址
    
    返回:
        str: 本机IP地址
    """
    try:
        # 创建一个UDP socket来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def get_dynamic_cors_origins() -> list[str]:
    """
    动态生成CORS允许的源列表
    
    包括配置文件中的源和基于本机IP的源
    
    返回:
        list[str]: CORS允许的源列表
    """
    origins = list(settings.ALLOWED_ORIGINS)
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    # 添加基于本机IP的源
    dynamic_origins = [
        f"http://{local_ip}:3000",
        f"http://{local_ip}:8000",
        f"https://{local_ip}:3000",
        f"https://{local_ip}:8000",
    ]
    
    # 合并并去重
    all_origins = list(set(origins + dynamic_origins))
    
    print(f"🌐 本机IP地址: {local_ip}")
    print(f"🔗 CORS允许的源: {all_origins}")
    
    return all_origins


def create_app() -> FastAPI:
    """
    创建并配置FastAPI应用程序实例
    
    返回:
        FastAPI: 配置好的应用程序实例
    """
    # 设置日志
    setup_logging()
    
    # 创建FastAPI应用
    app = FastAPI(
        title="Ansible Web UI",
        description="现代化的Ansible Web用户界面，提供玻璃态设计风格的自动化管理平台",
        version="0.1.0",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
    )

    # 注入请求上下文中间件，提供request_id等公共信息
    app.add_middleware(RequestContextMiddleware)

    # 配置CORS - 使用动态生成的源列表
    cors_origins = get_dynamic_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册全局异常处理器
    register_exception_handlers(app)

    ws_listener = get_websocket_event_listener()

    @app.on_event("startup")
    async def startup_event():
        """应用启动事件处理"""
        # 🚀 自动创建性能索引和优化数据库
        from ansible_web_ui.core.db_init import initialize_database_optimizations
        await initialize_database_optimizations()
        
        # 启动WebSocket监听器
        await ws_listener.start()

    @app.on_event("shutdown")
    async def stop_websocket_listener():
        await ws_listener.stop()
    
    # 添加认证中间件（可选，根据需要启用）
    # from ansible_web_ui.auth.middleware import AuthMiddleware, RateLimitMiddleware
    # app.add_middleware(AuthMiddleware)
    # app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
    
    # 添加API路由
    from ansible_web_ui.api import api_router
    app.include_router(api_router, prefix="/api")
    
    # 添加根级别的健康检查端点
    @app.get("/health", tags=["系统"])
    async def root_health_check():
        """
        根级别健康检查端点
        
        用于负载均衡器和监控系统检查服务状态。
        """
        return {
            "status": "healthy",
            "message": "🌟 Ansible Web UI 服务运行正常",
            "service": "ansible-web-ui",
            "version": "0.1.0"
        }
    
    # 添加根级别的欢迎页面
    @app.get("/", tags=["系统"])
    async def root():
        """
        根路径欢迎页面
        
        提供服务基本信息和API文档链接。
        """
        return {
            "message": "🎨 欢迎使用 Ansible Web UI",
            "description": "现代化的Ansible Web用户界面，提供玻璃态设计风格的自动化管理平台",
            "version": "0.1.0",
            "api_docs": "/api/docs" if settings.DEBUG else "API文档在生产环境中不可用",
            "api_health": "/api/health",
            "features": [
                "🔒 安全的用户认证和授权",
                "👥 完整的用户管理功能", 
                "🎯 基于角色的访问控制",
                "🚀 现代化的RESTful API",
                "🎨 玻璃态UI设计风格"
            ]
        }
    
    return app


def main():
    """主函数 - 启动应用程序"""
    uvicorn.run(
        "ansible_web_ui.main:create_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )


if __name__ == "__main__":
    main()
