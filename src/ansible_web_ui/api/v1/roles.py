"""
🎭 Role管理API端点

提供Ansible Role的CRUD操作和结构查询功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_async_db as get_db
from ansible_web_ui.auth.dependencies import get_current_user
from ansible_web_ui.models.user import User
from ansible_web_ui.services.role_service import RoleService
from ansible_web_ui.schemas.role_schemas import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse,
    RoleStructureResponse,
    RoleFilesResponse,
)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=RoleListResponse)
async def get_roles(
    project_id: Optional[int] = Query(None, description="按项目ID过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📋 获取Role列表
    
    支持按项目过滤和分页查询
    """
    role_service = RoleService(db)
    
    if project_id:
        roles = await role_service.get_roles_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit
        )
        total = await role_service.count_by_project(project_id)
    else:
        roles = await role_service.get_all(skip=skip, limit=limit)
        total = await role_service.count()
    
    return RoleListResponse(
        roles=roles,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✨ 创建新Role
    
    支持选择Role模板：
    - basic: 基础结构（tasks, handlers, defaults, meta）
    - full: 完整结构（所有标准目录）
    - minimal: 最小结构（仅tasks）
    """
    role_service = RoleService(db)
    
    try:
        role = await role_service.create_role(
            project_id=role_data.project_id,
            role_name=role_data.name,
            description=role_data.description,
            template=role_data.template
        )
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Role失败: {str(e)}"
        )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔍 获取Role详情
    """
    role_service = RoleService(db)
    role = await role_service.get_by_id(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} 不存在"
        )
    
    return role


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✏️ 更新Role信息
    """
    role_service = RoleService(db)
    
    try:
        role = await role_service.update_role(
            role_id=role_id,
            **role_data.model_dump(exclude_unset=True)
        )
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role {role_id} 不存在"
            )
        
        return role
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    delete_files: bool = Query(False, description="是否同时删除文件系统中的Role文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ 删除Role
    
    参数:
    - delete_files: 是否同时删除文件系统中的Role文件（默认false）
    """
    role_service = RoleService(db)
    
    success = await role_service.delete_role(
        role_id=role_id,
        delete_files=delete_files
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role {role_id} 不存在"
        )


# ==================== Role结构查询API ====================

@router.get("/{role_id}/structure", response_model=RoleStructureResponse)
async def get_role_structure(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🌲 获取Role的目录结构
    
    动态扫描文件系统，返回Role的实际目录结构
    """
    role_service = RoleService(db)
    
    try:
        structure = await role_service.get_role_structure(role_id)
        return structure
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{role_id}/files", response_model=RoleFilesResponse)
async def get_role_files(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📄 获取Role的文件列表
    
    返回扁平化的文件列表，包含所有目录下的文件
    """
    role_service = RoleService(db)
    
    try:
        files = await role_service.get_role_files(role_id)
        return files
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
