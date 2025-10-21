"""
FastAPI依赖项

提供用户认证和权限检查的依赖项。
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.models.user import User, UserRole
# 延迟导入避免循环依赖
from ansible_web_ui.auth.security import verify_token
from ansible_web_ui.auth.permissions import Permission, PermissionManager


# HTTP Bearer认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    获取当前用户（可选）
    
    Args:
        credentials: HTTP认证凭据
        db: 数据库会话
        
    Returns:
        Optional[User]: 当前用户或None
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    try:
        # 延迟导入避免循环依赖
        from ansible_web_ui.services.user_service import UserService
        user_service = UserService(db)
        user = await user_service.get_by_id(int(user_id))
        return user
    except (ValueError, Exception):
        return None


async def get_current_active_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户（必需）
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 当前活跃用户
        
    Raises:
        HTTPException: 用户未认证或未激活
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供有效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被停用"
        )
    
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取管理员用户
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 管理员用户
        
    Raises:
        HTTPException: 用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user


async def get_operator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    获取操作员用户（管理员或操作员）
    
    Args:
        current_user: 当前用户
        
    Returns:
        User: 操作员用户
        
    Raises:
        HTTPException: 用户不是操作员
    """
    if not current_user.can_execute_tasks:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要操作员权限"
        )
    
    return current_user


def require_role(required_role: UserRole):
    """
    要求特定角色的依赖项工厂
    
    Args:
        required_role: 所需角色
        
    Returns:
        Callable: 依赖项函数
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        # 角色层级检查
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.OPERATOR: 1,
            UserRole.ADMIN: 2
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role.value} 或更高权限"
            )
        
        return current_user
    
    return role_checker


def require_permission(permission: Permission):
    """
    要求特定权限的依赖项工厂
    
    Args:
        permission: 所需权限
        
    Returns:
        Callable: 依赖项函数
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db_session)
    ) -> User:
        if not PermissionManager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {permission.value}"
            )
        
        return current_user
    
    return permission_checker


async def get_optional_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> Optional[User]:
    """
    获取可选用户（用于公开端点）
    
    Args:
        current_user: 当前用户
        
    Returns:
        Optional[User]: 当前用户或None
    """
    return current_user