"""
存储抽象层服务

统一管理所有项目的文件存储路径，提供路径安全验证。
"""

import os
import aiofiles
import aiofiles.os
from pathlib import Path
from typing import Dict, Any, List, Optional
from ansible_web_ui.core.config import settings


class StorageService:
    """
    存储抽象层服务
    
    职责：
    1. 统一管理所有项目的文件存储路径
    2. 提供路径安全验证
    3. 防止路径遍历攻击
    """
    
    def __init__(self):
        # 从配置读取基础存储路径
        # 使用新的配置项，如果不存在则使用PLAYBOOK_DIR作为默认值
        base_path_str = getattr(settings, 'PROJECTS_BASE_PATH', settings.PLAYBOOK_DIR)
        self.base_path = Path(base_path_str).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_project_path(self, project_name: str) -> Path:
        """
        获取项目的实际存储路径
        
        Args:
            project_name: 项目名称（数据库中的唯一标识）
        
        Returns:
            Path: 项目的绝对路径
        
        Raises:
            ValueError: 项目名称不合法时抛出
        """
        # 安全验证：防止路径遍历
        if '..' in project_name or '/' in project_name or '\\' in project_name:
            raise ValueError(f"非法的项目名称: {project_name}")
        
        project_path = (self.base_path / project_name).resolve()
        
        # 确保路径在基础目录内
        if not str(project_path).startswith(str(self.base_path)):
            raise ValueError("路径遍历攻击检测")
        
        return project_path
    
    def validate_path_within_project(
        self,
        project_name: str,
        relative_path: str
    ) -> Path:
        """
        验证相对路径是否在项目范围内
        
        Args:
            project_name: 项目名称
            relative_path: 相对于项目根目录的路径
        
        Returns:
            Path: 验证后的绝对路径
        
        Raises:
            ValueError: 路径不合法时抛出
        """
        project_path = self.get_project_path(project_name)
        
        # 处理空字符串或 None 的情况
        if not relative_path:
            return project_path
        
        target_path = (project_path / relative_path).resolve()
        
        # 确保目标路径在项目目录内
        if not str(target_path).startswith(str(project_path)):
            raise ValueError("路径必须在项目范围内")
        
        return target_path
    
    async def get_directory_tree(
        self,
        project_name: str,
        relative_path: str = "",
        max_depth: int = 10,
        current_depth: int = 0
    ) -> Dict[str, Any]:
        """
        获取项目内的目录树结构
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径（默认为项目根目录）
            max_depth: 最大递归深度
            current_depth: 当前递归深度
        
        Returns:
            目录树结构字典
        """
        # 确保 relative_path 是字符串
        if relative_path is None:
            relative_path = ""
        
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"路径不存在: {target_path}")
        
        if target_path.is_file():
            return {
                "name": target_path.name,
                "type": "file",
                "path": relative_path,
                "size": target_path.stat().st_size
            }
        
        # 目录
        children = []
        
        # 只有在未达到最大深度时才递归获取子项
        if current_depth < max_depth:
            try:
                for item in sorted(target_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                    # 计算相对路径
                    item_relative = str(Path(relative_path) / item.name) if relative_path else item.name
                    # 标准化路径分隔符（Windows兼容）
                    item_relative = item_relative.replace('\\', '/')
                    
                    try:
                        if item.is_dir():
                            child_tree = await self.get_directory_tree(
                                project_name,
                                item_relative,
                                max_depth,
                                current_depth + 1
                            )
                            # 确保返回的字典包含所有必需字段
                            if child_tree and isinstance(child_tree, dict) and all(k in child_tree for k in ['name', 'type', 'path']):
                                children.append(child_tree)
                        else:
                            children.append({
                                "name": item.name,
                                "type": "file",
                                "path": item_relative,
                                "size": item.stat().st_size
                            })
                    except (OSError, PermissionError) as e:
                        # 跳过无法访问的文件/目录
                        continue
            except PermissionError:
                pass  # 忽略权限错误
        
        return {
            "name": target_path.name if target_path.name else project_name,
            "type": "directory",
            "path": relative_path if relative_path else "",
            "children": children
        }
    
    async def create_directory(
        self,
        project_name: str,
        relative_path: str
    ) -> bool:
        """
        在项目内创建目录
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
        
        Returns:
            bool: 创建成功返回True
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        target_path.mkdir(parents=True, exist_ok=True)
        return True
    
    async def create_file(
        self,
        project_name: str,
        relative_path: str,
        content: str = ""
    ) -> bool:
        """
        在项目内创建文件
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
            content: 文件内容
        
        Returns:
            bool: 创建成功返回True
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        # 确保父目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        return True
    
    async def read_file(
        self,
        project_name: str,
        relative_path: str
    ) -> str:
        """
        读取项目内的文件内容
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
        
        Returns:
            str: 文件内容
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        
        if not target_path.is_file():
            raise ValueError(f"不是文件: {relative_path}")
        
        async with aiofiles.open(target_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    async def write_file(
        self,
        project_name: str,
        relative_path: str,
        content: str
    ) -> bool:
        """
        写入文件内容
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
            content: 文件内容
        
        Returns:
            bool: 写入成功返回True
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        # 确保父目录存在
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(target_path, 'w', encoding='utf-8') as f:
            await f.write(content)
        
        return True
    
    async def delete_file(
        self,
        project_name: str,
        relative_path: str
    ) -> bool:
        """
        删除项目内的文件
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
        
        Returns:
            bool: 删除成功返回True
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        if not target_path.exists():
            return False
        
        if target_path.is_file():
            await aiofiles.os.remove(target_path)
        elif target_path.is_dir():
            import shutil
            shutil.rmtree(target_path)
        
        return True
    
    async def move_file(
        self,
        project_name: str,
        source_relative: str,
        dest_relative: str
    ) -> bool:
        """
        在项目内移动文件
        
        Args:
            project_name: 项目名称
            source_relative: 源相对路径
            dest_relative: 目标相对路径
        
        Returns:
            bool: 移动成功返回True
        """
        source_path = self.validate_path_within_project(project_name, source_relative)
        dest_path = self.validate_path_within_project(project_name, dest_relative)
        
        if not source_path.exists():
            raise FileNotFoundError(f"源文件不存在: {source_relative}")
        
        # 确保目标目录存在
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        source_path.rename(dest_path)
        return True
    
    async def file_exists(
        self,
        project_name: str,
        relative_path: str
    ) -> bool:
        """
        检查文件是否存在
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
        
        Returns:
            bool: 文件存在返回True
        """
        try:
            target_path = self.validate_path_within_project(project_name, relative_path)
            return target_path.exists()
        except ValueError:
            return False
    
    async def get_file_info(
        self,
        project_name: str,
        relative_path: str
    ) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            project_name: 项目名称
            relative_path: 相对路径
        
        Returns:
            文件信息字典
        """
        target_path = self.validate_path_within_project(project_name, relative_path)
        
        if not target_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        
        stat = target_path.stat()
        
        return {
            "name": target_path.name,
            "path": relative_path,
            "type": "directory" if target_path.is_dir() else "file",
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime
        }
