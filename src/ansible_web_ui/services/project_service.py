"""
项目管理服务

提供Ansible项目的CRUD操作和项目结构管理。
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ansible_web_ui.models.project import Project
from ansible_web_ui.models.project_file import ProjectFile
from ansible_web_ui.services.base import BaseService
from ansible_web_ui.services.storage_service import StorageService

# 配置日志
logger = logging.getLogger(__name__)


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
    
    def __init__(self, db_session: AsyncSession, project_file_service=None):
        super().__init__(Project, db_session)
        self.storage_service = StorageService()
        self._project_file_service = project_file_service
    
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
        根据模板创建项目结构（使用数据库存储）
        
        Args:
            project: 项目实例
            template_name: 模板名称
        """
        template = PROJECT_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知的模板: {template_name}")
        
        logger.info(f"开始创建项目结构: project_id={project.id}, template={template_name}")
        
        try:
            # 如果注入了 ProjectFileService，使用数据库存储
            if self._project_file_service:
                structure = template['structure']
                # 收集所有文件列表
                files = self._collect_files_from_structure("", structure)
                
                logger.info(f"收集到 {len(files)} 个文件，准备批量创建到数据库")
                
                # 调用 ProjectFileService.create_files_batch 批量创建文件到数据库
                created_files = await self._project_file_service.create_files_batch(
                    project.id,
                    files
                )
                
                logger.info(f"成功创建 {len(created_files)} 个文件到数据库")
            else:
                # 降级到文件系统存储（向后兼容）
                logger.warning("未注入 ProjectFileService，使用文件系统存储")
                structure = template['structure']
                await self._create_structure_recursive(project.name, "", structure)
                
        except Exception as e:
            logger.error(f"创建项目结构失败: {str(e)}", exc_info=True)
            raise
    
    def _collect_files_from_structure(
        self,
        current_path: str,
        structure: Dict[str, Any]
    ) -> List[Tuple[str, str]]:
        """
        从模板结构中收集所有文件和目录
        
        Args:
            current_path: 当前路径
            structure: 结构定义
            
        Returns:
            List[Tuple[str, str]]: 文件列表，每个元素是 (relative_path, content) 元组
                对于目录，content 为空字符串，路径以 '/' 结尾表示目录
        """
        files = []
        
        for name, content in structure.items():
            item_path = f"{current_path}/{name}" if current_path else name
            
            if isinstance(content, dict):
                # 目录：先添加目录本身（如果是空目录或有子项）
                # 移除路径末尾的 '/' 以保持一致性
                dir_path = item_path.rstrip('/')
                
                # 如果是空目录，添加目录记录
                if len(content) == 0:
                    # 空目录：添加一个特殊标记，表示这是一个目录
                    files.append((dir_path, "__DIRECTORY__"))
                else:
                    # 有子项的目录：递归收集子文件
                    files.extend(self._collect_files_from_structure(dir_path, content))
            elif isinstance(content, str):
                # 文件：添加到列表
                files.append((item_path, content))
        
        return files
    
    async def _create_structure_recursive(
        self,
        project_name: str,
        current_path: str,
        structure: Dict[str, Any]
    ) -> None:
        """
        递归创建目录结构（文件系统存储，向后兼容）
        
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
        验证项目结构完整性（使用数据库存储）
        
        Args:
            project_id: 项目ID
        
        Returns:
            验证结果字典（is_valid、missing_files、missing_directories、warnings、structure）
        """
        project = await self.get_by_id(project_id)
        if not project:
            raise ValueError(f"项目不存在: {project_id}")
        
        # 如果没有注入 ProjectFileService，抛出异常
        if not self._project_file_service:
            raise ValueError("ProjectFileService 未注入，无法验证项目结构")
        
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
        
        # 使用 SQLAlchemy 查询检查必需的目录是否存在于数据库中
        for dir_name in required.get("directories", []):
            try:
                # 查询数据库中是否存在该目录记录
                result = await self.db.execute(
                    select(ProjectFile).where(
                        and_(
                            ProjectFile.project_id == project_id,
                            ProjectFile.relative_path == dir_name,
                            ProjectFile.is_directory == True
                        )
                    )
                )
                dir_record = result.scalar_one_or_none()
                exists = dir_record is not None
                
                structure_status[dir_name] = {
                    "exists": exists,
                    "required": True,
                    "type": "directory"
                }
                if not exists:
                    missing_directories.append(dir_name)
            except Exception as e:
                logger.error(f"检查目录失败: {dir_name}, 错误: {str(e)}")
                structure_status[dir_name] = {
                    "exists": False,
                    "required": True,
                    "type": "directory"
                }
                missing_directories.append(dir_name)
        
        # 使用 SQLAlchemy 查询检查必需的文件是否存在于数据库中
        for file_name in required.get("files", []):
            try:
                # 查询数据库中是否存在该文件记录
                result = await self.db.execute(
                    select(ProjectFile).where(
                        and_(
                            ProjectFile.project_id == project_id,
                            ProjectFile.relative_path == file_name,
                            ProjectFile.is_directory == False
                        )
                    )
                )
                file_record = result.scalar_one_or_none()
                exists = file_record is not None
                
                structure_status[file_name] = {
                    "exists": exists,
                    "required": True,
                    "type": "file"
                }
                if not exists:
                    missing_files.append(file_name)
            except Exception as e:
                logger.error(f"检查文件失败: {file_name}, 错误: {str(e)}")
                structure_status[file_name] = {
                    "exists": False,
                    "required": True,
                    "type": "file"
                }
                missing_files.append(file_name)
        
        # 检查可选的目录
        optional_dirs = ["group_vars", "host_vars", "files", "templates"]
        for dir_name in optional_dirs:
            if dir_name not in structure_status:
                try:
                    # 查询数据库中是否存在该目录记录
                    result = await self.db.execute(
                        select(ProjectFile).where(
                            and_(
                                ProjectFile.project_id == project_id,
                                ProjectFile.relative_path == dir_name,
                                ProjectFile.is_directory == True
                            )
                        )
                    )
                    dir_record = result.scalar_one_or_none()
                    exists = dir_record is not None
                    
                    structure_status[dir_name] = {
                        "exists": exists,
                        "required": False,
                        "type": "directory"
                    }
                    if not exists:
                        warnings.append(f"可选目录 {dir_name} 不存在")
                except Exception as e:
                    logger.error(f"检查可选目录失败: {dir_name}, 错误: {str(e)}")
                    structure_status[dir_name] = {
                        "exists": False,
                        "required": False,
                        "type": "directory"
                    }
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
        project_id: int
    ) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
        
        Returns:
            bool: 是否删除成功
        """
        project = await self.get_by_id(project_id)
        if not project:
            logger.warning(f"尝试删除不存在的项目: project_id={project_id}")
            return False
        
        logger.info(
            f"开始删除项目: project_id={project_id}, name={project.name}, type={project.project_type}"
        )
        
        try:
            # 删除项目对象
            # ORM 级联删除会自动删除关联的 ProjectFile、Playbook、Role 等记录
            # 必须使用 db.delete(object) 而不是 delete(Model).where() 才能触发级联删除
            await self.db.delete(project)
            await self.db.commit()
            
            logger.info(
                f"项目删除成功: project_id={project_id}, name={project.name}"
            )
            
            return True
            
        except Exception as e:
            logger.error(
                f"删除项目时发生异常: project_id={project_id}, name={project.name}, error={str(e)}",
                exc_info=True
            )
            # 回滚事务
            await self.db.rollback()
            raise
    
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
