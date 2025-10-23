"""
项目文件管理服务

提供项目文件的数据库 CRUD 操作和业务逻辑。
采用纯数据库存储方案，无缓存依赖。
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
import hashlib
import os
from pathlib import Path
import logging

from ansible_web_ui.models.project_file import ProjectFile
from ansible_web_ui.services.base import BaseService

# 获取日志记录器
logger = logging.getLogger(__name__)


class ProjectFileService(BaseService[ProjectFile]):
    """
    项目文件管理服务类
    
    职责：
    1. 管理项目文件的数据库 CRUD 操作
    2. 构建文件树结构（通过路径前缀匹配）
    3. 文件内容的读写和验证
    4. 路径安全验证
    5. 批量操作和事务管理
    
    特点：
    - 纯数据库操作，无缓存依赖
    - 路径驱动的文件树构建
    - 完整的安全验证机制
    - 支持事务的批量操作
    """
    
    # 配置常量
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化项目文件服务
        
        Args:
            db_session: 数据库会话
        """
        super().__init__(ProjectFile, db_session)

    # ==================== 辅助验证方法 ====================
    
    def _validate_path(self, relative_path: str) -> None:
        """
        验证路径安全性（防止路径遍历攻击）
        
        Args:
            relative_path: 文件相对路径
            
        Raises:
            ValueError: 路径不合法时抛出异常
        """
        if not relative_path:
            raise ValueError("路径不能为空")
        
        # 防止路径遍历攻击
        if '..' in relative_path:
            raise ValueError("路径不能包含 '..'，这可能导致路径遍历攻击")
        
        # 防止绝对路径
        if relative_path.startswith('/') or relative_path.startswith('\\'):
            raise ValueError("路径必须是相对路径，不能以 '/' 或 '\\' 开头")
        
        # Windows 驱动器路径检查
        if len(relative_path) >= 2 and relative_path[1] == ':':
            raise ValueError("路径不能包含驱动器盘符（如 'C:'）")
        
        # 防止特殊字符
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']
        for char in forbidden_chars:
            if char in relative_path:
                raise ValueError(f"路径包含非法字符: '{char}'")
        
        # 规范化路径并检查
        normalized = os.path.normpath(relative_path)
        if normalized.startswith('..'):
            raise ValueError("路径规范化后不能指向父目录")
    
    def _validate_file_size(self, content: str) -> None:
        """
        验证文件大小限制（最大 10MB）
        
        Args:
            content: 文件内容
            
        Raises:
            ValueError: 文件大小超过限制时抛出异常
        """
        if not isinstance(content, str):
            raise ValueError("文件内容必须是字符串类型")
        
        # 计算 UTF-8 编码后的字节大小
        size_bytes = len(content.encode('utf-8'))
        
        if size_bytes > self.MAX_FILE_SIZE:
            size_mb = size_bytes / (1024 * 1024)
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise ValueError(
                f"文件大小超过限制：当前 {size_mb:.2f}MB，最大允许 {max_mb:.0f}MB"
            )
    
    def _validate_encoding(self, content: str) -> None:
        """
        验证 UTF-8 编码
        
        Args:
            content: 文件内容
            
        Raises:
            ValueError: 编码验证失败时抛出异常
        """
        if not isinstance(content, str):
            raise ValueError("文件内容必须是字符串类型")
        
        try:
            # 尝试编码为 UTF-8
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            raise ValueError(
                f"文件内容包含无效的 UTF-8 字符（位置 {e.start}-{e.end}），"
                f"请使用 UTF-8 编码保存文件"
            )
    
    def _calculate_hash(self, content: str) -> str:
        """
        计算文件哈希值（SHA-256）
        
        Args:
            content: 文件内容
            
        Returns:
            str: SHA-256 哈希值（十六进制字符串）
        """
        if not isinstance(content, str):
            content = str(content)
        
        # 计算 SHA-256 哈希
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _extract_filename(self, relative_path: str) -> str:
        """
        从路径提取文件名（从路径中提取最后一部分）
        
        Args:
            relative_path: 文件相对路径
            
        Returns:
            str: 文件名
        """
        if not relative_path:
            return ""
        
        # 使用 Path 对象提取文件名
        path_obj = Path(relative_path)
        return path_obj.name

    # ==================== 文件 CRUD 操作 ====================
    
    async def create_file(
        self,
        project_id: int,
        relative_path: str,
        content: str
    ) -> ProjectFile:
        """
        创建文件
        
        Args:
            project_id: 项目 ID
            relative_path: 文件相对路径
            content: 文件内容
            
        Returns:
            ProjectFile: 创建的文件对象
            
        Raises:
            ValueError: 验证失败或数据库约束冲突时抛出异常
        """
        try:
            # 验证路径安全性
            self._validate_path(relative_path)
            
            # 验证文件大小
            self._validate_file_size(content)
            
            # 验证 UTF-8 编码
            self._validate_encoding(content)
            
            # 计算文件哈希值
            file_hash = self._calculate_hash(content)
            
            # 从 relative_path 提取 filename
            filename = self._extract_filename(relative_path)
            
            # 计算文件大小（字节）
            file_size = len(content.encode('utf-8'))
            
            # 递归创建父目录记录（如果不存在）
            await self._ensure_parent_directories(project_id, relative_path)
            
            # 创建 ProjectFile 记录
            file_data = {
                'project_id': project_id,
                'relative_path': relative_path,
                'filename': filename,
                'file_content': content,
                'file_size': file_size,
                'file_hash': file_hash,
                'is_directory': False
            }
            
            # 存储到数据库
            project_file = await self.create(**file_data)
            
            # 记录成功日志
            logger.info(
                "文件已创建",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "size": file_size,
                    "hash": file_hash[:8] if file_hash else None
                }
            )
            
            return project_file
            
        except (ValueError, FileNotFoundError):
            # 直接抛出验证异常，无需捕获
            raise
        except IntegrityError as e:
            # 数据库完整性约束错误（如唯一索引冲突）
            logger.error(
                "操作失败：创建文件时发生数据库完整性约束错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"文件已存在或违反数据库约束: {relative_path}")
        except OperationalError as e:
            # 数据库操作错误（如连接失败）
            logger.error(
                "操作失败：创建文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：创建文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"创建文件失败: {str(e)}")
    
    async def _ensure_parent_directories(
        self,
        project_id: int,
        relative_path: str
    ) -> None:
        """
        递归创建父目录记录（如果不存在）
        
        Args:
            project_id: 项目 ID
            relative_path: 文件相对路径
        """
        # 获取父目录路径（统一使用正斜杠）
        path_obj = Path(relative_path)
        parent_path = str(path_obj.parent).replace('\\', '/')
        
        # 如果父路径是 '.' 或空，说明已经到根目录
        if parent_path == '.' or not parent_path:
            return
        
        # 检查父目录是否已存在
        result = await self.db.execute(
            select(ProjectFile).where(
                and_(
                    ProjectFile.project_id == project_id,
                    ProjectFile.relative_path == parent_path
                )
            )
        )
        existing_dir = result.scalar_one_or_none()
        
        if not existing_dir:
            # 递归创建更上层的父目录
            await self._ensure_parent_directories(project_id, parent_path)
            
            # 创建当前父目录
            dir_filename = self._extract_filename(parent_path)
            dir_data = {
                'project_id': project_id,
                'relative_path': parent_path,
                'filename': dir_filename,
                'file_content': '',
                'file_size': 0,
                'file_hash': self._calculate_hash(''),
                'is_directory': True
            }
            await self.create(**dir_data)

    async def read_file(
        self,
        project_id: int,
        relative_path: str
    ) -> str:
        """
        读取文件内容
        
        Args:
            project_id: 项目 ID
            relative_path: 文件相对路径
            
        Returns:
            str: 文件内容
            
        Raises:
            ValueError: 路径不合法或数据库错误时抛出异常
            FileNotFoundError: 文件不存在时抛出异常
        """
        try:
            # 验证路径安全性
            self._validate_path(relative_path)
            
            # 使用 SQLAlchemy 查询从数据库读取文件记录
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == relative_path
                    )
                )
            )
            file_record = result.scalar_one_or_none()
            
            # 如果文件不存在，抛出 FileNotFoundError
            if not file_record:
                raise FileNotFoundError(f"文件不存在: {relative_path}")
            
            # 返回文件内容字符串
            return file_record.file_content or ""
            
        except (ValueError, FileNotFoundError):
            # 直接抛出验证异常和文件不存在异常
            raise
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：读取文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：读取文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"读取文件失败: {str(e)}")

    async def update_file(
        self,
        project_id: int,
        relative_path: str,
        content: str
    ) -> ProjectFile:
        """
        更新文件内容
        
        Args:
            project_id: 项目 ID
            relative_path: 文件相对路径
            content: 新的文件内容
            
        Returns:
            ProjectFile: 更新后的文件对象
            
        Raises:
            ValueError: 验证失败或数据库错误时抛出异常
            FileNotFoundError: 文件不存在时抛出异常
        """
        try:
            # 验证路径安全性
            self._validate_path(relative_path)
            
            # 验证文件大小
            self._validate_file_size(content)
            
            # 验证 UTF-8 编码
            self._validate_encoding(content)
            
            # 查询现有文件记录
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == relative_path
                    )
                )
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise FileNotFoundError(f"文件不存在: {relative_path}")
            
            # 计算新的哈希值和大小
            file_hash = self._calculate_hash(content)
            file_size = len(content.encode('utf-8'))
            
            # 更新 file_content、file_size、file_hash 字段
            # updated_at 会自动更新（模型中已配置 onupdate）
            updated_file = await self.update(
                file_record.id,
                file_content=content,
                file_size=file_size,
                file_hash=file_hash
            )
            
            # 记录成功日志
            logger.info(
                "文件已更新",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "size": file_size,
                    "hash": file_hash[:8] if file_hash else None
                }
            )
            
            return updated_file
            
        except (ValueError, FileNotFoundError):
            # 直接抛出验证异常和文件不存在异常
            raise
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：更新文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：更新文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"更新文件失败: {str(e)}")

    async def delete_file(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """
        删除文件
        
        Args:
            project_id: 项目 ID
            relative_path: 文件相对路径
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            ValueError: 路径不合法或数据库错误时抛出异常
            FileNotFoundError: 文件不存在时抛出异常
        """
        try:
            # 验证路径安全性
            self._validate_path(relative_path)
            
            # 查询文件记录
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == relative_path
                    )
                )
            )
            file_record = result.scalar_one_or_none()
            
            if not file_record:
                raise FileNotFoundError(f"文件不存在: {relative_path}")
            
            # 如果是目录（is_directory=True），调用 delete_directory_recursive
            if file_record.is_directory:
                deleted_count = await self.delete_directory_recursive(project_id, relative_path)
                
                # 记录成功日志
                logger.info(
                    "目录已删除",
                    extra={
                        "project_id": project_id,
                        "path": relative_path,
                        "deleted_count": deleted_count
                    }
                )
                
                return deleted_count > 0
            
            # 如果是文件，直接从数据库删除记录
            success = await self.delete(file_record.id)
            
            # 记录成功日志
            if success:
                logger.info(
                    "文件已删除",
                    extra={
                        "project_id": project_id,
                        "path": relative_path,
                        "size": file_record.file_size
                    }
                )
            
            return success
            
        except (ValueError, FileNotFoundError):
            # 直接抛出验证异常和文件不存在异常
            raise
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：删除文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：删除文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"删除文件失败: {str(e)}")
    
    # ==================== 目录操作 ====================
    
    async def create_directory(
        self,
        project_id: int,
        relative_path: str
    ) -> ProjectFile:
        """
        创建目录
        
        Args:
            project_id: 项目 ID
            relative_path: 目录相对路径
            
        Returns:
            ProjectFile: 创建的目录对象
            
        Raises:
            ValueError: 路径不合法或数据库错误时抛出异常
        """
        try:
            # 验证路径安全性
            self._validate_path(relative_path)
            
            # 递归创建父目录（如果不存在）
            await self._ensure_parent_directories(project_id, relative_path)
            
            # 检查目录是否已存在
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == relative_path
                    )
                )
            )
            existing_dir = result.scalar_one_or_none()
            
            if existing_dir:
                # 如果已存在，直接返回
                return existing_dir
            
            # 创建 is_directory=True 的 ProjectFile 记录
            filename = self._extract_filename(relative_path)
            dir_data = {
                'project_id': project_id,
                'relative_path': relative_path,
                'filename': filename,
                'file_content': '',  # file_content 设置为空字符串
                'file_size': 0,      # file_size 为 0
                'file_hash': self._calculate_hash(''),
                'is_directory': True
            }
            
            # 返回创建的 ProjectFile 对象
            directory = await self.create(**dir_data)
            
            # 记录成功日志
            logger.info(
                "目录已创建",
                extra={
                    "project_id": project_id,
                    "path": relative_path
                }
            )
            
            return directory
            
        except ValueError:
            # 直接抛出验证异常
            raise
        except IntegrityError as e:
            # 数据库完整性约束错误
            logger.error(
                "操作失败：创建目录时发生数据库完整性约束错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"目录已存在或违反数据库约束: {relative_path}")
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：创建目录时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：创建目录时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"创建目录失败: {str(e)}")
    
    async def list_directory(
        self,
        project_id: int,
        relative_path: str = ""
    ) -> List[ProjectFile]:
        """
        列出目录下的直接子项
        
        Args:
            project_id: 项目 ID
            relative_path: 目录相对路径（空字符串表示根目录）
            
        Returns:
            List[ProjectFile]: 直接子项列表
            
        Raises:
            ValueError: 路径不合法或数据库错误时抛出异常
        """
        try:
            # 验证路径安全性（空路径表示根目录，允许）
            if relative_path:
                self._validate_path(relative_path)
            
            # 使用 SQLAlchemy 查询，通过路径前缀匹配查询直接子项
            # 过滤条件：relative_path LIKE '{parent_path}/%' 且不包含更深层级的 /
            
            if relative_path:
                # 非根目录：查找以 "parent_path/" 开头的路径
                prefix = f"{relative_path}/"
            else:
                # 根目录：查找不包含 / 的路径
                prefix = ""
            
            # 查询所有匹配前缀的文件
            query = select(ProjectFile).where(
                ProjectFile.project_id == project_id
            )
            
            if prefix:
                # 路径以前缀开头
                query = query.where(ProjectFile.relative_path.like(f"{prefix}%"))
            
            result = await self.db.execute(query)
            all_matches = result.scalars().all()
            
            # 过滤出直接子项（不包含更深层级的 /）
            direct_children = []
            for file in all_matches:
                # 获取相对于父目录的路径部分
                if prefix:
                    relative_to_parent = file.relative_path[len(prefix):]
                else:
                    relative_to_parent = file.relative_path
                
                # 如果不包含 /，说明是直接子项
                if '/' not in relative_to_parent and relative_to_parent:
                    direct_children.append(file)
            
            # 按 is_directory DESC, filename ASC 排序（目录优先、名称排序）
            direct_children.sort(
                key=lambda x: (not x.is_directory, x.filename.lower())
            )
            
            return direct_children
            
        except ValueError:
            # 直接抛出验证异常
            raise
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：列出目录时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：列出目录时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"列出目录失败: {str(e)}")
    
    async def get_file_tree(
        self,
        project_id: int,
        relative_path: str = "",
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        构建文件树结构 - 基于路径前缀匹配
        
        Args:
            project_id: 项目 ID
            relative_path: 起始路径（空字符串表示根目录）
            max_depth: 最大递归深度（默认 10）
            
        Returns:
            Dict[str, Any]: 文件树结构
                {
                    "name": str,
                    "type": "file"|"directory",
                    "path": str,
                    "size": int,
                    "children": []  # 仅目录有此字段
                }
            
        Raises:
            ValueError: 路径不合法或数据库错误时抛出异常
        """
        try:
            # 验证路径安全性
            if relative_path:
                self._validate_path(relative_path)
            
            # 使用单次 SQLAlchemy 查询获取所有文件记录
            query = select(ProjectFile).where(
                ProjectFile.project_id == project_id
            ).order_by(ProjectFile.relative_path)
            
            result = await self.db.execute(query)
            all_files = result.scalars().all()
            
            # 构建路径映射
            path_map = {f.relative_path: f for f in all_files}
            
            # 递归构建树
            def build_tree(path: str, depth: int) -> Optional[Dict[str, Any]]:
                """
                递归构建文件树
                
                Args:
                    path: 当前路径
                    depth: 当前深度
                    
                Returns:
                    Optional[Dict[str, Any]]: 树节点，如果超过深度限制返回 None
                """
                # 支持最大递归深度限制
                if depth >= max_depth:
                    return None
                
                # 获取当前路径的文件对象
                file_obj = path_map.get(path)
                
                # 如果是根目录且不存在记录，创建虚拟根节点
                if not file_obj and path == "":
                    node = {
                        "name": "root",
                        "type": "directory",
                        "path": "",
                        "size": 0,
                        "children": []
                    }
                elif not file_obj:
                    return None
                else:
                    # 构建节点
                    node = {
                        "name": file_obj.filename or "root",
                        "type": "directory" if file_obj.is_directory else "file",
                        "path": file_obj.relative_path,
                        "size": file_obj.file_size
                    }
                
                # 如果是目录，查找子节点
                if node["type"] == "directory":
                    children = []
                    prefix = path + "/" if path else ""
                    
                    # 通过路径前缀匹配查找子节点
                    for child_path, child_file in path_map.items():
                        # 检查是否为直接子项
                        if child_path.startswith(prefix) and child_path != path:
                            # 确保是直接子项（不是孙子项）
                            relative_to_parent = child_path[len(prefix):]
                            if '/' not in relative_to_parent:
                                child_node = build_tree(child_path, depth + 1)
                                if child_node:
                                    children.append(child_node)
                    
                    # 子节点按目录优先、名称排序
                    children.sort(
                        key=lambda x: (x["type"] != "directory", x["name"].lower())
                    )
                    node["children"] = children
                
                return node
            
            # 从指定路径开始构建树
            tree = build_tree(relative_path, 0)
            
            # 如果树为空，返回空的根节点
            if not tree:
                return {
                    "name": "root",
                    "type": "directory",
                    "path": relative_path,
                    "size": 0,
                    "children": []
                }
            
            return tree
            
        except ValueError:
            # 直接抛出验证异常
            raise
        except OperationalError as e:
            # 数据库操作错误
            logger.error(
                "操作失败：构建文件树时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            logger.error(
                "操作失败：构建文件树时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"构建文件树失败: {str(e)}")
    
    async def delete_directory_recursive(
        self,
        project_id: int,
        relative_path: str
    ) -> int:
        """
        递归删除目录及所有子项
        
        Args:
            project_id: 项目 ID
            relative_path: 目录相对路径
            
        Returns:
            int: 删除的文件数量
            
        Raises:
            ValueError: 数据库错误时抛出异常
        """
        from sqlalchemy import delete as sql_delete
        
        try:
            # 使用 SQLAlchemy 查询，通过路径前缀匹配查找所有子项
            # 查找所有以该路径开头的文件（包括目录本身）
            prefix_pattern = f"{relative_path}/%"
            
            # 构建删除条件：路径等于目录路径 或 路径以 "目录路径/" 开头
            delete_stmt = sql_delete(ProjectFile).where(
                and_(
                    ProjectFile.project_id == project_id,
                    or_(
                        ProjectFile.relative_path == relative_path,
                        ProjectFile.relative_path.like(prefix_pattern)
                    )
                )
            )
            
            # 在事务中批量删除所有子项和目录本身
            result = await self.db.execute(delete_stmt)
            await self.db.commit()
            
            deleted_count = result.rowcount
            
            # 记录成功日志
            logger.info(
                "递归删除目录完成",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "deleted_count": deleted_count
                }
            )
            
            # 返回删除的文件数量
            return deleted_count
            
        except OperationalError as e:
            # 数据库操作错误
            await self.db.rollback()
            logger.error(
                "操作失败：递归删除目录时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            await self.db.rollback()
            logger.error(
                "操作失败：递归删除目录时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "path": relative_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"递归删除目录失败: {str(e)}")
    
    # ==================== 批量操作 ====================
    
    async def create_files_batch(
        self,
        project_id: int,
        files: List[Tuple[str, str]]
    ) -> List[ProjectFile]:
        """
        批量创建文件（单个事务）
        
        Args:
            project_id: 项目 ID
            files: 文件列表，每个元素是 (relative_path, content) 元组
            
        Returns:
            List[ProjectFile]: 创建的文件对象列表
            
        Raises:
            ValueError: 验证失败或数据库错误时抛出异常
        """
        created_files = []
        
        try:
            # 收集所有需要创建的目录路径（去重）
            all_directories = set()
            
            for relative_path, content in files:
                # 验证路径安全性
                self._validate_path(relative_path)
                
                # 如果不是目录标记，验证文件内容
                if content != "__DIRECTORY__":
                    # 验证文件大小
                    self._validate_file_size(content)
                    
                    # 验证 UTF-8 编码
                    self._validate_encoding(content)
                
                # 收集所有父目录路径
                path_obj = Path(relative_path)
                current_path = path_obj.parent
                
                while str(current_path) != '.' and str(current_path):
                    dir_path = str(current_path).replace('\\', '/')
                    all_directories.add(dir_path)
                    current_path = current_path.parent
            
            # 查询已存在的目录
            if all_directories:
                result = await self.db.execute(
                    select(ProjectFile.relative_path).where(
                        and_(
                            ProjectFile.project_id == project_id,
                            ProjectFile.relative_path.in_(all_directories),
                            ProjectFile.is_directory == True
                        )
                    )
                )
                existing_dirs = set(result.scalars().all())
                
                # 创建缺失的目录（按路径深度排序，确保父目录先创建）
                missing_dirs = sorted(
                    all_directories - existing_dirs,
                    key=lambda x: x.count('/')
                )
                
                for dir_path in missing_dirs:
                    dir_filename = self._extract_filename(dir_path)
                    dir_obj = ProjectFile(
                        project_id=project_id,
                        relative_path=dir_path,
                        filename=dir_filename,
                        file_content='',
                        file_size=0,
                        file_hash=self._calculate_hash(''),
                        is_directory=True
                    )
                    self.db.add(dir_obj)
                    created_files.append(dir_obj)
            
            # 批量创建文件对象
            file_objects = []
            for relative_path, content in files:
                filename = self._extract_filename(relative_path)
                
                # 检查是否是目录标记
                if content == "__DIRECTORY__":
                    # 这是一个空目录，创建目录记录
                    dir_obj = ProjectFile(
                        project_id=project_id,
                        relative_path=relative_path,
                        filename=filename,
                        file_content='',
                        file_size=0,
                        file_hash=self._calculate_hash(''),
                        is_directory=True
                    )
                    file_objects.append(dir_obj)
                else:
                    # 这是一个文件，创建文件记录
                    # 计算哈希值和大小
                    file_hash = self._calculate_hash(content)
                    file_size = len(content.encode('utf-8'))
                    
                    # 创建 ProjectFile 对象
                    file_obj = ProjectFile(
                        project_id=project_id,
                        relative_path=relative_path,
                        filename=filename,
                        file_content=content,
                        file_size=file_size,
                        file_hash=file_hash,
                        is_directory=False
                    )
                    file_objects.append(file_obj)
            
            # 使用 db.add_all() 批量插入
            self.db.add_all(file_objects)
            created_files.extend(file_objects)
            
            # 在事务中执行，任何失败自动回滚
            await self.db.commit()
            
            # 刷新对象以获取数据库生成的 ID
            for file_obj in created_files:
                await self.db.refresh(file_obj)
            
            # 计算总大小
            total_size = sum(f.file_size for f in created_files)
            
            # 记录成功日志
            logger.info(
                "批量创建文件完成",
                extra={
                    "project_id": project_id,
                    "file_count": len(created_files),
                    "total_size": total_size
                }
            )
            
            # 返回创建的 ProjectFile 对象列表
            return created_files
            
        except (ValueError, FileNotFoundError):
            # 直接抛出验证异常
            await self.db.rollback()
            raise
        except IntegrityError as e:
            # 数据库完整性约束错误
            await self.db.rollback()
            logger.error(
                "操作失败：批量创建文件时发生数据库完整性约束错误",
                extra={
                    "project_id": project_id,
                    "file_count": len(files),
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"批量创建文件失败：存在重复文件或违反数据库约束")
        except OperationalError as e:
            # 数据库操作错误
            await self.db.rollback()
            logger.error(
                "操作失败：批量创建文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "file_count": len(files),
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            await self.db.rollback()
            logger.error(
                "操作失败：批量创建文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "file_count": len(files),
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"批量创建文件失败: {str(e)}")
        except Exception as e:
            # 其他未预期的异常
            await self.db.rollback()
            logger.error(
                "操作失败：批量创建文件时发生未知错误",
                extra={
                    "project_id": project_id,
                    "file_count": len(files),
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"批量创建文件失败: {str(e)}")
    
    # ==================== 文件移动操作 ====================
    
    async def move_file(
        self,
        project_id: int,
        source_path: str,
        dest_path: str
    ) -> bool:
        """
        移动文件或目录
        
        Args:
            project_id: 项目 ID
            source_path: 源文件相对路径
            dest_path: 目标文件相对路径
            
        Returns:
            bool: 移动是否成功
            
        Raises:
            ValueError: 路径不合法或目标路径已存在时抛出异常
            FileNotFoundError: 源文件不存在时抛出异常
        """
        # 验证源路径和目标路径的合法性
        self._validate_path(source_path)
        self._validate_path(dest_path)
        
        # 检查源路径和目标路径是否相同
        if source_path == dest_path:
            raise ValueError("源路径和目标路径不能相同")
        
        try:
            # 查询源文件记录
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == source_path
                    )
                )
            )
            source_file = result.scalar_one_or_none()
            
            # 如果源文件不存在，抛出 FileNotFoundError
            if not source_file:
                raise FileNotFoundError(f"源文件不存在: {source_path}")
            
            # 检查目标路径是否已存在
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        ProjectFile.relative_path == dest_path
                    )
                )
            )
            dest_file = result.scalar_one_or_none()
            
            # 如果目标路径已存在，抛出 ValueError
            if dest_file:
                raise ValueError(f"目标路径已存在: {dest_path}")
            
            # 确保目标路径的父目录存在
            await self._ensure_parent_directories(project_id, dest_path)
            
            # 如果是文件，直接更新 relative_path 和 filename
            if not source_file.is_directory:
                # 提取新的文件名
                new_filename = self._extract_filename(dest_path)
                
                # 更新文件记录
                source_file.relative_path = dest_path
                source_file.filename = new_filename
                
                # 提交更改
                await self.db.commit()
                
                return True
            
            # 如果是目录，查询所有子项（路径前缀匹配）
            prefix_pattern = f"{source_path}/%"
            
            result = await self.db.execute(
                select(ProjectFile).where(
                    and_(
                        ProjectFile.project_id == project_id,
                        or_(
                            ProjectFile.relative_path == source_path,
                            ProjectFile.relative_path.like(prefix_pattern)
                        )
                    )
                )
            )
            all_items = result.scalars().all()
            
            # 批量更新它们的 relative_path
            for item in all_items:
                # 计算新的相对路径
                if item.relative_path == source_path:
                    # 目录本身
                    new_path = dest_path
                else:
                    # 子项：替换路径前缀
                    # 例如：source_path = "old/dir", dest_path = "new/dir"
                    # item.relative_path = "old/dir/file.txt" -> "new/dir/file.txt"
                    relative_part = item.relative_path[len(source_path):]
                    new_path = dest_path + relative_part
                
                # 更新路径和文件名
                item.relative_path = new_path
                item.filename = self._extract_filename(new_path)
            
            # 使用事务确保原子性（在事务中执行）
            await self.db.commit()
            
            # 记录成功日志
            logger.info(
                "文件已移动",
                extra={
                    "project_id": project_id,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "is_directory": source_file.is_directory,
                    "items_moved": len(all_items) if source_file.is_directory else 1
                }
            )
            
            return True
            
        except (ValueError, FileNotFoundError):
            # 重新抛出已知异常
            await self.db.rollback()
            raise
        except IntegrityError as e:
            # 数据库完整性约束错误
            await self.db.rollback()
            logger.error(
                "操作失败：移动文件时发生数据库完整性约束错误",
                extra={
                    "project_id": project_id,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"移动文件失败：目标路径已存在或违反数据库约束")
        except OperationalError as e:
            # 数据库操作错误
            await self.db.rollback()
            logger.error(
                "操作失败：移动文件时发生数据库操作错误",
                extra={
                    "project_id": project_id,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"数据库操作失败，请稍后重试: {str(e)}")
        except SQLAlchemyError as e:
            # 其他 SQLAlchemy 异常
            await self.db.rollback()
            logger.error(
                "操作失败：移动文件时发生数据库错误",
                extra={
                    "project_id": project_id,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"移动文件失败: {str(e)}")
        except Exception as e:
            # 其他未预期的异常
            await self.db.rollback()
            logger.error(
                "操作失败：移动文件时发生未知错误",
                extra={
                    "project_id": project_id,
                    "source_path": source_path,
                    "dest_path": dest_path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise ValueError(f"移动文件失败: {str(e)}")
