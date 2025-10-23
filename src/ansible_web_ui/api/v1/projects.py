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
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_file_service = ProjectFileService(db)
    project_service = ProjectService(db, project_file_service)
    
    try:
        project = await project_service.create_project(
            name=project_data.name,
            display_name=project_data.display_name,
            description=project_data.description,
            project_type=project_data.project_type,
            template=project_data.template,
            created_by=current_user.id if current_user else None
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    🗑️ 删除项目
    
    删除项目及其所有关联的文件记录（通过ORM级联删除）
    """
    project_service = ProjectService(db)
    
    success = await project_service.delete_project(project_id=project_id)
    
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
    
    返回指定路径下的目录树结构（从数据库读取）
    """
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
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
        
        # 调用 ProjectFileService.get_file_tree 替代 ProjectService.get_project_files
        structure = await project_file_service.get_file_tree(
            project_id=project_id,
            relative_path=path,
            max_depth=max_depth
        )
        
        # 返回完整的响应（保持响应格式不变）
        return ProjectStructureResponse(
            project=project,
            structure=structure
        )
    except ValueError as e:
        # 路径不合法返回 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        # 文件不存在返回 404
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
    
    从数据库读取文件内容和元数据
    """
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
    try:
        # 验证项目存在
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 调用 ProjectFileService.read_file 方法
        content = await project_file_service.read_file(project_id, path)
        
        # 获取文件元数据
        from sqlalchemy import select
        from ansible_web_ui.models.project_file import ProjectFile
        
        query = select(ProjectFile).where(
            ProjectFile.project_id == project_id,
            ProjectFile.relative_path == path
        )
        result = await db.execute(query)
        file_record = result.scalar_one_or_none()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件不存在: {path}"
            )
        
        # 返回 FileContentResponse（包含 content、size、hash、last_modified）
        return FileContentResponse(
            path=path,
            content=content,
            size=file_record.file_size,
            hash=file_record.file_hash,
            last_modified=file_record.updated_at
        )
    except ValueError as e:
        # 编码错误返回 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        # 文件不存在返回 404
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
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
    try:
        # 验证项目存在
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 先尝试调用 update_file，如果文件不存在则调用 create_file
        try:
            file_record = await project_file_service.update_file(
                project_id=project_id,
                relative_path=file_data.path,
                content=file_data.content
            )
        except FileNotFoundError:
            # 文件不存在，创建新文件
            file_record = await project_file_service.create_file(
                project_id=project_id,
                relative_path=file_data.path,
                content=file_data.content
            )
        
        # 返回成功消息和文件元数据（size、hash）
        return {
            "message": "文件已保存",
            "path": file_data.path,
            "size": file_record.file_size,
            "hash": file_record.file_hash
        }
    except ValueError as e:
        # 文件过大返回 400
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
    
    在数据库中创建目录记录
    """
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
    try:
        # 验证项目存在
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 调用 ProjectFileService.create_directory 方法
        directory = await project_file_service.create_directory(
            project_id=project_id,
            relative_path=dir_data.path
        )
        
        # 返回成功消息和创建的目录信息
        return {
            "message": "目录已创建",
            "path": dir_data.path,
            "name": directory.filename
        }
    except ValueError as e:
        # 路径不合法返回 400
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
    
    更新数据库中的文件路径
    """
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
    try:
        # 验证项目存在
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 调用 ProjectFileService.move_file 方法
        success = await project_file_service.move_file(
            project_id=project_id,
            source_path=move_data.source,
            dest_path=move_data.destination
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文件移动失败"
            )
        
        # 返回成功消息
        return {
            "message": "文件已移动",
            "source": move_data.source,
            "destination": move_data.destination
        }
    except ValueError as e:
        # 目标已存在返回 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        # 源文件不存在返回 404
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
    
    从数据库中删除文件记录（会自动处理目录递归删除）
    """
    from ansible_web_ui.services.project_file_service import ProjectFileService
    
    project_service = ProjectService(db)
    project_file_service = ProjectFileService(db)
    
    try:
        # 验证项目存在
        project = await project_service.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"项目 {project_id} 不存在"
            )
        
        # 调用 ProjectFileService.delete_file 方法（会自动处理目录递归删除）
        deleted_count = await project_file_service.delete_file(
            project_id=project_id,
            relative_path=path
        )
        
        # 返回成功消息和删除的文件数量
        return {
            "message": "删除成功",
            "path": path,
            "deleted_count": deleted_count
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError as e:
        # 文件不存在返回 404
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
