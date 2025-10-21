"""
API v1路由器

汇总所有v1版本的API路由。
"""

from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .inventory import router as inventory_router
from .playbooks import router as playbooks_router
from .execution import router as execution_router
from .history import router as history_router
from .monitoring import router as monitoring_router
from .config import router as config_router
from .logging import router as logging_router
from .projects import router as projects_router
from .roles import router as roles_router

# 创建v1路由器
router = APIRouter()

# 注册子路由
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(inventory_router)
router.include_router(playbooks_router)
router.include_router(execution_router)
router.include_router(history_router)
router.include_router(monitoring_router)
router.include_router(config_router)
router.include_router(logging_router)
router.include_router(projects_router)
router.include_router(roles_router)

# v1版本信息端点
# 注意：此端点保持公开访问，不需要认证
# 用于服务发现、健康检查和API文档生成
# 不包含敏感信息，符合行业标准做法
@router.get("/info", tags=["系统"])
async def v1_info():
    """
    获取v1版本信息
    
    返回v1版本的详细信息和功能列表。
    
    ⚠️ 注意：此端点无需认证，用于服务发现和健康检查。
    """
    return {
        "version": "v1",
        "status": "stable",
        "message": "🎯 Ansible Web UI API v1 - 稳定版本",
        "features": {
            "authentication": "✅ JWT令牌认证",
            "user_management": "✅ 完整的用户管理功能",
            "role_based_access": "✅ 基于角色的访问控制",
            "password_security": "✅ 安全的密码哈希和验证",
            "inventory_management": "✅ Ansible主机清单管理",
            "host_management": "✅ 主机增删改查和连接测试",
            "group_management": "✅ 主机组管理和层级结构",
            "inventory_export_import": "✅ 多格式inventory导入导出",
            "playbook_management": "✅ Playbook文件管理和编辑",
            "playbook_validation": "✅ YAML语法和Ansible结构验证",
            "file_upload": "✅ Playbook文件上传和下载",
            "task_execution": "✅ Ansible任务异步执行",
            "real_time_logs": "✅ WebSocket实时日志推送",
            "task_management": "✅ 任务状态查询和取消",
            "connection_testing": "✅ 主机连接性测试",
            "execution_history": "✅ 执行历史记录和查询",
            "statistics_analytics": "✅ 执行统计和趋势分析",
            "system_monitoring": "✅ 系统资源监控",
            "health_checks": "✅ 系统健康检查和警告",
            "performance_reports": "✅ 性能分析报告",
            "config_management": "✅ 系统配置管理",
            "ansible_config": "✅ Ansible配置文件管理",
            "config_validation": "✅ 配置验证和默认值处理"
        },
        "endpoints": {
            "auth": "/api/v1/auth/*",
            "users": "/api/v1/users/*",
            "inventory": "/api/v1/inventory/*",
            "playbooks": "/api/v1/playbooks/*",
            "execution": "/api/v1/execution/*",
            "history": "/api/v1/history/*",
            "monitoring": "/api/v1/monitoring/*",
            "config": "/api/v1/config/*"
        }
    }
