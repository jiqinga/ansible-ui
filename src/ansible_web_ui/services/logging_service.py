"""
日志服务模块

提供审计日志和系统日志记录功能。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
import structlog

from ansible_web_ui.services.base import BaseService
from ansible_web_ui.utils.timezone import now

logger = structlog.get_logger(__name__)


class AuditLogService(BaseService):
    """
    审计日志服务
    
    记录和查询系统审计日志。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化审计日志服务
        
        Args:
            db: 数据库会话
        """
        super().__init__(db)
        self.logger = logger.bind(service="audit_log")
    
    async def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success"
    ) -> bool:
        """
        记录用户操作
        
        Args:
            user_id: 用户ID
            action: 操作类型（create, update, delete, view等）
            resource_type: 资源类型（host, playbook, task等）
            resource_id: 资源ID
            details: 操作详情
            ip_address: IP地址
            user_agent: 用户代理
            status: 操作状态（success, failed）
            
        Returns:
            bool: 是否记录成功
        """
        try:
            # 使用 structlog 记录审计日志
            self.logger.info(
                "audit_log",
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
                timestamp=now().isoformat()
            )
            
            # TODO: 如果需要，可以将审计日志存储到数据库
            # 目前使用 structlog 记录到文件
            
            return True
            
        except Exception as e:
            self.logger.error(
                "failed_to_log_audit",
                error=str(e),
                user_id=user_id,
                action=action
            )
            return False
    
    async def log_login(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True
    ) -> bool:
        """
        记录登录操作
        
        Args:
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            success: 是否成功
            
        Returns:
            bool: 是否记录成功
        """
        return await self.log_action(
            user_id=user_id,
            action="login",
            resource_type="auth",
            details={"username": username},
            ip_address=ip_address,
            user_agent=user_agent,
            status="success" if success else "failed"
        )
    
    async def log_logout(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        记录登出操作
        
        Args:
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            
        Returns:
            bool: 是否记录成功
        """
        return await self.log_action(
            user_id=user_id,
            action="logout",
            resource_type="auth",
            details={"username": username},
            ip_address=ip_address,
            status="success"
        )
    
    async def log_resource_access(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        action: str = "view",
        ip_address: Optional[str] = None
    ) -> bool:
        """
        记录资源访问
        
        Args:
            user_id: 用户ID
            resource_type: 资源类型
            resource_id: 资源ID
            action: 操作类型
            ip_address: IP地址
            
        Returns:
            bool: 是否记录成功
        """
        return await self.log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status="success"
        )
    
    async def log_config_change(
        self,
        user_id: int,
        config_key: str,
        old_value: Any,
        new_value: Any,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        记录配置变更
        
        Args:
            user_id: 用户ID
            config_key: 配置键
            old_value: 旧值
            new_value: 新值
            ip_address: IP地址
            
        Returns:
            bool: 是否记录成功
        """
        return await self.log_action(
            user_id=user_id,
            action="update",
            resource_type="config",
            details={
                "config_key": config_key,
                "old_value": old_value,
                "new_value": new_value
            },
            ip_address=ip_address,
            status="success"
        )
    
    async def log_task_execution(
        self,
        user_id: int,
        task_id: int,
        task_type: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        记录任务执行
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            task_type: 任务类型
            status: 执行状态
            details: 执行详情
            
        Returns:
            bool: 是否记录成功
        """
        return await self.log_action(
            user_id=user_id,
            action="execute",
            resource_type="task",
            resource_id=task_id,
            details={
                "task_type": task_type,
                **(details or {})
            },
            status=status
        )
