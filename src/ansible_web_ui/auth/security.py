"""
安全工具模块

提供JWT令牌生成、验证和认证相关功能。
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, status

from ansible_web_ui.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Optional[Dict[str, Any]]: 令牌载荷，如果无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def extract_token_from_header(authorization: str) -> Optional[str]:
    """
    从Authorization头中提取令牌
    
    Args:
        authorization: Authorization头的值
        
    Returns:
        Optional[str]: 提取的令牌，如果格式不正确则返回None
    """
    if not authorization:
        return None
    
    parts = authorization.split()
    
    if len(parts) != 2:
        return None
    
    scheme, token = parts
    
    if scheme.lower() != "bearer":
        return None
    
    return token


def create_user_token(user_id: int, username: str, role: str = "user", is_superuser: bool = False) -> str:
    """
    为用户创建令牌
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        is_superuser: 是否为超级用户
        
    Returns:
        str: JWT令牌
    """
    token_data = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "is_superuser": is_superuser
    }
    
    return create_access_token(token_data)


def create_refresh_token(user_id: int, username: str) -> str:
    """
    创建刷新令牌
    
    Args:
        user_id: 用户ID
        username: 用户名
        
    Returns:
        str: 刷新令牌
    """
    token_data = {
        "sub": str(user_id),
        "username": username,
        "type": "refresh"
    }
    
    # 刷新令牌有效期更长（7天）
    expires_delta = timedelta(days=7)
    
    return create_access_token(token_data, expires_delta)


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证刷新令牌
    
    Args:
        token: 刷新令牌
        
    Returns:
        Optional[Dict[str, Any]]: 令牌载荷，如果无效则返回None
    """
    payload = verify_token(token)
    
    if not payload:
        return None
    
    # 检查令牌类型
    if payload.get("type") != "refresh":
        return None
    
    return payload


def decode_token(token: str) -> Dict[str, Any]:
    """
    解码JWT令牌（不验证）
    
    Args:
        token: JWT令牌
        
    Returns:
        Dict[str, Any]: 令牌载荷
        
    Raises:
        HTTPException: 如果令牌无效
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        error_msg = str(e)
        if "expired" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
