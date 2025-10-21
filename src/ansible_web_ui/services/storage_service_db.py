"""
基于数据库的存储服务

将项目文件内容存储到数据库，同时使用本地文件系统作为缓存。
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ansible_web_ui.models.project_file import ProjectFile
from ansible_web_ui.services.file_cache_service import FileCacheService


class StorageServiceDB:
    """
    基于数据库的存储服务
    
    职责：
    1. 将文件内容存储到数据库
    2. 使用本地文件系统作为缓存
    3. 提供路径安全验证
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化存储服务
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
        self.cache_service = FileCacheService()
    
    @staticmethod
    def _normalize_path(path: str) -> str:
        """标准化路径（统一使用正斜杠）"""
        return path.replace('\\', '/')
    
    @staticmethod
    def _calculate_hash(content: str) -> str:
        """计算内容哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _get_cache_key(self, project_id: int, relative_path: str) -> str:
        """生成缓存键"""
        normalized_path = self._normalize_path(relative_path)
        return f"project_{project_id}_{normalized_path}"

    async def _get_file_record(
        self,
        project_id: int,
        relative_path: str
    ) -> Optional[ProjectFile]:
        """获取文件记录"""
        normalized_path = self._normalize_path(relative_path)
        result = await self.db.execute(
            select(ProjectFile).where(
                and_(
                    ProjectFile.project_id == project_id,
                    ProjectFile.relative_path == normalized_path
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def read_file(
        self,
        project_id: int,
        relative_path: str
    ) -> str:
        """
        读取文件内容
        
        优先从缓存读取，缓存未命中则从数据库读取。
        
        Args:
            project_id: 项目ID
            relative_path: 文件相对路径
        
        Returns:
            str: 文件内容
        """
        # 获取文件记录
        file_record = await self._get_file_record(project_id, relative_path)
        if not file_record:
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        
        if file_record.is_directory:
            raise ValueError(f"不是文件: {relative_path}")
        
        # 尝试从缓存读取
        cache_key = self._get_cache_key(project_id, relative_path)
        content = await self.cache_service.get_from_cache(cache_key, file_record.file_hash)
        
        # 缓存未命中，从数据库读取
        if content is None:
            content = file_record.file_content or ""
            
            # 更新缓存
            try:
                await self.cache_service.save_to_cache(cache_key, content)
            except Exception:
                pass
        
        return content

    async def write_file(
        self,
        project_id: int,
        relative_path: str,
        content: str
    ) -> bool:
        """
        写入文件内容
        
        Args:
            project_id: 项目ID
            relative_path: 文件相对路径
            content: 文件内容
        
        Returns:
            bool: 是否写入成功
        """
        normalized_path = self._normalize_path(relative_path)
        file_hash = self._calculate_hash(content)
        file_size = len(content.encode('utf-8'))
        
        # 检查文件是否存在
        file_record = await self._get_file_record(project_id, normalized_path)
        
        if file_record:
            # 更新现有文件
            file_record.file_content = content
            file_record.file_hash = file_hash
            file_record.file_size = file_size
        else:
            # 创建新文件
            file_record = ProjectFile(
                project_id=project_id,
                relative_path=normalized_path,
                file_content=content,
                file_hash=file_hash,
                file_size=file_size,
                is_directory=0
            )
            self.db.add(file_record)
        
        await self.db.commit()
        
        # 更新缓存
        try:
            cache_key = self._get_cache_key(project_id, normalized_path)
            await self.cache_service.save_to_cache(cache_key, content)
        except Exception:
            pass
        
        return True
    
    async def create_file(
        self,
        project_id: int,
        relative_path: str,
        content: str = ""
    ) -> bool:
        """创建文件"""
        return await self.write_file(project_id, relative_path, content)

    async def delete_file(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """
        删除文件
        
        Args:
            project_id: 项目ID
            relative_path: 文件相对路径
        
        Returns:
            bool: 是否删除成功
        """
        file_record = await self._get_file_record(project_id, relative_path)
        if not file_record:
            return False
        
        await self.db.delete(file_record)
        await self.db.commit()
        
        # 删除缓存
        try:
            cache_key = self._get_cache_key(project_id, relative_path)
            await self.cache_service.remove_from_cache(cache_key)
        except Exception:
            pass
        
        return True
    
    async def file_exists(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """检查文件是否存在"""
        file_record = await self._get_file_record(project_id, relative_path)
        return file_record is not None
    
    async def create_directory(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """
        创建目录
        
        Args:
            project_id: 项目ID
            relative_path: 目录相对路径
        
        Returns:
            bool: 是否创建成功
        """
        normalized_path = self._normalize_path(relative_path)
        
        # 检查是否已存在
        existing = await self._get_file_record(project_id, normalized_path)
        if existing:
            return True
        
        # 创建目录记录
        dir_record = ProjectFile(
            project_id=project_id,
            relative_path=normalized_path,
            file_content="",
            file_hash="",
            file_size=0,
            is_directory=1
        )
        self.db.add(dir_record)
        await self.db.commit()
        
        return True

    async def get_directory_tree(
        self,
        project_id: int,
        relative_path: str = "",
        max_depth: int = 10,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """
        获取目录树结构
        
        Args:
            project_id: 项目ID
            relative_path: 相对路径
            max_depth: 最大递归深度
            current_depth: 当前递归深度
        
        Returns:
            目录树结构字典
        """
        normalized_path = self._normalize_path(relative_path) if relative_path else ""
        
        # 获取当前路径的记录
        if normalized_path:
            current_record = await self._get_file_record(project_id, normalized_path)
            if not current_record:
                raise FileNotFoundError(f"路径不存在: {relative_path}")
            
            if not current_record.is_directory:
                # 是文件，直接返回文件信息
                return {
                    "name": Path(normalized_path).name,
                    "type": "file",
                    "path": normalized_path,
                    "size": current_record.file_size
                }
        
        # 是目录，获取子项
        children = []
        
        if current_depth < max_depth:
            # 查询所有子项
            if normalized_path:
                prefix = normalized_path + "/"
                # 查找直接子项（不包含更深层级）
                result = await self.db.execute(
                    select(ProjectFile).where(
                        and_(
                            ProjectFile.project_id == project_id,
                            ProjectFile.relative_path.like(f"{prefix}%")
                        )
                    )
                )
            else:
                # 根目录
                result = await self.db.execute(
                    select(ProjectFile).where(
                        ProjectFile.project_id == project_id
                    )
                )
            
            all_items = result.scalars().all()
            
            # 过滤出直接子项
            direct_children = {}
            for item in all_items:
                if normalized_path:
                    if not item.relative_path.startswith(prefix):
                        continue
                    remaining = item.relative_path[len(prefix):]
                else:
                    remaining = item.relative_path
                
                # 只取第一级
                parts = remaining.split('/')
                if len(parts) > 0 and parts[0]:
                    first_part = parts[0]
                    if first_part not in direct_children:
                        if len(parts) == 1:
                            # 直接子项
                            direct_children[first_part] = item
                        else:
                            # 有更深层级，创建目录占位符
                            direct_children[first_part] = None
            
            # 构建子项树
            for name, item in sorted(direct_children.items()):
                child_path = f"{normalized_path}/{name}" if normalized_path else name
                
                if item and not item.is_directory:
                    # 文件
                    children.append({
                        "name": name,
                        "type": "file",
                        "path": child_path,
                        "size": item.file_size
                    })
                else:
                    # 目录，递归获取
                    try:
                        child_tree = await self.get_directory_tree(
                            project_id,
                            child_path,
                            max_depth,
                            current_depth + 1
                        )
                        children.append(child_tree)
                    except Exception:
                        continue
        
        return {
            "name": Path(normalized_path).name if normalized_path else f"project_{project_id}",
            "type": "directory",
            "path": normalized_path,
            "children": children
        }
