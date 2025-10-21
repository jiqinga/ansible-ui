"""
用户数据模型

定义用户认证和授权相关的数据结构。
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from ansible_web_ui.models.base import BaseModel


class UserRole(str, Enum):
    """
    用户角色枚举
    """
    ADMIN = "admin"          # 管理员：完全访问权限
    OPERATOR = "operator"    # 操作员：可执行任务和管理资源
    VIEWER = "viewer"        # 查看者：只读权限


class User(BaseModel):
    """
    用户模型
    
    存储用户认证信息、角色权限和基本资料。
    """
    __tablename__ = "users"

    # 基本信息
    username = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="用户名"
    )
    email = Column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="邮箱地址"
    )
    full_name = Column(
        String(100), 
        nullable=True,
        comment="真实姓名"
    )
    
    # 认证信息
    password_hash = Column(
        String(255), 
        nullable=False,
        comment="密码哈希值"
    )
    
    # 权限和状态
    role = Column(
        SQLEnum(UserRole), 
        nullable=False, 
        default=UserRole.VIEWER,
        comment="用户角色"
    )
    is_active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="是否激活"
    )
    is_superuser = Column(
        Boolean, 
        nullable=False, 
        default=False,
        comment="是否超级用户"
    )
    
    # 登录信息
    last_login = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="最后登录时间"
    )
    login_count = Column(
        String(20), 
        nullable=False, 
        default="0",
        comment="登录次数"
    )
    
    # 关联关系
    task_executions = relationship(
        "TaskExecution", 
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', role='{self.role}')>"

    @property
    def is_admin(self) -> bool:
        """
        检查用户是否为管理员
        """
        return self.role == UserRole.ADMIN or self.is_superuser

    @property
    def can_execute_tasks(self) -> bool:
        """
        检查用户是否可以执行任务
        """
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR] or self.is_superuser

    @property
    def can_manage_hosts(self) -> bool:
        """
        检查用户是否可以管理主机
        """
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR] or self.is_superuser

    @property
    def can_manage_playbooks(self) -> bool:
        """
        检查用户是否可以管理Playbook
        """
        return self.role in [UserRole.ADMIN, UserRole.OPERATOR] or self.is_superuser

    def update_last_login(self) -> None:
        """
        更新最后登录时间和登录次数
        """
        self.last_login = datetime.utcnow()
        try:
            count = int(self.login_count)
            self.login_count = str(count + 1)
        except (ValueError, TypeError):
            self.login_count = "1"