"""
项目管理服务

提供Ansible项目的CRUD操作和项目结构管理。
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from ansible_web_ui.models.project import Project
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.services.storage_service import StorageService


# 项目模板定义
PROJECT_TEMPLATES = {
    "standard": {
        "name": "standard",
        "description": "标准Ansible项目结构",
        "structure": {
            "ansible.cfg": "# Ansible配置文件\n[defaults]\nhost_key_checking = False\n",
            "inventory/": {
                "production": "# 生产环境清单\n",
                "staging": "# 测试环境清单\n",
                "hosts": "# 默认清单\n[all]\n"
            },
            "group_vars/": {
                "all.yml": "---\n# 所有主机的变量\n"
            },
            "host_vars/": {},
            "roles/": {},
            "playbooks/": {
                "site.yml": "---\n# 主Playbook\n- hosts: all\n  roles:\n    - common\n"
            },
            "files/": {},
            "templates/": {},
            "README.md": "# Ansible项目\n\n这是一个标准的Ansible项目结构。\n"
        }
    },
    "simple": {
        "name": "simple",
        "description": "简单单文件项目",
        "structure": {
            "playbook.yml": "---\n# 简单Playbook\n- hosts: all\n  tasks:\n    - name: 示例任务\n      debug:\n        msg: Hello World\n",
            "inventory.ini": "# 主机清单\n[all]\n",
            "ansible.cfg": "# Ansible配置文件\n[defaults]\nhost_key_checking = False\n"
        }
    },
    "role-based": {
        "name": "role-based",
        "description": "以Role为中心的项目",
        "structure": {
            "ansible.cfg": "# Ansible配置文件\n[defaults]\nhost_key_checking = False\nroles_path = ./roles\n",
            "inventory/": {
                "hosts": "# 主机清单\n[all]\n"
            },
            "roles/": {
                "common/": {
                    "tasks/": {
                        "main.yml": "---\n# Common角色任务\n"
                    },
                    "handlers/": {
                        "main.yml": "---\n# Common角色处理器\n"
                    },
                    "defaults/": {
                        "main.yml": "---\n# Common角色默认变量\n"
                    },
                    "meta/": {
                        "main.yml": "---\n# Common角色元数据\ndependencies: []\n"
                    }
                }
            },
            "site.yml": "---\n# 主Playbook\n- hosts: all\n  roles:\n    - common\n"
        }
    }
}


class ProjectService(BaseService[Project]):
    """项目管理服务"""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(Project, db_session)
        self.storage_service = StorageService()
    
    async def create_project(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        project_type: str = 'standard',
        template: Optional[str] = None,
        created_by: Optional[int] = None
    ) -> Project:
        """
        创建新项目
        
        Args:
            name: 项目名称（唯一标识符）
            display_name: 显示名称
            description: 项目描述
            project_type: 项目类型
            template: 模板名称
            created_by: 创建用户ID
        
        Returns:
            Project: 创建的项目实例
        """
        # 检查项目名称是否已存在
        existing = await self.get_by_field('name', name)
        if existing:
            raise ValueError(f"项目名称已存在: {name}")
        
        # 创建数据库记录
        project = await self.create(
            name=name,
            display_name=display_name or name,
            description=description,
            project_type=project_type,
            created_by=created_by
        )
        
        # 创建项目目录结构
        try:
            await self._create_project_structure(project, template or project_type)
        except Exception as e:
            # 如果创建失败，删除数据库记录
            await self.delete(project.id)
            raise ValueError(f"创建项目结构失败: {str(e)}")
        
        return project
    
    async def _create_project_structure(
        self,
        project: Project,
        template_name: str
    ) -> None:
        """
        根据模板创建项目结构
        
        Args:
            project: 项目实例
            template_name: 模板名称
        """
        template = PROJECT_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知的模板: {template_name}")
        
        structure = template['structure']
        await self._create_structure_recursive(project.name, "", structure)
    
    async def _create_structure_recursive(
        self,
        project_name: str,
        current_path: str,
        structure: Dict[str, Any]
    ) -> None:
        """
        递归创建目录结构
        
        Args:
            project_name: 项目名称
            current_path: 当前路径
            structure: 结构定义
        """
        for name, content in structure.items():
            item_path = f"{current_path}/{name}" if current_path else name
            
            if isinstance(content, dict):
                # 目录
                await self.storage_service.create_directory(project_name, item_path)
                await self._create_structure_recursive(project_name, item_path, content)
            elif isinstance(content, str):
                # 文件
                await self.storage_service.create_file(project_name, item_path, content)
    
    async def get_project_structure(
        self,
        project_id: int,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        获取项目的目录树结构
        
        Args:
            project_id: 项目ID
            max_depth: 最大递归深度
        
        Returns:
            目录树结构
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.get_directory_tree(
            project.name,
            "",
            max_depth
        )
    
    async def validate_project_structure(
        self,
        project_id: int
    ) -> Dict[str, Any]:
        """
        验证项目结构完整性
        
        Args:
            project_id: 项目ID
        
        Returns:
            验证结果字典
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 根据项目类型定义必需的目录和文件
        required_structure = {
            "standard": {
                "directories": ["inventory", "roles", "playbooks"],
                "files": ["ansible.cfg"]
            },
            "simple": {
                "directories": [],
                "files": ["playbook.yml", "inventory.ini"]
            },
            "role-based": {
                "directories": ["inventory", "roles"],
                "files": ["ansible.cfg", "site.yml"]
            }
        }
        
        required = required_structure.get(project.project_type, {})
        missing_directories = []
        missing_files = []
        warnings = []
        structure_status = {}
        
        # 检查必需的目录
        for dir_name in required.get("directories", []):
            exists = await self.storage_service.file_exists(project.name, dir_name)
            structure_status[dir_name] = {
                "exists": exists,
                "required": True,
                "type": "directory"
            }
            if not exists:
                missing_directories.append(dir_name)
        
        # 检查必需的文件
        for file_name in required.get("files", []):
            exists = await self.storage_service.file_exists(project.name, file_name)
            structure_status[file_name] = {
                "exists": exists,
                "required": True,
                "type": "file"
            }
            if not exists:
                missing_files.append(file_name)
        
        # 检查可选的目录
        optional_dirs = ["group_vars", "host_vars", "files", "templates"]
        for dir_name in optional_dirs:
            if dir_name not in structure_status:
                exists = await self.storage_service.file_exists(project.name, dir_name)
                structure_status[dir_name] = {
                    "exists": exists,
                    "required": False,
                    "type": "directory"
                }
                if not exists:
                    warnings.append(f"可选目录 {dir_name} 不存在")
        
        is_valid = len(missing_directories) == 0 and len(missing_files) == 0
        
        return {
            "is_valid": is_valid,
            "project_type": project.project_type,
            "missing_directories": missing_directories,
            "missing_files": missing_files,
            "warnings": warnings,
            "structure": structure_status
        }
    
    async def delete_project(
        self,
        project_id: int,
        delete_files: bool = True
    ) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            delete_files: 是否删除文件系统中的文件
        
        Returns:
            bool: 是否删除成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            return False
        
        # 删除文件系统中的项目目录
        if delete_files:
            try:
                project_path = self.storage_service.get_project_path(project.name)
                if project_path.exists():
                    import shutil
                    shutil.rmtree(project_path)
            except Exception as e:
                # 记录错误但继续删除数据库记录
                print(f"删除项目文件失败: {str(e)}")
        
        # 删除数据库记录（级联删除关联的playbooks和roles）
        return await self.delete(project_id)
    
    async def get_project_files(
        self,
        project_id: int,
        relative_path: str = "",
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        获取项目文件树
        
        Args:
            project_id: 项目ID
            relative_path: 相对路径
            max_depth: 最大递归深度
        
        Returns:
            文件树结构
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.get_directory_tree(
            project.name,
            relative_path,
            max_depth
        )
    
    async def create_directory_in_project(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """
        在项目中创建目录
        
        Args:
            project_id: 项目ID
            relative_path: 相对路径
        
        Returns:
            bool: 是否创建成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.create_directory(project.name, relative_path)
    
    async def move_file_in_project(
        self,
        project_id: int,
        source_path: str,
        dest_path: str
    ) -> bool:
        """
        在项目中移动文件
        
        Args:
            project_id: 项目ID
            source_path: 源路径
            dest_path: 目标路径
        
        Returns:
            bool: 是否移动成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.move_file(project.name, source_path, dest_path)
    
    async def delete_file_in_project(
        self,
        project_id: int,
        relative_path: str
    ) -> bool:
        """
        删除项目中的文件
        
        Args:
            project_id: 项目ID
            relative_path: 相对路径
        
        Returns:
            bool: 是否删除成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.delete_file(project.name, relative_path)

    async def read_file(
        self,
        project_id: int,
        relative_path: str
    ) -> str:
        """
        读取项目中的文件内容
        
        Args:
            project_id: 项目ID
            relative_path: 文件相对路径
        
        Returns:
            str: 文件内容
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.read_file(project.name, relative_path)
    
    async def write_file(
        self,
        project_id: int,
        relative_path: str,
        content: str
    ) -> bool:
        """
        写入文件内容到项目中
        
        Args:
            project_id: 项目ID
            relative_path: 文件相对路径
            content: 文件内容
        
        Returns:
            bool: 是否写入成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        return await self.storage_service.write_file(project.name, relative_path, content)
