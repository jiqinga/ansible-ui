"""
Playbook管理服务

提供Playbook的数据库操作和业务逻辑。
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from fastapi import HTTPException, UploadFile
from ansible_web_ui.models.playbook import Playbook
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.services.file_service import FileService

from ansible_web_ui.services.playbook_validation_service import PlaybookValidationService
from ansible_web_ui.schemas.playbook_schemas import (
    PlaybookCreate, PlaybookUpdate, PlaybookInfo, PlaybookContent,
    PlaybookListResponse, PlaybookUploadResponse, PlaybookValidationResult,
    ValidationIssue
)


class PlaybookService(BaseService[Playbook]):
    """
    Playbook管理服务类
    
    提供Playbook的完整管理功能，包括数据库操作和文件操作。
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化Playbook服务
        
        Args:
            db_session: 数据库会话
        """
        super().__init__(Playbook, db_session)
        self.file_service = FileService()
        self.validation_service = PlaybookValidationService()
    
    async def create_playbook(
        self, 
        playbook_data: PlaybookCreate, 
        user_id: Optional[int] = None
    ) -> PlaybookInfo:
        """
        创建新的Playbook
        
        Args:
            playbook_data: Playbook创建数据
            user_id: 创建用户ID
            
        Returns:
            PlaybookInfo: 创建的Playbook信息
            
        Raises:
            HTTPException: 创建失败时抛出异常
        """
        # 检查文件名是否已存在
        existing = await self.get_by_filename(playbook_data.filename)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"文件名已存在: {playbook_data.filename}"
            )
        
        try:
            # 准备内容（如果没有提供内容，创建空文件）
            content = playbook_data.content if playbook_data.content is not None else ""
            
            # 直接计算哈希值和大小
            import hashlib
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            file_size = len(content.encode('utf-8'))
            
            # 创建数据库记录
            playbook_dict = playbook_data.model_dump(exclude={'content', 'path'})
            playbook_dict.update({
                'file_content': content,
                'file_path': None,
                'file_size': file_size,
                'file_hash': file_hash
            })
            
            if user_id:
                playbook_dict['created_by'] = user_id
            
            playbook = await self.create(**playbook_dict)
            
            return PlaybookInfo.model_validate(playbook)
            
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            raise HTTPException(
                status_code=500,
                detail=f"创建Playbook失败: {str(e)}"
            )
    
    async def get_playbook_by_id(self, playbook_id: int) -> Optional[PlaybookInfo]:
        """
        根据ID获取Playbook信息
        
        Args:
            playbook_id: Playbook ID
            
        Returns:
            Optional[PlaybookInfo]: Playbook信息或None
        """
        playbook = await self.get_by_id(playbook_id)
        if playbook:
            return PlaybookInfo.model_validate(playbook)
        return None
    
    async def get_by_filename(self, filename: str) -> Optional[Playbook]:
        """
        根据文件名获取Playbook
        
        Args:
            filename: 文件名
            
        Returns:
            Optional[Playbook]: Playbook实例或None
        """
        result = await self.db.execute(
            select(Playbook).where(Playbook.filename == filename)
        )
        return result.scalar_one_or_none()
    
    async def get_playbook_content(self, playbook_id: int) -> PlaybookContent:
        """
        获取Playbook文件内容（直接从数据库读取）
        
        Args:
            playbook_id: Playbook ID
            
        Returns:
            PlaybookContent: Playbook内容信息
            
        Raises:
            HTTPException: Playbook不存在时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        # 直接从数据库读取内容
        return PlaybookContent(
            filename=playbook.filename,
            content=playbook.file_content or "",
            file_size=playbook.file_size,
            last_modified=playbook.updated_at.isoformat() if playbook.updated_at else None
        )
    
    async def update_playbook(
        self, 
        playbook_id: int, 
        playbook_data: PlaybookUpdate
    ) -> Optional[PlaybookInfo]:
        """
        更新Playbook信息
        
        Args:
            playbook_id: Playbook ID
            playbook_data: 更新数据
            
        Returns:
            Optional[PlaybookInfo]: 更新后的Playbook信息
            
        Raises:
            HTTPException: 更新失败时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        # 准备更新数据
        update_dict = playbook_data.model_dump(exclude_unset=True, exclude={'content'})
        
        # 如果提供了内容，更新数据库
        if playbook_data.content is not None:
            content = playbook_data.content
            
            # 直接计算哈希值和大小
            import hashlib
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            file_size = len(content.encode('utf-8'))
            
            update_dict.update({
                'file_content': content,
                'file_size': file_size,
                'file_hash': file_hash
            })
        
        # 更新数据库记录
        updated_playbook = await self.update(playbook_id, **update_dict)
        
        if updated_playbook:
            return PlaybookInfo.model_validate(updated_playbook)
        return None
    
    async def delete_playbook(self, playbook_id: int) -> bool:
        """
        删除Playbook
        
        Args:
            playbook_id: Playbook ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            HTTPException: 删除失败时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        try:
            # 直接删除数据库记录
            success = await self.delete(playbook_id)
            
            return success
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"删除Playbook失败: {str(e)}"
            )
    
    async def get_playbooks_count_fast(
        self,
        search: Optional[str] = None,
        is_valid: Optional[bool] = None
    ) -> int:
        """
        快速获取Playbook数量（优化：只count，不查询数据）
        
        Args:
            search: 搜索关键词
            is_valid: 是否有效
            
        Returns:
            int: Playbook数量
        """
        from ansible_web_ui.core.cache import get_cache
        
        # 生成缓存key
        cache_key = f"playbooks_count:{search}:{is_valid}"
        
        # 尝试从缓存获取
        cache = get_cache()
        cached_count = cache.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        # 构建count查询
        count_query = select(func.count(Playbook.id))
        
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                or_(
                    Playbook.filename.ilike(search_pattern),
                    Playbook.display_name.ilike(search_pattern),
                    Playbook.description.ilike(search_pattern)
                )
            )
        
        if is_valid is not None:
            count_query = count_query.where(Playbook.is_valid == is_valid)
        
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        # 缓存结果
        cache.set(cache_key, count, ttl=60)
        
        return count
    
    async def list_playbooks(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        is_valid: Optional[bool] = None,
        order_by: str = "updated_at",
        desc: bool = True
    ) -> PlaybookListResponse:
        """
        获取Playbook列表
        
        Args:
            page: 页码
            size: 每页大小
            search: 搜索关键词
            is_valid: 是否有效
            order_by: 排序字段
            desc: 是否降序
            
        Returns:
            PlaybookListResponse: Playbook列表响应
        """
        # 构建查询条件
        filters = {}
        if is_valid is not None:
            filters['is_valid'] = is_valid
        
        # 构建搜索条件
        query = select(Playbook)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Playbook.filename.ilike(search_pattern),
                    Playbook.display_name.ilike(search_pattern),
                    Playbook.description.ilike(search_pattern)
                )
            )
        
        # 应用过滤条件
        for field, value in filters.items():
            if hasattr(Playbook, field):
                query = query.where(getattr(Playbook, field) == value)
        
        # 计算总数
        count_query = select(func.count(Playbook.id))
        if search:
            count_query = count_query.where(
                or_(
                    Playbook.filename.ilike(search_pattern),
                    Playbook.display_name.ilike(search_pattern),
                    Playbook.description.ilike(search_pattern)
                )
            )
        for field, value in filters.items():
            if hasattr(Playbook, field):
                count_query = count_query.where(getattr(Playbook, field) == value)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 应用排序和分页
        if hasattr(Playbook, order_by):
            order_field = getattr(Playbook, order_by)
            if desc:
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field)
        
        skip = (page - 1) * size
        query = query.offset(skip).limit(size)
        
        # 执行查询
        result = await self.db.execute(query)
        playbooks = result.scalars().all()
        
        # 转换为响应格式
        items = [PlaybookInfo.model_validate(playbook) for playbook in playbooks]
        
        pages = (total + size - 1) // size  # 向上取整
        
        return PlaybookListResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def upload_playbook(
        self, 
        file: UploadFile, 
        user_id: Optional[int] = None
    ) -> PlaybookUploadResponse:
        """
        上传Playbook文件
        
        Args:
            file: 上传的文件
            user_id: 上传用户ID
            
        Returns:
            PlaybookUploadResponse: 上传结果
            
        Raises:
            HTTPException: 上传失败时抛出异常
        """
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="文件名不能为空"
            )
        
        # 读取上传的文件内容
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # 直接计算哈希值和大小
        import hashlib
        file_hash = hashlib.sha256(content_str.encode('utf-8')).hexdigest()
        file_size = len(content)
        
        # 检查是否已存在同名记录
        existing = await self.get_by_filename(file.filename)
        
        # 验证内容
        validation_result = None
        try:
            validation_result = self.validation_service.validate_playbook_content(content_str)
        except Exception:
            validation_result = PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message="验证过程中发生错误",
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[]
            )
        
        error_messages = [error.message for error in validation_result.errors] if validation_result.errors else []
        
        if existing:
            # 更新现有记录
            update_data = {
                'file_content': content_str,
                'file_size': file_size,
                'file_hash': file_hash,
                'is_valid': validation_result.is_valid,
                'validation_error': '; '.join(error_messages) if error_messages else None
            }
            await self.update(existing.id, **update_data)
        else:
            # 创建新记录
            playbook_data = {
                'filename': file.filename,
                'file_content': content_str,
                'file_path': None,
                'file_size': file_size,
                'file_hash': file_hash,
                'is_valid': validation_result.is_valid,
                'validation_error': '; '.join(error_messages) if error_messages else None,
                'created_by': user_id
            }
            await self.create(**playbook_data)
        
        return PlaybookUploadResponse(
            filename=file.filename,
            file_size=file_size,
            upload_path=None,
            is_valid=validation_result.is_valid if validation_result else False,
            validation_result=validation_result
        )
    
    async def copy_playbook(
        self, 
        playbook_id: int, 
        new_filename: str,
        user_id: Optional[int] = None
    ) -> PlaybookInfo:
        """
        复制Playbook
        
        Args:
            playbook_id: 源Playbook ID
            new_filename: 新文件名
            user_id: 操作用户ID
            
        Returns:
            PlaybookInfo: 复制的Playbook信息
            
        Raises:
            HTTPException: 复制失败时抛出异常
        """
        # 获取源Playbook
        source_playbook = await self.get_by_id(playbook_id)
        if not source_playbook:
            raise HTTPException(
                status_code=404,
                detail="源Playbook不存在"
            )
        
        # 检查新文件名是否已存在
        existing = await self.get_by_filename(new_filename)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"文件名已存在: {new_filename}"
            )
        
        # 复制内容（从数据库）
        content = source_playbook.file_content or ""
        
        # 直接计算哈希值和大小
        import hashlib
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        file_size = len(content.encode('utf-8'))
        
        # 创建新的数据库记录
        new_playbook_data = {
            'filename': new_filename,
            'display_name': f"{source_playbook.display_name or source_playbook.filename} (副本)",
            'description': source_playbook.description,
            'file_content': content,
            'file_path': None,
            'file_size': file_size,
            'file_hash': file_hash,
            'is_valid': source_playbook.is_valid,
            'validation_error': source_playbook.validation_error,
            'created_by': user_id
        }
        
        new_playbook = await self.create(**new_playbook_data)
        
        return PlaybookInfo.model_validate(new_playbook)
    
    async def get_playbook_stats(self) -> Dict[str, Any]:
        """
        获取Playbook统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 总数统计
            total_result = await self.db.execute(select(func.count(Playbook.id)))
            total = total_result.scalar()
            
            # 有效文件统计
            valid_result = await self.db.execute(
                select(func.count(Playbook.id)).where(Playbook.is_valid == True)
            )
            valid = valid_result.scalar()
            
            # 无效文件统计
            invalid = total - valid
            
            # 文件大小统计
            size_result = await self.db.execute(select(func.sum(Playbook.file_size)))
            total_size = size_result.scalar() or 0
            
            return {
                'total_playbooks': total,
                'valid_playbooks': valid,
                'invalid_playbooks': invalid,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取统计信息失败: {str(e)}"
            )
    
    async def sync_files_with_database(self) -> Dict[str, Any]:
        """
        同步文件系统与数据库
        
        Returns:
            Dict[str, Any]: 同步结果
        """
        try:
            # 获取文件系统中的文件
            file_list = await self.file_service.list_files()
            file_names = {file_info['filename'] for file_info in file_list}
            
            # 获取数据库中的记录
            db_playbooks = await self.get_all()
            db_names = {playbook.filename for playbook in db_playbooks}
            
            # 找出需要添加到数据库的文件
            files_to_add = file_names - db_names
            
            # 找出需要从数据库删除的记录
            records_to_remove = db_names - file_names
            
            added_count = 0
            removed_count = 0
            
            # 添加新文件到数据库
            for filename in files_to_add:
                file_info = next(
                    (f for f in file_list if f['filename'] == filename), 
                    None
                )
                if file_info:
                    await self.create(
                        filename=filename,
                        file_path=file_info['file_path'],
                        file_size=file_info['file_size']
                    )
                    added_count += 1
            
            # 从数据库删除不存在的文件记录
            for filename in records_to_remove:
                playbook = await self.get_by_filename(filename)
                if playbook:
                    await self.delete(playbook.id)
                    removed_count += 1
            
            return {
                'files_added': added_count,
                'records_removed': removed_count,
                'total_files': len(file_names),
                'total_records': len(db_names) + added_count - removed_count
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"同步失败: {str(e)}"
            )
    
    async def validate_playbook_content(self, content: str) -> PlaybookValidationResult:
        """
        验证Playbook内容
        
        Args:
            content: Playbook内容
            
        Returns:
            PlaybookValidationResult: 验证结果
        """
        try:
            return self.validation_service.validate_playbook_content(content)
        except Exception as e:
            error_msg = f"验证过程中发生错误: {str(e)}"
            return PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message=error_msg,
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[{
                    'type': 'validation_error',
                    'message': error_msg,
                    'line': None,
                    'column': None
                }]
            )
    
    async def validate_playbook_by_id(self, playbook_id: int) -> PlaybookValidationResult:
        """
        根据ID验证Playbook
        
        Args:
            playbook_id: Playbook ID
            
        Returns:
            PlaybookValidationResult: 验证结果
            
        Raises:
            HTTPException: Playbook不存在时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        try:
            # 从数据库读取内容
            content = playbook.file_content or ""
            
            # 验证内容
            validation_result = self.validation_service.validate_playbook_content(content)
            
            # 更新数据库中的验证状态
            error_messages = [error.message for error in validation_result.errors] if validation_result.errors else []
            update_data = {
                'is_valid': validation_result.is_valid,
                'validation_error': '; '.join(error_messages) if error_messages else None
            }
            await self.update(playbook_id, **update_data)
            
            return validation_result
            
        except HTTPException:
            raise
        except Exception as e:
            # 更新数据库中的验证状态为失败
            error_msg = f"验证失败: {str(e)}"
            await self.update(playbook_id, is_valid=False, validation_error=error_msg)
            
            return PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message=f"验证Playbook失败: {str(e)}",
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[{
                    'type': 'validation_error',
                    'message': f"验证Playbook失败: {str(e)}",
                    'line': None,
                    'column': None
                }]
            )
    
    async def validate_and_update_playbook(
        self, 
        playbook_id: int, 
        content: str
    ) -> Tuple[PlaybookValidationResult, Optional[PlaybookInfo]]:
        """
        验证并更新Playbook内容
        
        Args:
            playbook_id: Playbook ID
            content: 新的内容
            
        Returns:
            Tuple[PlaybookValidationResult, Optional[PlaybookInfo]]: 验证结果和更新后的Playbook信息
            
        Raises:
            HTTPException: Playbook不存在时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        try:
            # 先验证内容
            validation_result = self.validation_service.validate_playbook_content(content)
            
            # 直接计算哈希值和大小
            import hashlib
            file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            file_size = len(content.encode('utf-8'))
            
            # 更新数据库记录
            error_messages = [error.message for error in validation_result.errors] if validation_result.errors else []
            update_data = {
                'file_content': content,
                'file_size': file_size,
                'file_hash': file_hash,
                'is_valid': validation_result.is_valid,
                'validation_error': '; '.join(error_messages) if error_messages else None
            }
            
            updated_playbook = await self.update(playbook_id, **update_data)
            
            playbook_info = None
            if updated_playbook:
                playbook_info = PlaybookInfo.model_validate(updated_playbook)
            
            return validation_result, playbook_info
            
        except HTTPException:
            raise
        except Exception as e:
            # 更新验证状态为失败
            error_msg = f"更新失败: {str(e)}"
            await self.update(playbook_id, is_valid=False, validation_error=error_msg)
            
            validation_result = PlaybookValidationResult(
                is_valid=False,
                errors=[ValidationIssue(
                    line=0,
                    column=0,
                    message=f"更新Playbook失败: {str(e)}",
                    severity='error'
                )],
                warnings=[],
                syntax_errors=[{
                    'type': 'update_error',
                    'message': f"更新Playbook失败: {str(e)}",
                    'line': None,
                    'column': None
                }]
            )
            
            return validation_result, None
    
    async def get_validation_suggestions(self, playbook_id: int) -> List[str]:
        """
        获取Playbook的验证建议
        
        Args:
            playbook_id: Playbook ID
            
        Returns:
            List[str]: 建议列表
            
        Raises:
            HTTPException: Playbook不存在时抛出异常
        """
        playbook = await self.get_by_id(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=404,
                detail="Playbook不存在"
            )
        
        try:
            # 从数据库读取内容
            content = playbook.file_content or ""
            
            # 获取建议
            suggestions = self.validation_service.get_validation_suggestions(content)
            
            return suggestions
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取建议失败: {str(e)}"
            )
    
    async def get_playbooks_count_fast(
        self,
        search: Optional[str] = None,
        is_valid: Optional[bool] = None
    ) -> int:
        """
        快速获取Playbook数量（优化：直接count，不查询数据）
        
        优化点:
        1. 使用 func.count() 直接在数据库中计数
        2. 不查询完整数据，只返回数量
        3. 支持筛选条件
        
        Args:
            search: 搜索关键词
            is_valid: 是否有效
            
        Returns:
            int: Playbook数量
        """
        from sqlalchemy import select, func, or_
        
        # 构建查询
        query = select(func.count(Playbook.id))
        
        # 应用筛选条件
        conditions = []
        
        if search:
            conditions.append(
                or_(
                    Playbook.filename.ilike(f"%{search}%"),
                    Playbook.display_name.ilike(f"%{search}%"),
                    Playbook.description.ilike(f"%{search}%")
                )
            )
        
        if is_valid is not None:
            conditions.append(Playbook.is_valid == is_valid)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 执行查询
        result = await self.db.execute(query)
        count = result.scalar()
        
        return count or 0
