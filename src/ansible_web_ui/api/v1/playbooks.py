"""
Playbook管理API端点

提供Playbook的CRUD操作、文件上传、验证等功能的RESTful API。
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ansible_web_ui.core.database import get_async_db_session
from ansible_web_ui.services.playbook_service import PlaybookService
from ansible_web_ui.services.file_service import FileService
from ansible_web_ui.schemas.playbook_schemas import (
    PlaybookCreate, PlaybookUpdate, PlaybookInfo, PlaybookContent,
    PlaybookListResponse, PlaybookUploadResponse, PlaybookValidationResult
)
from ansible_web_ui.auth.dependencies import get_current_active_user as get_current_user
from ansible_web_ui.models.user import User

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("/files", summary="浏览Playbook文件")
async def browse_playbook_files(
    path: str = Query("", description="文件路径，空字符串表示根目录"),
    current_user: User = Depends(get_current_user)
):
    """
    浏览文件系统中的Playbook文件和目录
    
    返回指定路径下的文件和子目录列表。
    """
    file_service = FileService()
    
    try:
        # 如果path为空，使用playbooks根目录
        if not path or path == "":
            from pathlib import Path
            playbooks_dir = Path("playbooks")
            playbooks_dir.mkdir(exist_ok=True)
            path = "playbooks"
        
        files = await file_service.list_files(path)
        return {"files": files}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"路径不存在: {path}"
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限访问: {path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"浏览文件失败: {str(e)}"
        )


@router.get("/content", summary="获取文件内容")
async def get_file_content(
    path: str = Query(..., description="文件路径"),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定文件的内容
    """
    file_service = FileService()
    
    try:
        content = await file_service.read_file(path)
        return {"content": content, "path": path}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件不存在: {path}"
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限读取: {path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取文件失败: {str(e)}"
        )


@router.put("/content", summary="保存文件内容")
async def save_file_content(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    保存文件内容到指定路径
    
    请求体格式:
    {
        "path": "文件路径",
        "content": "文件内容"
    }
    """
    file_service = FileService()
    
    path = request_data.get("path")
    content = request_data.get("content")
    
    if not path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必需参数: path"
        )
    
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必需参数: content"
        )
    
    try:
        await file_service.write_file(path, content)
        return {"message": "文件保存成功", "path": path}
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"没有权限写入: {path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败: {str(e)}"
        )


@router.get("/count", summary="获取Playbook数量")
async def get_playbooks_count(
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_valid: Optional[bool] = Query(None, description="是否有效"),
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """获取Playbook总数量（优化：直接count，不查询数据）"""
    service = PlaybookService(db)
    
    try:
        # 🚀 优化：直接count，不查询完整数据
        count = await service.get_playbooks_count_fast(
            search=search,
            is_valid=is_valid
        )
        
        return {
            "total": count,
            "valid_count": count if is_valid is True else None,
            "search_term": search,
            "timestamp": "2025-10-14T06:41:23.381783+00:00"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Playbook数量失败: {str(e)}"
        )


@router.get("/", response_model=PlaybookListResponse, summary="获取Playbook列表")
async def list_playbooks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_valid: Optional[bool] = Query(None, description="是否有效"),
    order_by: str = Query("updated_at", description="排序字段"),
    desc: bool = Query(True, description="是否降序"),
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取Playbook列表
    
    支持分页、搜索、筛选和排序功能。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.list_playbooks(
            page=page,
            size=size,
            search=search,
            is_valid=is_valid,
            order_by=order_by,
            desc=desc
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Playbook列表失败: {str(e)}"
        )


@router.post("/", response_model=PlaybookInfo, status_code=status.HTTP_201_CREATED, summary="创建Playbook")
async def create_playbook(
    playbook_data: PlaybookCreate,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的Playbook
    
    可以同时提供文件内容，系统会自动进行语法验证。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.create_playbook(playbook_data, user_id=current_user.id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Playbook失败: {str(e)}"
        )


@router.get("/{playbook_id}", response_model=PlaybookInfo, summary="获取Playbook信息")
async def get_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    根据ID获取Playbook详细信息
    """
    service = PlaybookService(db)
    
    result = await service.get_playbook_by_id(playbook_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook不存在"
        )
    
    return result


@router.get("/{playbook_id}/content", response_model=PlaybookContent, summary="获取Playbook内容")
async def get_playbook_content(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取Playbook的文件内容
    """
    service = PlaybookService(db)
    
    try:
        result = await service.get_playbook_content(playbook_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Playbook内容失败: {str(e)}"
        )


@router.get("/{playbook_id}/raw", response_class=PlainTextResponse, summary="获取Playbook原始内容")
async def get_playbook_raw_content(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取Playbook的原始文件内容（纯文本格式）
    """
    service = PlaybookService(db)
    
    try:
        result = await service.get_playbook_content(playbook_id)
        return result.content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Playbook内容失败: {str(e)}"
        )


@router.put("/{playbook_id}", response_model=PlaybookInfo, summary="更新Playbook")
async def update_playbook(
    playbook_id: int,
    playbook_data: PlaybookUpdate,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    更新Playbook信息和内容
    
    如果提供了内容，系统会自动进行语法验证。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.update_playbook(playbook_id, playbook_data)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook不存在"
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Playbook失败: {str(e)}"
        )


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除Playbook")
async def delete_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    删除Playbook及其文件
    
    注意：此操作不可逆，文件将被移动到备份目录。
    """
    service = PlaybookService(db)
    
    try:
        success = await service.delete_playbook(playbook_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Playbook失败: {str(e)}"
        )


@router.post("/upload", response_model=PlaybookUploadResponse, summary="上传Playbook文件")
async def upload_playbook(
    file: UploadFile = File(..., description="Playbook文件"),
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    上传Playbook文件
    
    支持.yml和.yaml格式的文件，系统会自动进行语法验证。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.upload_playbook(file, user_id=current_user.id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传Playbook失败: {str(e)}"
        )


@router.post("/{playbook_id}/validate", response_model=PlaybookValidationResult, summary="验证Playbook")
async def validate_playbook(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    验证Playbook的语法和结构
    
    返回详细的验证结果，包括错误、警告和建议。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.validate_playbook_by_id(playbook_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证Playbook失败: {str(e)}"
        )


@router.post("/validate-content", response_model=PlaybookValidationResult, summary="验证Playbook内容")
async def validate_playbook_content(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    验证Playbook内容的语法和结构
    
    不需要保存文件，直接验证提供的内容。
    
    请求体格式:
    {
        "content": "playbook内容"
    }
    """
    from ansible_web_ui.services.playbook_validation_service import PlaybookValidationService
    
    content = request_data.get("content")
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必需参数: content"
        )
    
    try:
        validation_service = PlaybookValidationService()
        result = validation_service.validate_playbook_content(content)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"验证内容失败: {str(e)}"
        )


@router.get("/{playbook_id}/suggestions", response_model=List[str], summary="获取Playbook建议")
async def get_playbook_suggestions(
    playbook_id: int,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取Playbook的改进建议
    
    基于最佳实践提供优化建议。
    """
    service = PlaybookService(db)
    
    try:
        suggestions = await service.get_validation_suggestions(playbook_id)
        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取建议失败: {str(e)}"
        )


@router.post("/{playbook_id}/copy", response_model=PlaybookInfo, status_code=status.HTTP_201_CREATED, summary="复制Playbook")
async def copy_playbook(
    playbook_id: int,
    new_filename: str = Query(..., description="新文件名"),
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    复制Playbook到新文件
    
    创建现有Playbook的副本，使用新的文件名。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.copy_playbook(playbook_id, new_filename, user_id=current_user.id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制Playbook失败: {str(e)}"
        )


@router.get("/stats/summary", summary="获取Playbook统计信息")
async def get_playbook_stats(
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    获取Playbook的统计信息
    
    包括总数、有效数量、文件大小等统计数据。
    """
    service = PlaybookService(db)
    
    try:
        stats = await service.get_playbook_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计信息失败: {str(e)}"
        )


@router.post("/sync", summary="同步文件系统与数据库")
async def sync_playbooks(
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    同步文件系统中的Playbook文件与数据库记录
    
    扫描playbooks目录，添加新文件到数据库，删除不存在文件的记录。
    """
    service = PlaybookService(db)
    
    try:
        result = await service.sync_files_with_database()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"同步失败: {str(e)}"
        )


@router.put("/{playbook_id}/content", response_model=PlaybookValidationResult, summary="更新Playbook内容并验证")
async def update_playbook_content_with_validation(
    playbook_id: int,
    content: str,
    db: AsyncSession = Depends(get_async_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    更新Playbook内容并返回验证结果
    
    同时更新文件内容和数据库记录，返回验证结果。
    """
    service = PlaybookService(db)
    
    try:
        validation_result, playbook_info = await service.validate_and_update_playbook(
            playbook_id, content
        )
        return validation_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新内容失败: {str(e)}"
        )