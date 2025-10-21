"""
认证API端点

提供用户登录、注册、令牌刷新等认证相关的API。
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from ansible_web_ui.core.database import get_db_session
from ansible_web_ui.models.user import User, UserRole
from ansible_web_ui.services.user_service import UserService
from ansible_web_ui.auth.dependencies import get_current_active_user, get_optional_user
from ansible_web_ui.auth.security import (
    create_user_token,
    create_refresh_token,
    verify_refresh_token
)
from ansible_web_ui.auth.password_utils import get_password_hash


router = APIRouter(prefix="/auth", tags=["认证"])


# 请求和响应模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class UserInfoResponse(BaseModel):
    """用户信息响应模型"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级用户")
    last_login: Optional[str] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")

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
            "login_count": obj.login_count or 0
        }
        return cls(**data)


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱地址
    - **password**: 用户密码
    
    返回访问令牌和刷新令牌。
    """
    user_service = UserService(db)
    
    # 验证用户凭据
    user = await user_service.authenticate(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成令牌
    access_token = create_user_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        is_superuser=user.is_superuser
    )
    refresh_token = create_refresh_token(user.id, user.username)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60  # 30分钟
    )


@router.post("/login/form", response_model=TokenResponse, summary="表单登录")
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session)
):
    """
    OAuth2兼容的表单登录
    
    支持标准的OAuth2密码流程。
    """
    user_service = UserService(db)
    
    # 验证用户凭据
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成令牌
    access_token = create_user_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        is_superuser=user.is_superuser
    )
    refresh_token = create_refresh_token(user.id, user.username)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=30 * 60
    )


@router.post("/register", response_model=UserInfoResponse, summary="用户注册")
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    用户注册
    
    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少6字符）
    - **full_name**: 真实姓名（可选）
    
    新注册用户默认角色为查看者。
    """
    user_service = UserService(db)
    
    # 检查用户名是否已存在
    existing_user = await user_service.get_by_username(register_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await user_service.get_by_email(register_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建新用户
    try:
        user = await user_service.create_user(
            username=register_data.username,
            email=register_data.email,
            password=register_data.password,
            full_name=register_data.full_name,
            role=UserRole.VIEWER,  # 默认角色
            is_active=True
        )
        
        return UserInfoResponse.from_orm(user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    刷新访问令牌
    
    使用刷新令牌获取新的访问令牌。
    """
    # 验证刷新令牌
    payload = verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 从payload中提取用户ID
    user_id = int(payload.get("sub"))
    
    # 获取用户信息
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被停用"
        )
    
    # 生成新令牌
    access_token = create_user_token(
        user_id=user.id,
        username=user.username,
        role=user.role.value if hasattr(user.role, 'value') else str(user.role),
        is_superuser=user.is_superuser
    )
    new_refresh_token = create_refresh_token(user.id, user.username)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=30 * 60
    )


@router.get("/me", response_model=UserInfoResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的信息
    
    需要有效的访问令牌。
    """
    return UserInfoResponse.from_orm(current_user)


@router.put("/me", response_model=UserInfoResponse, summary="更新当前用户信息")
async def update_current_user_info(
    full_name: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新当前用户信息
    
    用户只能更新自己的基本信息。
    """
    user_service = UserService(db)
    
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    
    if update_data:
        updated_user = await user_service.update(current_user.id, **update_data)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户信息失败"
            )
        return UserInfoResponse.from_orm(updated_user)
    
    return UserInfoResponse.from_orm(current_user)


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    修改当前用户密码
    
    需要提供旧密码进行验证。
    """
    user_service = UserService(db)
    
    # 修改密码
    success = await user_service.change_password(
        current_user.id,
        password_data.old_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    return {"message": "密码修改成功"}


@router.post("/logout", summary="用户注销")
async def logout(
    response: Response,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    用户注销
    
    清除客户端的认证信息。
    """
    # 清除Cookie中的令牌（如果有的话）
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    
    return {"message": "注销成功"}


@router.get("/check", summary="检查认证状态")
async def check_auth_status(
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    检查当前认证状态
    
    返回用户是否已认证的信息。
    """
    if current_user:
        return {
            "authenticated": True,
            "user": UserInfoResponse.from_orm(current_user)
        }
    else:
        return {
            "authenticated": False,
            "user": None
        }