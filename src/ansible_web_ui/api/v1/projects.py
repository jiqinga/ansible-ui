"""
📦 项目管理API端点

提供项目的CRUD操作和文件管理功能
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_async_db as get_db
from ansible_web_ui.auth.dependencies import get_current_user
from ansible_web_ui.models.user import User
from ansible_web_ui.services.project_service import ProjectService
from ansible_web_ui.schemas.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectStructureResponse,
    ProjectValidationResponse,
    CreateDirectoryRequest,
    MoveFileRequest,
    DeleteFileRequest,
    FileContentRequest,
    FileContentResponse,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectListResponse)
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📋 获取项目列表
    
    支持分页查询
    """
    project_service = ProjectService(db)
    projects = await project_service.get_all(skip=skip, limit=limit)
    total = await project_service.count()
    
    return ProjectListResponse(
        projects=projects,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✨ 创建新项目
    
    支持选择项目模板：
    - standard: 标准Ansible项目结构
    - simple: 简单单文件项目
    - role-based: 以Role为中心的项目
    """
    project_service = ProjectService(db)
    
    try:
        project = await project_service.create_project(
            name=project_data.name,
            display_name=project_data.display_name,
            description=project_data.description,
            project_type=project_data.project_type,
            template=project_data.template,
            created_by=current_user.id
        )
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔍 获取项目详情
    """
    project_service = ProjectService(db)
    project = await project_service.get_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✏️ 更新项目信息
    """
    project_service = ProjectService(db)
    
    try:
        project = await project_service.update_project(
            project_id=project_id,
            **project_data.model_dump(exclude_unset=True)
        )
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    delete_files: bool = Query(False, description="是否同时删除文件系统中的项目文件"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ 删除项目
    
    参数:
    - delete_files: 是否同时删除文件系统中的项目文件（默认false）
    """
    project_service = ProjectService(db)
    
    success = await project_service.delete_project(
        project_id=project_id,
        delete_files=delete_files
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"项目 {project_id} 不存在"
        )


# ==================== 文件操作API ====================

@router.get("/{project_id}/files", response_model=ProjectStructureResponse)
async def get_project_files(
    project_id: int,
    path: str = Query("", description="相对路径，默认为项目根目录"),
    max_depth: int = Query(10, ge=1, le=20, description="最大递归深度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📁 获取项目文件树
    
    返回指定路径下的目录树结构
    """
    project_service = ProjectService(db)
    
    try:
        # 获取项目信息
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 确保 path 是字符串，处理 None 的情况
        if path is None:
            path = ""
        
        # 获取文件树结构
        structure = await project_service.get_project_files(
            project_id=project_id,
            relative_path=path,
            max_depth=max_depth
        )
        
        # 返回完整的响应
        return ProjectStructureResponse(
            project=project,
            structure=structure
        )
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


@router.get("/{project_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    project_id: int,
    path: str = Query(..., description="文件相对路径"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📄 读取文件内容
    """
    project_service = ProjectService(db)
    
    try:
        content = await project_service.read_file(project_id, path)
        return FileContentResponse(
            path=path,
            content=content
        )
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


@router.post("/{project_id}/files/content", status_code=status.HTTP_201_CREATED)
async def write_file_content(
    project_id: int,
    file_data: FileContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✍️ 写入文件内容
    
    如果文件不存在则创建，存在则覆盖
    """
    project_service = ProjectService(db)
    
    try:
        await project_service.write_file(
            project_id=project_id,
            relative_path=file_data.path,
            content=file_data.content
        )
        return {"message": "文件写入成功", "path": file_data.path}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/files/directory", status_code=status.HTTP_201_CREATED)
async def create_directory(
    project_id: int,
    dir_data: CreateDirectoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    📂 在项目中创建目录
    """
    project_service = ProjectService(db)
    
    try:
        await project_service.create_directory_in_project(
            project_id=project_id,
            relative_path=dir_data.path
        )
        return {"message": "目录创建成功", "path": dir_data.path}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/files/move")
async def move_file(
    project_id: int,
    move_data: MoveFileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🔄 在项目中移动文件
    """
    project_service = ProjectService(db)
    
    try:
        await project_service.move_file_in_project(
            project_id=project_id,
            source_relative=move_data.source,
            dest_relative=move_data.destination
        )
        return {
            "message": "文件移动成功",
            "source": move_data.source,
            "destination": move_data.destination
        }
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


@router.delete("/{project_id}/files")
async def delete_file(
    project_id: int,
    path: str = Query(..., description="要删除的文件或目录相对路径"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ 删除项目中的文件或目录
    """
    project_service = ProjectService(db)
    
    try:
        await project_service.delete_file_in_project(
            project_id=project_id,
            relative_path=path
        )
        return {"message": "删除成功", "path": path}
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


# ==================== 项目验证API ====================

@router.post("/{project_id}/validate", response_model=ProjectValidationResponse)
async def validate_project_structure(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ 验证项目结构完整性
    
    检查项目是否包含必需的目录和文件
    """
    project_service = ProjectService(db)
    
    try:
        validation_result = await project_service.validate_project_structure(project_id)
        return validation_result
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
