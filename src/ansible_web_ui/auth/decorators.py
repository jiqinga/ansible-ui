"""
认证装饰器

提供基于装饰器的权限检查和认证功能。
"""

import functools
from typing import Callable, Any, Optional, List
from fastapi import HTTPException, status

from ansible_web_ui.models.user import User, UserRole
from ansible_web_ui.auth.permissions import Permission, PermissionManager


def require_permission(permission: Permission):
    """
    要求特定权限的装饰器
    
    Args:
        permission: 所需权限名称
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中查找用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # 从关键字参数中查找用户对象
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User) and key in ['user', 'current_user']:
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户认证信息"
                )
            
            # 检查权限
            if not PermissionManager.has_permission(user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(required_role: UserRole):
    """
    要求特定角色的装饰器
    
    Args:
        required_role: 所需角色
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中查找用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # 从关键字参数中查找用户对象
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User) and key in ['user', 'current_user']:
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户认证信息"
                )
            
            # 检查角色
            if not _check_user_role(user, required_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要 {required_role.value} 或更高权限"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_roles(required_roles: List[UserRole]):
    """
    要求多个角色之一的装饰器
    
    Args:
        required_roles: 所需角色列表
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中查找用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # 从关键字参数中查找用户对象
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User) and key in ['user', 'current_user']:
                        user = value
                        break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户认证信息"
                )
            
            # 检查是否有任一所需角色
            if not any(_check_user_role(user, role) for role in required_roles):
                role_names = [role.value for role in required_roles]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要以下角色之一: {', '.join(role_names)}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_active_user(func: Callable) -> Callable:
    """
    要求活跃用户的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 从参数中查找用户对象
        user = None
        for arg in args:
            if isinstance(arg, User):
                user = arg
                break
        
        # 从关键字参数中查找用户对象
        if not user:
            for key, value in kwargs.items():
                if isinstance(value, User) and key in ['user', 'current_user']:
                    user = value
                    break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未找到用户认证信息"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被停用"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    要求管理员权限的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    return require_role(UserRole.ADMIN)(func)


def require_operator(func: Callable) -> Callable:
    """
    要求操作员权限的装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    return require_roles([UserRole.ADMIN, UserRole.OPERATOR])(func)


def audit_log(action: str, resource: Optional[str] = None):
    """
    审计日志装饰器
    
    Args:
        action: 操作类型
        resource: 资源类型
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中查找用户对象
            user = None
            for arg in args:
                if isinstance(arg, User):
                    user = arg
                    break
            
            # 从关键字参数中查找用户对象
            if not user:
                for key, value in kwargs.items():
                    if isinstance(value, User) and key in ['user', 'current_user']:
                        user = value
                        break
            
            # 记录操作开始
            import logging
            logger = logging.getLogger(__name__)
            
            user_info = f"用户 {user.username}" if user else "匿名用户"
            resource_info = f" 资源 {resource}" if resource else ""
            
            logger.info(f"🔍 {user_info} 开始执行操作: {action}{resource_info}")
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                
                # 记录操作成功
                logger.info(f"✅ {user_info} 成功完成操作: {action}{resource_info}")
                
                return result
            except Exception as e:
                # 记录操作失败
                logger.error(f"❌ {user_info} 操作失败: {action}{resource_info}, 错误: {str(e)}")
                raise
        
        return wrapper
    return decorator


def _check_user_permission(user: User, permission: Permission) -> bool:
    """
    检查用户权限
    
    Args:
        user: 用户对象
        permission: 权限对象
        
    Returns:
        bool: 是否有权限
    """
    return PermissionManager.has_permission(user, permission)


def _check_user_role(user: User, required_role: UserRole) -> bool:
    """
    检查用户角色
    
    Args:
        user: 用户对象
        required_role: 所需角色
        
    Returns:
        bool: 是否有所需角色
    """
    if not user.is_active:
        return False
    
    if user.is_superuser:
        return True
    
    # 角色层级检查
    role_hierarchy = {
        UserRole.VIEWER: 0,
        UserRole.OPERATOR: 1,
        UserRole.ADMIN: 2
    }
    
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 0)
    
    return user_level >= required_level