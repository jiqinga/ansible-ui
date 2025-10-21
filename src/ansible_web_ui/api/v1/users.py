"""
用户管理API端点

提供用户CRUD操作和管理功能的API。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.models.user import User, UserRole
from ansible_web_ui.services.user_service import UserService
from ansible_web_ui.auth.dependencies import (
    get_current_active_user,
    require_permission,
    get_admin_user
)
from ansible_web_ui.auth.permissions import Permission


router = APIRouter(prefix="/users", tags=["用户管理"])


# 请求和响应模型
class UserCreateRequest(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    role: UserRole = Field(default=UserRole.VIEWER, description="用户角色")
    is_active: bool = Field(default=True, description="是否激活")


class UserUpdateRequest(BaseModel):
    """更新用户请求模型"""
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    role: Optional[UserRole] = Field(None, description="用户角色")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        """从ORM对象创建响应模型"""
        data = {
            "id": obj.id,
            "username": obj.username,
            "email": obj.email,
            "full_name": obj.full_name,
            "role": obj.role,
            "is_active": obj.is_active,
            "is_superuser": obj.is_superuser,
            "last_login": obj.last_login.isoformat() if obj.last_login else None,
            "login_count": obj.login_count or 0,
            "created_at": obj.created_at.isoformat() if obj.created_at else "",
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else ""
        }
        return cls(**data)


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse] = Field(..., description="用户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class UserStatsResponse(BaseModel):
    """用户统计响应模型"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    admin_users: int = Field(..., description="管理员数量")
    operator_users: int = Field(..., description="操作员数量")
    viewer_users: int = Field(..., description="查看者数量")


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    new_password: str = Field(..., min_length=6, description="新密码")


@router.get("", response_model=UserListResponse, summary="获取用户列表")
async def get_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    role: Optional[UserRole] = Query(None, description="按角色筛选"),
    is_active: Optional[bool] = Query(None, description="按激活状态筛选"),
    search: Optional[str] = Query(None, description="搜索用户名或邮箱"),
    current_user: User = Depends(require_permission(Permission.VIEW_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户列表
    
    支持分页、筛选和搜索功能。
    需要查看用户权限。
    """
    user_service = UserService(db)
    
    # 构建筛选条件
    filters = {}
    if role is not None:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    
    # 获取用户列表
    users = await user_service.get_paginated(
        page=page,
        page_size=page_size,
        filters=filters,
        search_fields=["username", "email"] if search else None,
        search_value=search
    )
    
    # 获取总数
    total = await user_service.count(filters)
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=UserStatsResponse, summary="获取用户统计")
async def get_user_stats(
    current_user: User = Depends(require_permission(Permission.VIEW_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取用户统计信息
    
    需要查看用户权限。
    """
    user_service = UserService(db)
    stats = await user_service.get_user_stats()
    
    return UserStatsResponse(**stats)


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permission.VIEW_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取指定用户的详细信息
    
    需要查看用户权限。
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.from_orm(user)


@router.post("", response_model=UserResponse, summary="创建用户")
async def create_user(
    user_data: UserCreateRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建新用户
    
    需要创建用户权限。
    """
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    existing_user = await user_service.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await user_service.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    try:
        user = await user_service.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=user_data.is_active
        )
        
        return UserResponse.from_orm(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user: User = Depends(require_permission(Permission.UPDATE_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新用户信息
    
    需要更新用户权限。
    """
    user_service = UserService(db)
    
    # 检查用户是否存在
    existing_user = await user_service.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 如果更新邮箱，检查是否已被其他用户使用
    if user_data.email and user_data.email != existing_user.email:
        email_user = await user_service.get_by_email(user_data.email)
        if email_user and email_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户注册"
            )
    
    # 构建更新数据
    update_data = {}
    if user_data.email is not None:
        update_data["email"] = user_data.email
    if user_data.full_name is not None:
        update_data["full_name"] = user_data.full_name
    if user_data.role is not None:
        update_data["role"] = user_data.role
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    # 更新用户
    try:
        updated_user = await user_service.update(user_id, **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户失败"
            )
        
        return UserResponse.from_orm(updated_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )


@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permission.DELETE_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除用户
    
    需要删除用户权限。
    不能删除自己的账户。
    """
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    user_service = UserService(db)
    
    # 检查用户是否存在
    user = await user_service.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 删除用户
    try:
        success = await user_service.delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )
        
        return {"message": f"用户 {user.username} 已被删除"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.post("/{user_id}/activate", summary="激活用户")
async def activate_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permission.UPDATE_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    激活用户账户
    
    需要更新用户权限。
    """
    user_service = UserService(db)
    
    success = await user_service.activate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "用户已激活"}


@router.post("/{user_id}/deactivate", summary="停用用户")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permission.UPDATE_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    停用用户账户
    
    需要更新用户权限。
    不能停用自己的账户。
    """
    # 不能停用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能停用自己的账户"
        )
    
    user_service = UserService(db)
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "用户已停用"}


@router.post("/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(
    user_id: int,
    password_data: ResetPasswordRequest,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    重置用户密码
    
    需要管理员权限。
    """
    user_service = UserService(db)
    
    success = await user_service.update_password(user_id, password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": "密码重置成功"}


@router.put("/{user_id}/role", summary="更新用户角色")
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(require_permission(Permission.MANAGE_USER_ROLES)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新用户角色
    
    需要管理用户角色权限。
    不能修改自己的角色。
    """
    # 不能修改自己的角色
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    user_service = UserService(db)
    
    success = await user_service.update_user_role(user_id, role)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return {"message": f"用户角色已更新为 {role.value}"}


@router.get("/role/{role}", response_model=List[UserResponse], summary="按角色获取用户")
async def get_users_by_role(
    role: UserRole,
    current_user: User = Depends(require_permission(Permission.VIEW_USERS)),
    db: AsyncSession = Depends(get_db_session)
):
    """
    按角色获取用户列表
    
    需要查看用户权限。
    """
    user_service = UserService(db)
    users = await user_service.get_users_by_role(role)
    
    return [UserResponse.from_orm(user) for user in users]