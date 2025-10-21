"""
用户服务

提供用户认证、授权和管理相关的业务逻辑。
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ansible_web_ui.models.user import User, UserRole
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.auth.security import (
    create_user_token,
    verify_token
)
from ansible_web_ui.auth.password_utils import (
    verify_password, 
    get_password_hash
)


class UserService(BaseService[User]):
    """
    用户服务类
    
    提供用户认证、密码管理、权限检查等功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名或邮箱
            password: 密码
            
        Returns:
            Optional[User]: 认证成功返回用户对象，失败返回None
        """
        # 支持用户名或邮箱登录
        result = await self.db.execute(
            select(User).where(
                or_(User.username == username, User.email == username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        # 更新登录信息
        user.update_last_login()
        await self.db.commit()
        
        return user

    def create_access_token(self, user: User) -> str:
        """
        创建访问令牌
        
        Args:
            user: 用户对象
            
        Returns:
            str: JWT访问令牌
        """
        return create_user_token(user)

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        根据令牌获取当前用户
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[User]: 用户对象或None
        """
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        return await self.get_by_id(int(user_id))

    async def create_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.VIEWER,
        is_active: bool = True
    ) -> User:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            full_name: 真实姓名
            role: 用户角色
            is_active: 是否激活
            
        Returns:
            User: 创建的用户对象
        """
        password_hash = get_password_hash(password)
        
        return await self.create(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=is_active
        )

    async def update_password(self, user_id: int, new_password: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            new_password: 新密码
            
        Returns:
            bool: 是否更新成功
        """
        password_hash = get_password_hash(new_password)
        user = await self.update(user_id, password_hash=password_hash)
        return user is not None

    async def change_password(
        self, 
        user_id: int, 
        old_password: str, 
        new_password: str
    ) -> bool:
        """
        修改用户密码（需要验证旧密码）
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            bool: 是否修改成功
        """
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        if not verify_password(old_password, user.password_hash):
            return False
        
        return await self.update_password(user_id, new_password)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            Optional[User]: 用户对象或None
        """
        return await self.get_by_field("username", username)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            Optional[User]: 用户对象或None
        """
        return await self.get_by_field("email", email)

    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """
        根据角色获取用户列表
        
        Args:
            role: 用户角色
            
        Returns:
            List[User]: 用户列表
        """
        return await self.get_by_filters({"role": role})

    async def activate_user(self, user_id: int) -> bool:
        """
        激活用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否激活成功
        """
        user = await self.update(user_id, is_active=True)
        return user is not None

    async def deactivate_user(self, user_id: int) -> bool:
        """
        停用用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否停用成功
        """
        user = await self.update(user_id, is_active=False)
        return user is not None

    async def update_user_role(self, user_id: int, role: UserRole) -> bool:
        """
        更新用户角色
        
        Args:
            user_id: 用户ID
            role: 新角色
            
        Returns:
            bool: 是否更新成功
        """
        user = await self.update(user_id, role=role)
        return user is not None

    async def check_permission(self, user: User, permission: str) -> bool:
        """
        检查用户权限
        
        Args:
            user: 用户对象
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        if not user.is_active:
            return False
        
        if user.is_superuser:
            return True
        
        # 权限映射
        permission_map = {
            "execute_tasks": user.can_execute_tasks,
            "manage_hosts": user.can_manage_hosts,
            "manage_playbooks": user.can_manage_playbooks,
            "admin": user.is_admin,
        }
        
        return permission_map.get(permission, False)

    async def get_user_stats(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_users = await self.count()
        active_users = await self.count({"is_active": True})
        admin_users = await self.count({"role": UserRole.ADMIN})
        operator_users = await self.count({"role": UserRole.OPERATOR})
        viewer_users = await self.count({"role": UserRole.VIEWER})
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "admin_users": admin_users,
            "operator_users": operator_users,
            "viewer_users": viewer_users
        }