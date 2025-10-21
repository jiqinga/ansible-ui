"""
Role管理服务

提供Ansible Role的CRUD操作和结构管理。
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ansible_web_ui.models.role import Role
from ansible_web_ui.models.project import Project
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.services.storage_service import StorageService


# Role标准目录结构
ROLE_STANDARD_DIRECTORIES = [
    "tasks",
    "handlers",
    "templates",
    "files",
    "vars",
    "defaults",
    "meta"
]

# Role模板定义
ROLE_TEMPLATES = {
    "basic": {
        "name": "basic",
        "description": "基础Role结构",
        "directories": ["tasks", "handlers", "defaults", "meta"],
        "files": {
            "tasks/main.yml": "---\n# 任务列表\n",
            "handlers/main.yml": "---\n# 处理器列表\n",
            "defaults/main.yml": "---\n# 默认变量\n",
            "meta/main.yml": "---\n# Role元数据\ndependencies: []\n"
        }
    },
    "full": {
        "name": "full",
        "description": "完整Role结构",
        "directories": ROLE_STANDARD_DIRECTORIES,
        "files": {
            "tasks/main.yml": "---\n# 任务列表\n",
            "handlers/main.yml": "---\n# 处理器列表\n",
            "templates/.gitkeep": "",
            "files/.gitkeep": "",
            "vars/main.yml": "---\n# 变量\n",
            "defaults/main.yml": "---\n# 默认变量\n",
            "meta/main.yml": "---\n# Role元数据\ndependencies: []\n"
        }
    },
    "minimal": {
        "name": "minimal",
        "description": "最小Role结构",
        "directories": ["tasks"],
        "files": {
            "tasks/main.yml": "---\n# 任务列表\n"
        }
    }
}


class RoleService(BaseService[Role]):
    """Role管理服务"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(Role, db_session)
        self.storage_service = StorageService()
    
    async def create_role(
        self,
        project_id: int,
        role_name: str,
        description: Optional[str] = None,
        template: str = 'basic'
    ) -> Role:
        """
        创建新Role
        
        Args:
            project_id: 项目ID
            role_name: Role名称
            description: Role描述
            template: 模板名称
        
        Returns:
            Role: 创建的Role实例
        """
        from sqlalchemy import select
        
        # 检查项目是否存在
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 检查Role名称是否已存在
        existing = await self.get_by_filters({
            'project_id': project_id,
            'name': role_name
        })
        if existing:
            raise ValueError(f"Role已存在: {role_name}")
        
        # Role相对路径
        relative_path = f"roles/{role_name}"
        
        # 创建数据库记录
        role = await self.create(
            project_id=project_id,
            name=role_name,
            description=description,
            relative_path=relative_path
        )
        
        # 创建Role目录结构
        try:
            await self._create_role_structure(project.name, relative_path, template)
        except Exception as e:
            # 如果创建失败，删除数据库记录
            await self.delete(role.id)
            raise ValueError(f"创建Role结构失败: {str(e)}")
        
        return role
    
    async def _create_role_structure(
        self,
        project_name: str,
        role_path: str,
        template_name: str
    ) -> None:
        """
        根据模板创建Role结构
        
        Args:
            project_name: 项目名称
            role_path: Role路径
            template_name: 模板名称
        """
        template = ROLE_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知的模板: {template_name}")
        
        # 创建目录
        for dir_name in template['directories']:
            dir_path = f"{role_path}/{dir_name}"
            await self.storage_service.create_directory(project_name, dir_path)
        
        # 创建文件
        for file_path, content in template['files'].items():
            full_path = f"{role_path}/{file_path}"
            await self.storage_service.create_file(project_name, full_path, content)
    
    async def get_role_structure(
        self,
        role_id: int
    ) -> Dict[str, Any]:
        """
        动态扫描并获取Role的实际目录结构
        
        Args:
            role_id: Role ID
        
        Returns:
            Role结构字典
        """
        role = await self.get_by_id(role_id)
        if not role:
            raise ValueError(f"Role不存在: {role_id}")
        
        # 获取项目信息
        from sqlalchemy import select
        result = await self.db.execute(
            select(Project).where(Project.id == role.project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"项目不存在: {role.project_id}")
        
        # 扫描Role目录
        role_path = self.storage_service.validate_path_within_project(
            project.name,
            role.relative_path
        )
        
        if not role_path.exists():
            return {
                "role_name": role.name,
                "directories": {},
                "exists": False
            }
        
        directories = {}
        
        # 扫描标准目录
        for dir_name in ROLE_STANDARD_DIRECTORIES:
            dir_path = role_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                files = []
                try:
                    for file in sorted(dir_path.iterdir()):
                        if file.is_file():
                            files.append(file.name)
                except PermissionError:
                    pass
                
                directories[dir_name] = {
                    "exists": True,
                    "files": files
                }
            else:
                directories[dir_name] = {
                    "exists": False,
                    "files": []
                }
        
        # 扫描自定义目录（不在标准列表中的）
        try:
            for item in role_path.iterdir():
                if item.is_dir() and item.name not in ROLE_STANDARD_DIRECTORIES:
                    files = []
                    try:
                        for file in sorted(item.iterdir()):
                            if file.is_file():
                                files.append(file.name)
                    except PermissionError:
                        pass
                    
                    directories[item.name] = {
                        "exists": True,
                        "files": files,
                        "custom": True
                    }
        except PermissionError:
            pass
        
        return {
            "role_name": role.name,
            "directories": directories,
            "exists": True
        }
    
    async def get_role_files(
        self,
        role_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取Role的所有文件列表
        
        Args:
            role_id: Role ID
        
        Returns:
            文件列表
        """
        role = await self.get_by_id(role_id)
        if not role:
            raise ValueError(f"Role不存在: {role_id}")
        
        # 获取项目信息
        from sqlalchemy import select
        result = await self.db.execute(
            select(Project).where(Project.id == role.project_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"项目不存在: {role.project_id}")
        
        # 获取文件树
        file_tree = await self.storage_service.get_directory_tree(
            project.name,
            role.relative_path,
            max_depth=5
        )
        
        # 扁平化文件列表
        files = []
        self._flatten_file_tree(file_tree, files)
        
        return files
    
    def _flatten_file_tree(
        self,
        node: Dict[str, Any],
        files: List[Dict[str, Any]],
        parent_path: str = ""
    ) -> None:
        """
        递归扁平化文件树
        
        Args:
            node: 文件树节点
            files: 文件列表（输出）
            parent_path: 父路径
        """
        if node.get('type') == 'file':
            files.append({
                'name': node['name'],
                'path': node['path'],
                'size': node.get('size', 0)
            })
        elif node.get('type') == 'directory':
            for child in node.get('children', []):
                self._flatten_file_tree(child, files, node['path'])
    
    async def get_roles_by_project(
        self,
        project_id: int
    ) -> List[Role]:
        """
        获取项目的所有Role
        
        Args:
            project_id: 项目ID
        
        Returns:
            Role列表
        """
        return await self.get_by_filters({'project_id': project_id})
    
    async def delete_role(
        self,
        role_id: int,
        delete_files: bool = True
    ) -> bool:
        """
        删除Role
        
        Args:
            role_id: Role ID
            delete_files: 是否删除文件系统中的文件
        
        Returns:
            bool: 是否删除成功
        """
        role = await self.get_by_id(role_id)
        if not role:
            return False
        
        # 删除文件系统中的Role目录
        if delete_files:
            try:
                from sqlalchemy import select
                result = await self.db.execute(
                    select(Project).where(Project.id == role.project_id)
                )
                project = result.scalar_one_or_none()
                if project:
                    await self.storage_service.delete_file(project.name, role.relative_path)
            except Exception as e:
                # 记录错误但继续删除数据库记录
                print(f"删除Role文件失败: {str(e)}")
        
        # 删除数据库记录
        return await self.delete(role_id)
